"""
Amazon Scraper — Phase 1

Fetches product data from Amazon via the Keepa API.
Keepa provides price history, BSR (Best Seller Rank), and product details.

Requires KEEPA_API_KEY environment variable.
Get one at https://keepa.com/#!api (€20/month for 500 tokens/day)

If no Keepa API key is configured, falls back to HTML scraping with
the generic scraper (limited functionality).
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import httpx
import time

from app.core.config import settings
from app.services.scraper import fetch_price, _parse_price
from app.services.deal_criteria import PriceHistory
from app.services.affiliate_service import add_affiliate_tag


@dataclass
class AmazonProduct:
    """Amazon product data from Keepa API."""
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[Decimal] = None
    bsr: Optional[int] = None  # Best Seller Rank
    image_url: Optional[str] = None
    url: str = ""
    price_history: PriceHistory = field(default_factory=PriceHistory)
    in_stock: bool = True

    def __post_init__(self):
        if not self.url:
            self.url = add_affiliate_tag(f"https://www.amazon.com/dp/{self.asin}", "amazon", self.asin)


# Keepa API endpoints
KEEPA_API_BASE = "https://api.keepa.com"
KEEPA_PRODUCT_ENDPOINT = f"{KEEPA_API_BASE}/product"
KEEPA_CATEGORY_ENDPOINT = f"{KEEPA_API_BASE}/category"


def _keepa_time_to_datetime(keepa_minutes: int) -> datetime:
    """Convert Keepa time (minutes since epoch) to datetime."""
    # Keepa uses minutes since Jan 1, 1970
    return datetime(1970, 1, 1) + timedelta(minutes=keepa_minutes)


def _keepa_price_to_decimal(price_cents: int) -> Decimal:
    """Convert Keepa price (cents) to Decimal dollars."""
    return (Decimal(str(price_cents)) / Decimal("100")).quantize(Decimal("0.01"))


async def fetch_amazon_product(asin: str) -> Optional[AmazonProduct]:
    """Fetch Amazon product data via Keepa API.

    Args:
        asin: Amazon Standard Identification Number (e.g. "B08N5WRWNW")

    Returns:
        AmazonProduct with price history, or None if not found
    """
    api_key = getattr(settings, "KEEPA_API_KEY", "")
    if not api_key:
        # Fallback: scrape the Amazon page directly
        return await _scrape_amazon_product(asin)

    params = {
        "key": api_key,
        "domain": 1,  # amazon.com
        "asin": asin,
        "stats": 1,  # Include price history stats
        "history": 1,  # Include full price history
        "offers": 20,  # Include current offers
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(KEEPA_PRODUCT_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception:
            return None

    products = data.get("products", [])
    if not products:
        return None

    product = products[0]
    if not product:
        return None

    title = product.get("title", "")
    brand = product.get("brand", "")
    category_str = product.get("categoryTree", [{}])[-1].get("name", "") if product.get("categoryTree") else ""
    image_csv = product.get("imagesCSV", "")
    image_url = f"https://images-na.ssl-images-amazon.com/images/I/{image_csv.split(',')[0]}" if image_csv else None

    # Parse price history from Keepa's CSV format
    # Keepa returns data as arrays: [timestamp1, price1, timestamp2, price2, ...]
    price_history = PriceHistory()
    csv_data = product.get("data", {}).get("CSV", [])
    if csv_data:
        # Index 0 = Amazon price history
        amazon_csv = csv_data[0] if len(csv_data) > 0 else []
        # Parse pairs: [keepa_time, price_cents, keepa_time, price_cents, ...]
        for i in range(0, len(amazon_csv) - 1, 2):
            keepa_time = amazon_csv[i]
            price_cents = amazon_csv[i + 1]
            if price_cents > 0:
                dt = _keepa_time_to_datetime(keepa_time)
                price = _keepa_price_to_decimal(price_cents)
                price_history.prices.append((dt, price))

    # Current price (most recent non-zero)
    current_price = None
    if price_history.prices:
        current_price = price_history.prices[-1][1]

    # BSR (Best Seller Rank)
    bsr = None
    stats = product.get("stats", {})
    if stats:
        current_bsr = stats.get("current", [None, None, None, None])
        if current_bsr and len(current_bsr) > 3 and current_bsr[3]:
            bsr = int(current_bsr[3])

    return AmazonProduct(
        asin=asin,
        title=title,
        brand=brand,
        category=category_str,
        current_price=current_price,
        bsr=bsr,
        image_url=image_url,
        price_history=price_history,
        in_stock=current_price is not None,
    )


async def _scrape_amazon_product(asin: str) -> Optional[AmazonProduct]:
    """Fallback: scrape Amazon product page directly (limited data)."""
    url = add_affiliate_tag(f"https://www.amazon.com/dp/{asin}", "amazon", asin)
    price, _ = await fetch_price(url)

    return AmazonProduct(
        asin=asin,
        title="Unknown (scraped)",
        current_price=price,
        in_stock=price is not None,
    )


async def search_amazon_deals(
    category: str = "",
    min_discount: Decimal = Decimal("0.50"),
    max_price: Decimal = Decimal("500.00"),
    limit: int = 50,
) -> list[AmazonProduct]:
    """Search for deals on Amazon using Keepa's deal finder.

    This uses Keepa's /product endpoint with filtering to find products
    with significant price drops.

    Args:
        category: Amazon category to search (empty = all)
        min_discount: Minimum discount percentage (0.50 = 50% off)
        max_price: Maximum current price
        limit: Maximum number of results

    Returns:
        List of AmazonProduct with deal prices
    """
    api_key = getattr(settings, "KEEPA_API_KEY", "")
    if not api_key:
        return []  # Can't search without Keepa API

    # Keepa Deal Finder parameters
    params = {
        "key": api_key,
        "domain": 1,
        "selection": {
            "currentRange": [
                {"marketplaceId": "ATVPDKIKX0DER"}  # amazon.com
            ],
            "titleSearch": "",
            "priceTypes": 0,  # Amazon price
            "priceRange": [0, int(max_price * 100)],  # in cents
            "discountRange": [int(min_discount * 100), 100],  # discount percentage
            "limit": limit,
        },
    }

    if category:
        params["selection"]["category"] = category

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{KEEPA_API_BASE}/query",
                json=params,
            )
            response.raise_for_status()
            data = response.json()
        except Exception:
            return []

    products = []
    for deal in data.get("deals", []):
        asin = deal.get("asin", "")
        if not asin:
            continue
        product = await fetch_amazon_product(asin)
        if product and product.current_price:
            products.append(product)

    return products
