"""
Arbitrage Detection Service — Phase 1

Combines Amazon scraper (buy source) with eBay scraper (sell source)
and the profit calculator to find real arbitrage opportunities.

Flow:
1. Get Amazon product with price history
2. Evaluate discrepancy against historical data
3. Get eBay market price (median sold price)
4. Calculate profit with real fee tables
5. If profitable (meets min profit + ROI), create an alert

Also supports scanning Amazon deals in bulk and finding arbitrage
opportunities across multiple products.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
import logging

from app.services.amazon_scraper import AmazonProduct, fetch_amazon_product, search_amazon_deals
from app.services.ebay_scraper import get_ebay_market_price, eBayListing, search_ebay_sold
from app.services.profit_calculator import (
    calculate_profit,
    ProfitBreakdown,
    Platform,
    ProductCategory,
)
from app.services.deal_criteria import (
    evaluate_discrepancy,
    DealEvaluation,
    DealTier,
    DealStatus,
    PriceHistory,
    default_criteria,
)
from app.services.coupon_scraper import ScrapedCoupon, calculate_discounted_price

logger = logging.getLogger(__name__)


@dataclass
class ArbitrageOpportunity:
    """A detected arbitrage opportunity."""
    # Product info
    asin: str
    title: str
    image_url: Optional[str] = None
    buy_url: str = ""
    sell_platform: str = "ebay"

    # Prices
    buy_price: Decimal = Decimal("0")
    sell_price: Decimal = Decimal("0")  # eBay median sold price
    historical_avg: Optional[Decimal] = None

    # Evaluation
    discrepancy: Optional[Decimal] = None
    deal_tier: str = "arbitrage"
    deal_status: str = "pending"

    # Profit
    profit: Optional[ProfitBreakdown] = None

    # Coupon / promo code applied to buy price
    applied_coupon_code: Optional[str] = None
    coupon_discount: Optional[Decimal] = None
    original_buy_price: Optional[Decimal] = None  # price before coupon

    # Metadata
    bsr: Optional[int] = None
    category: Optional[str] = None
    detected_at: datetime = None

    def __post_init__(self):
        if self.detected_at is None:
            self.detected_at = datetime.utcnow()

    @property
    def is_profitable(self) -> bool:
        if not self.profit:
            return False
        return (
            self.profit.is_profitable
            and self.profit.net_profit >= default_criteria.min_net_profit
            and self.profit.roi >= default_criteria.min_roi
        )

    def to_dict(self) -> dict:
        return {
            "asin": self.asin,
            "title": self.title,
            "image_url": self.image_url,
            "buy_url": self.buy_url,
            "buy_price": float(self.buy_price),
            "sell_price": float(self.sell_price),
            "historical_avg": float(self.historical_avg) if self.historical_avg else None,
            "discrepancy": float(self.discrepancy) if self.discrepancy else None,
            "deal_tier": self.deal_tier,
            "net_profit": float(self.profit.net_profit) if self.profit else None,
            "roi": float(self.profit.roi) if self.profit else None,
            "total_costs": float(self.profit.total_costs) if self.profit else None,
            "platform_fee": float(self.profit.platform_fee) if self.profit else None,
            "bsr": self.bsr,
            "category": self.category,
            "is_profitable": self.is_profitable,
            "detected_at": self.detected_at.isoformat(),
            "applied_coupon_code": self.applied_coupon_code,
            "coupon_discount": float(self.coupon_discount) if self.coupon_discount else None,
            "original_buy_price": float(self.original_buy_price) if self.original_buy_price else None,
        }


def _map_category(amazon_category: str) -> ProductCategory:
    """Map Amazon category string to our ProductCategory enum."""
    if not amazon_category:
        return ProductCategory.GENERIC

    cat_lower = amazon_category.lower()
    category_map = {
        "toy": ProductCategory.TOYS,
        "game": ProductCategory.TOYS,
        "home": ProductCategory.HOME,
        "kitchen": ProductCategory.KITCHEN,
        "dining": ProductCategory.KITCHEN,
        "sport": ProductCategory.SPORTS,
        "outdoor": ProductCategory.SPORTS,
        "exercise": ProductCategory.SPORTS,
        "tool": ProductCategory.TOOLS,
        "hardware": ProductCategory.TOOLS,
        "electronic": ProductCategory.ELECTRONICS,
        "computer": ProductCategory.ELECTRONICS,
        "cell phone": ProductCategory.ELECTRONICS,
        "clothing": ProductCategory.CLOTHING,
        "apparel": ProductCategory.CLOTHING,
        "shoe": ProductCategory.CLOTHING,
        "beauty": ProductCategory.BEAUTY,
        "health": ProductCategory.BEAUTY,
        "book": ProductCategory.BOOKS,
    }

    for keyword, category in category_map.items():
        if keyword in cat_lower:
            return category

    return ProductCategory.GENERIC


def apply_coupon_to_opportunity(
    opportunity: ArbitrageOpportunity,
    coupon: ScrapedCoupon,
) -> ArbitrageOpportunity:
    """Apply a coupon to an existing arbitrage opportunity, recalculating profit.

    The coupon reduces the effective buy price, which increases net profit and ROI.
    Returns a new ArbitrageOpportunity with updated values.
    """
    effective_price, discount = calculate_discounted_price(opportunity.buy_price, coupon)

    if discount <= 0:
        return opportunity

    # Recalculate profit with the discounted buy price
    sell_platform = Platform.EBAY  # Default; could be parameterized
    category = _map_category(opportunity.category or "")

    new_profit = calculate_profit(
        buy_price=effective_price,
        sell_price=opportunity.sell_price,
        sell_platform=sell_platform,
        category=category,
    )

    # Create updated opportunity
    return ArbitrageOpportunity(
        asin=opportunity.asin,
        title=opportunity.title,
        image_url=opportunity.image_url,
        buy_url=opportunity.buy_url,
        buy_price=effective_price,
        sell_price=opportunity.sell_price,
        historical_avg=opportunity.historical_avg,
        discrepancy=opportunity.discrepancy,
        deal_tier=opportunity.deal_tier,
        deal_status=opportunity.deal_status,
        profit=new_profit,
        applied_coupon_code=coupon.code,
        coupon_discount=discount,
        original_buy_price=opportunity.buy_price,
        bsr=opportunity.bsr,
        category=opportunity.category,
        detected_at=opportunity.detected_at,
    )


async def find_arbitrage_for_asin(
    asin: str,
    sell_platform: Platform = Platform.EBAY,
) -> Optional[ArbitrageOpportunity]:
    """Find arbitrage opportunity for a specific Amazon product.

    Args:
        asin: Amazon ASIN to analyze
        sell_platform: Where the item will be sold (default: eBay)

    Returns:
        ArbitrageOpportunity if a deal is found, None otherwise
    """
    # Step 1: Get Amazon product data with price history
    product = await fetch_amazon_product(asin)
    if not product or not product.current_price:
        logger.info(f"No Amazon data found for ASIN {asin}")
        return None

    if not product.in_stock:
        logger.info(f"ASIN {asin} not in stock")
        return None

    # Step 2: Evaluate discrepancy against historical data
    evaluation = evaluate_discrepancy(product.current_price, product.price_history)

    # Even if discrepancy is low, we still check arbitrage (cross-platform price gap)
    # But we log the discrepancy evaluation for reference

    # Step 3: Get eBay market price (what this item sells for)
    search_query = product.title or asin
    ebay_market_price = await get_ebay_market_price(search_query, limit=10)

    if not ebay_market_price:
        logger.info(f"No eBay sold data for ASIN {asin} (query: {search_query[:50]})")
        return None

    # Step 4: Calculate profit
    category = _map_category(product.category or "")

    # Determine outbound shipping (eBay buyer typically pays, but account for it)
    outbound_shipping = Decimal("0") if sell_platform == Platform.EBAY else Decimal("5.99")

    profit = calculate_profit(
        buy_price=product.current_price,
        sell_price=ebay_market_price,
        sell_platform=sell_platform,
        category=category,
        outbound_shipping=outbound_shipping,
    )

    # Step 5: Build opportunity object
    opportunity = ArbitrageOpportunity(
        asin=asin,
        title=product.title,
        image_url=product.image_url,
        buy_url=product.url,
        buy_price=product.current_price,
        sell_price=ebay_market_price,
        historical_avg=product.price_history.average,
        discrepancy=evaluation.discrepancy,
        deal_tier=evaluation.tier.value if evaluation.tier != DealTier.REJECTED else "arbitrage",
        deal_status=evaluation.status.value,
        profit=profit,
        bsr=product.bsr,
        category=product.category,
    )

    # BSR quality filter: skip items with BSR > 100K (low sales velocity)
    if product.bsr and product.bsr > 100000:
        logger.info(f"ASIN {asin} BSR too high ({product.bsr:,}), skipping")
        return None

    if opportunity.is_profitable:
        logger.info(
            f"PROFITABLE DEAL: {asin} - {product.title[:40]}... "
            f"Buy ${product.current_price} → Sell ${ebay_market_price} "
            f"Net ${profit.net_profit} ({profit.roi*100:.1f}% ROI)"
        )
        return opportunity
    else:
        logger.info(
            f"Not profitable: {asin} - Buy ${product.current_price} → "
            f"Sell ${ebay_market_price} Net ${profit.net_profit}"
        )
        return None


async def scan_amazon_for_arbitrage(
    category: str = "",
    min_discount: Decimal = Decimal("0.50"),
    max_price: Decimal = Decimal("500.00"),
    limit: int = 20,
    sell_platform: Platform = Platform.EBAY,
) -> list[ArbitrageOpportunity]:
    """Scan Amazon for deals and check each for arbitrage potential.

    This is the main scanning function that:
    1. Searches Amazon for discounted products (via Keepa)
    2. For each deal, checks eBay sold prices
    3. Calculates profit
    4. Returns only profitable opportunities

    Args:
        category: Amazon category to search (empty = all)
        min_discount: Minimum discount percentage on Amazon
        max_price: Maximum Amazon price
        limit: Max products to scan
        sell_platform: Where items will be sold

    Returns:
        List of profitable ArbitrageOpportunity objects
    """
    logger.info(f"Scanning Amazon for deals (min {min_discount*100:.0f}% off, max ${max_price})...")

    # Get Amazon deals
    products = await search_amazon_deals(
        category=category,
        min_discount=min_discount,
        max_price=max_price,
        limit=limit,
    )

    logger.info(f"Found {len(products)} Amazon deals, checking eBay prices...")

    opportunities = []
    for product in products:
        if not product.current_price or not product.in_stock:
            continue

        # Get eBay market price
        search_query = product.title or product.asin
        ebay_price = await get_ebay_market_price(search_query, limit=10)

        if not ebay_price:
            continue

        # Calculate profit
        cat = _map_category(product.category or "")
        profit = calculate_profit(
            buy_price=product.current_price,
            sell_price=ebay_price,
            sell_platform=sell_platform,
            category=cat,
        )

        # BSR filter
        if product.bsr and product.bsr > 100000:
            continue

        opportunity = ArbitrageOpportunity(
            asin=product.asin,
            title=product.title,
            image_url=product.image_url,
            buy_url=product.url,
            buy_price=product.current_price,
            sell_price=ebay_price,
            historical_avg=product.price_history.average,
            profit=profit,
            bsr=product.bsr,
            category=product.category,
        )

        if opportunity.is_profitable:
            opportunities.append(opportunity)
            logger.info(
                f"  ✓ {product.asin}: Buy ${product.current_price} → "
                f"Sell ${ebay_price} → Net ${profit.net_profit} ({profit.roi*100:.1f}% ROI)"
            )

    # Sort by net profit (highest first)
    opportunities.sort(key=lambda o: o.profit.net_profit if o.profit else Decimal("0"), reverse=True)

    logger.info(f"Found {len(opportunities)} profitable arbitrage opportunities")
    return opportunities
