"""
Profit Calculator — Phase 1

Calculates true net profit for arbitrage deals, factoring in:
- Platform fees (referral, fulfillment, transaction, processing)
- Shipping costs (inbound and outbound)
- Estimated tax
- Return risk by category

Supports buy sources (Amazon, Walmart, Target, Best Buy) and
sell sources (eBay, Amazon FBA, StockX, Poshmark, Mercari).
"""

from decimal import Decimal, ROUND_HALF_UP
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class Platform(str, Enum):
    # Buy sources
    AMAZON = "amazon"
    WALMART = "walmart"
    TARGET = "target"
    BEST_BUY = "best_buy"
    HOME_DEPOT = "home_depot"
    # Sell sources
    EBAY = "ebay"
    AMAZON_FBA = "amazon_fba"
    STOCKX = "stockx"
    POSHMARK = "poshmark"
    MERCARI = "mercari"


class ProductCategory(str, Enum):
    TOYS = "toys"
    HOME = "home"
    KITCHEN = "kitchen"
    SPORTS = "sports"
    TOOLS = "tools"
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    BEAUTY = "beauty"
    BOOKS = "books"
    GENERIC = "generic"


# --- Fee Tables ---

# Amazon FBA fees by category
# Referral fee (% of sale) + fulfillment fee (per unit, based on size tier)
AMAZON_FBA_REFERRAL = {
    ProductCategory.TOYS: Decimal("0.15"),
    ProductCategory.HOME: Decimal("0.15"),
    ProductCategory.KITCHEN: Decimal("0.15"),
    ProductCategory.SPORTS: Decimal("0.15"),
    ProductCategory.TOOLS: Decimal("0.15"),
    ProductCategory.ELECTRONICS: Decimal("0.08"),
    ProductCategory.CLOTHING: Decimal("0.17"),
    ProductCategory.BEAUTY: Decimal("0.15"),
    ProductCategory.BOOKS: Decimal("0.15"),
    ProductCategory.GENERIC: Decimal("0.15"),
}

# FBA fulfillment fee by weight tier (simplified)
# Small standard: $3.22, Large standard: $5.32, Small oversize: $8.54
AMAZON_FBA_FULFILLMENT = {
    "small_standard": Decimal("3.22"),
    "large_standard": Decimal("5.32"),
    "small_oversize": Decimal("8.54"),
    "large_oversize": Decimal("10.79"),
}

# eBay fees
# Final value fee: 13.25% for most categories, $0.30 per order
EBAY_FINAL_VALUE_FEE = Decimal("0.1325")
EBAY_PER_ORDER_FEE = Decimal("0.30")

# StockX fees
# Transaction fee: ~10%, processing fee: ~3.5% + $3.50
STOCKX_TRANSACTION_FEE = Decimal("0.10")
STOCKX_PROCESSING_FEE = Decimal("0.035")
STOCKX_PROCESSING_FLAT = Decimal("3.50")

# Poshmark fees
# Flat 20% for sales over $15, flat $2.95 for sales under $15
POSHMARK_FEE_RATE = Decimal("0.20")
POSHMARK_LOW_SALE_FEE = Decimal("2.95")
POSHMARK_LOW_SALE_THRESHOLD = Decimal("15.00")

# Mercari fees
# 10% selling fee + 2.9% + $0.30 processing fee
MERCARI_SELLING_FEE = Decimal("0.10")
MERCARI_PROCESSING_FEE = Decimal("0.029")
MERCARI_PROCESSING_FLAT = Decimal("0.30")

# Return rate by category (for risk adjustment)
RETURN_RATES = {
    ProductCategory.TOYS: Decimal("0.05"),
    ProductCategory.HOME: Decimal("0.08"),
    ProductCategory.KITCHEN: Decimal("0.07"),
    ProductCategory.SPORTS: Decimal("0.09"),
    ProductCategory.TOOLS: Decimal("0.06"),
    ProductCategory.ELECTRONICS: Decimal("0.15"),  # High return risk
    ProductCategory.CLOTHING: Decimal("0.12"),
    ProductCategory.BEAUTY: Decimal("0.04"),
    ProductCategory.BOOKS: Decimal("0.03"),
    ProductCategory.GENERIC: Decimal("0.08"),
}

# Estimated shipping costs (buyer pays inbound, seller pays outbound)
DEFAULT_INBOUND_SHIPPING = Decimal("0.00")  # Often free with Prime/free shipping
DEFAULT_OUTBOUND_SHIPPING = Decimal("5.99")  # Average outbound shipping cost

# Default tax rate (estimated)
DEFAULT_TAX_RATE = Decimal("0.08")  # 8% average US sales tax


@dataclass
class ProfitBreakdown:
    """Detailed profit calculation breakdown."""
    buy_price: Decimal
    sell_price: Decimal
    platform_fee: Decimal
    fulfillment_fee: Decimal
    shipping_in: Decimal
    shipping_out: Decimal
    tax: Decimal
    return_risk_cost: Decimal
    total_costs: Decimal
    net_profit: Decimal
    roi: Decimal  # Return on investment as decimal (0.25 = 25%)
    is_profitable: bool


def calculate_profit(
    buy_price: Decimal,
    sell_price: Decimal,
    sell_platform: Platform,
    category: ProductCategory = ProductCategory.GENERIC,
    fba_size_tier: str = "small_standard",
    inbound_shipping: Decimal = DEFAULT_INBOUND_SHIPPING,
    outbound_shipping: Decimal = DEFAULT_OUTBOUND_SHIPPING,
    tax_rate: Decimal = DEFAULT_TAX_RATE,
    include_return_risk: bool = True,
) -> ProfitBreakdown:
    """Calculate the true net profit of an arbitrage deal.

    Args:
        buy_price: Price to buy the item at (source platform)
        sell_price: Expected sell price (destination platform)
        sell_platform: Where the item will be sold
        category: Product category for fee/return estimation
        fba_size_tier: FBA size tier if selling on Amazon FBA
        inbound_shipping: Shipping cost to get the item to you
        outbound_shipping: Shipping cost to deliver to buyer
        tax_rate: Estimated sales tax rate on the buy
        include_return_risk: Whether to factor in return risk cost

    Returns:
        ProfitBreakdown with all cost components and final net profit
    """
    # Tax on purchase
    tax = (buy_price * tax_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Platform fees based on sell platform
    platform_fee = Decimal("0")
    fulfillment_fee = Decimal("0")

    if sell_platform == Platform.AMAZON_FBA:
        referral_rate = AMAZON_FBA_REFERRAL.get(category, Decimal("0.15"))
        platform_fee = (sell_price * referral_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fulfillment_fee = AMAZON_FBA_FULFILLMENT.get(fba_size_tier, AMAZON_FBA_FULFILLMENT["small_standard"])

    elif sell_platform == Platform.EBAY:
        platform_fee = (sell_price * EBAY_FINAL_VALUE_FEE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fulfillment_fee = EBAY_PER_ORDER_FEE

    elif sell_platform == Platform.STOCKX:
        platform_fee = (sell_price * STOCKX_TRANSACTION_FEE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fulfillment_fee = (sell_price * STOCKX_PROCESSING_FEE + STOCKX_PROCESSING_FLAT).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    elif sell_platform == Platform.POSHMARK:
        if sell_price >= POSHMARK_LOW_SALE_THRESHOLD:
            platform_fee = (sell_price * POSHMARK_FEE_RATE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            platform_fee = POSHMARK_LOW_SALE_FEE
        fulfillment_fee = Decimal("0")

    elif sell_platform == Platform.MERCARI:
        platform_fee = (sell_price * MERCARI_SELLING_FEE).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        fulfillment_fee = (sell_price * MERCARI_PROCESSING_FEE + MERCARI_PROCESSING_FLAT).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    # Return risk cost (expected loss from returns)
    return_risk_cost = Decimal("0")
    if include_return_risk:
        return_rate = RETURN_RATES.get(category, Decimal("0.08"))
        # Expected cost = return_rate * (sell_price * 0.5)  # 50% loss on returned item value
        return_risk_cost = (return_rate * sell_price * Decimal("0.5")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

    # Total costs
    total_costs = (
        buy_price
        + tax
        + platform_fee
        + fulfillment_fee
        + inbound_shipping
        + outbound_shipping
        + return_risk_cost
    ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # Net profit
    net_profit = (sell_price - total_costs).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    # ROI
    roi = Decimal("0")
    if buy_price > 0:
        roi = (net_profit / buy_price).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)

    is_profitable = net_profit > 0

    return ProfitBreakdown(
        buy_price=buy_price,
        sell_price=sell_price,
        platform_fee=platform_fee,
        fulfillment_fee=fulfillment_fee,
        shipping_in=inbound_shipping,
        shipping_out=outbound_shipping,
        tax=tax,
        return_risk_cost=return_risk_cost,
        total_costs=total_costs,
        net_profit=net_profit,
        roi=roi,
        is_profitable=is_profitable,
    )
