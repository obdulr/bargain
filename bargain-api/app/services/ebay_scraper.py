"""
eBay Scraper — Self-contained, no API dependencies.

Scrapes eBay sold listings directly to find real market sell prices
for arbitrage calculations. Uses anti-detection HTTP client.

If eBay API credentials ARE configured, the Browse API is used as an
optional enhancement (better structured data) and scraping is the
fallback. Without credentials, the scraper works entirely on its own.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
import logging
import re

from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.scraper import _parse_price
from app.services.affiliate_service import add_affiliate_tag
from app.services.http_client import ScrapingClient

logger = logging.getLogger(__name__)


@dataclass
class eBayListing:
    """eBay listing data."""
    item_id: str
    title: str
    price: Decimal
    currency: str
    url: str
    condition: str = "New"
    shipping_cost: Optional[Decimal] = None
    seller_feedback_pct: Optional[float] = None
    sold_date: Optional[datetime] = None
    image_url: Optional[str] = None


# eBay API endpoints (optional enhancement when credentials are set)
EBAY_API_BASE = "https://api.ebay.com"
EBAY_BROWSE_ENDPOINT = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search"
EBAY_OAUTH_ENDPOINT = f"{EBAY_API_BASE}/identity/v1/oauth2/token"

# Cache for OAuth token
_ebay_token_cache: dict = {"token": None, "expires": 0}


# ---------------------------------------------------------------------------
# HTML scraping (primary path — no API required)
# ---------------------------------------------------------------------------


def _parse_sold_date(text: str) -> Optional[datetime]:
    """Parse a sold-date string from an eBay listing (e.g. 'Sep-12 18:24')."""
    if not text:
        return None
    text = text.strip()
    # eBay sold listings show dates like "Sep-12 18:24" or "Sep 12, 2024"
    for fmt in ("%b-%d %H:%M", "%b %d, %Y", "%b-%d-%y", "%m/%d/%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


async def _scrape_ebay_sold(
    query: str, limit: int = 20, condition: str = ""
) -> list[eBayListing]:
    """Scrape eBay sold/completed listings from the web interface."""
    from urllib.parse import quote

    url = (
        f"https://www.ebay.com/sch/i.html?_nkw={quote(query)}"
        "&LH_Sold=1&LH_Complete=1&_sop=13"  # sort by end date
    )
    if condition and condition.upper() == "NEW":
        url += "&LH_ItemCondition=1000"
    elif condition and condition.upper() == "USED":
        url += "&LH_ItemCondition=3000"

    proxy = getattr(settings, "SCRAPER_PROXY_URL", "") or None
    rate_limit = getattr(settings, "SCRAPER_RATE_LIMIT_SECONDS", 2.0)
    max_retries = getattr(settings, "SCRAPER_MAX_RETRIES", 3)

    async with ScrapingClient(
        max_retries=max_retries,
        rate_limit_seconds=rate_limit,
        proxy_url=proxy,
    ) as client:
        html = await client.get_html(url, referer="https://www.ebay.com/")

    if not html:
        logger.warning(f"Failed to fetch eBay sold listings for '{query}'")
        return []

    soup = BeautifulSoup(html, "lxml")
    listings: list[eBayListing] = []

    items = soup.select(".s-item")
    for item in items:
        title_el = item.select_one(".s-item__title")
        price_el = item.select_one(".s-item__price")
        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        # Skip promotional "Shop on eBay" cards
        if title.lower().startswith("shop on ebay"):
            continue
        if not title or title.lower() == "sold item":
            continue

        price = _parse_price(price_el.get_text(strip=True))
        if price is None or price <= 0:
            continue

        # Link / item id
        link_el = item.select_one(".s-item__link")
        link = link_el.get("href", "") if link_el else ""
        item_id = ""
        if link:
            match = re.search(r"/itm/(\d+)", link)
            if match:
                item_id = match.group(1)

        # Condition
        condition_text = "New"
        subtitle_el = item.select_one(".s-item__subtitle")
        if subtitle_el:
            sub = subtitle_el.get_text(strip=True).lower()
            if "used" in sub:
                condition_text = "Used"
            elif "pre-owned" in sub:
                condition_text = "Pre-Owned"
            elif "refurbished" in sub:
                condition_text = "Refurbished"
            elif "new" in sub:
                condition_text = "New"

        # Shipping cost
        shipping = None
        shipping_el = item.select_one(
            ".s-item__shipping .s-item__logisticsCost, .s-item__shipping"
        )
        if shipping_el:
            ship_text = shipping_el.get_text(strip=True)
            if "free" in ship_text.lower():
                shipping = Decimal("0")
            else:
                shipping = _parse_price(ship_text)

        # Sold date
        sold_date = None
        date_el = item.select_one(
            ".s-item__title--tagblock .POSITIVE, .s-item__caption-date, "
            ".s-item__title--tag .POSITIVE"
        )
        if date_el:
            sold_date = _parse_sold_date(date_el.get_text(strip=True))

        # Image
        image_url = None
        img_el = item.select_one(".s-item__image img")
        if img_el:
            image_url = img_el.get("src") or img_el.get("data-src")

        listing = eBayListing(
            item_id=item_id,
            title=title,
            price=price,
            currency="USD",
            url=add_affiliate_tag(link, "ebay"),
            condition=condition_text,
            shipping_cost=shipping,
            sold_date=sold_date,
            image_url=image_url,
        )
        listings.append(listing)

        if len(listings) >= limit:
            break

    return listings


# ---------------------------------------------------------------------------
# eBay Browse API path (optional enhancement)
# ---------------------------------------------------------------------------


async def _get_ebay_oauth_token() -> Optional[str]:
    """Get eBay OAuth token using client credentials flow."""
    import base64
    import time

    client_id = getattr(settings, "EBAY_CLIENT_ID", "")
    client_secret = getattr(settings, "EBAY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        return None

    if _ebay_token_cache["token"] and time.time() < _ebay_token_cache["expires"] - 60:
        return _ebay_token_cache["token"]

    import httpx

    credentials = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {credentials}",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        try:
            response = await client.post(EBAY_OAUTH_ENDPOINT, headers=headers, data=data)
            response.raise_for_status()
            token_data = response.json()
        except Exception as e:
            logger.warning(f"eBay OAuth failed: {e}")
            return None

    token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 7200)
    _ebay_token_cache["token"] = token
    _ebay_token_cache["expires"] = time.time() + expires_in
    return token


async def _search_ebay_sold_api(
    query: str, limit: int = 20, condition: str = "NEW"
) -> list[eBayListing]:
    """Search eBay sold listings via the Browse API (optional enhancement)."""
    import httpx

    token = await _get_ebay_oauth_token()
    if not token:
        return []

    headers = {
        "Authorization": f"Bearer {token}",
        "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
        "Content-Type": "application/json",
    }
    params = {
        "q": query,
        "limit": limit,
        "filter": "buyingOptions:FIXED_PRICE,soldItems:true",
        "sort": "price",
    }
    if condition:
        params["filter"] += f",conditions:{condition}"

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                EBAY_BROWSE_ENDPOINT, headers=headers, params=params
            )
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"eBay Browse API failed: {e}")
            return []

    listings = []
    for item in data.get("itemSummaries", []):
        price_val = item.get("price", {})
        price = _parse_price(price_val.get("value", "0"))
        if price is None or price <= 0:
            continue

        shipping = None
        shipping_info = item.get("shippingOptions", [{}])
        if shipping_info:
            shipping_cost = shipping_info[0].get("shippingCost", {})
            if shipping_cost:
                shipping = _parse_price(shipping_cost.get("value", "0"))

        seller = item.get("seller", {})
        feedback_pct = seller.get("feedbackPercentage") if seller else None

        listing = eBayListing(
            item_id=item.get("itemId", ""),
            title=item.get("title", ""),
            price=price,
            currency=price_val.get("currency", "USD"),
            url=add_affiliate_tag(item.get("itemWebUrl", ""), "ebay"),
            condition=item.get("condition", "New"),
            shipping_cost=shipping,
            seller_feedback_pct=feedback_pct,
            image_url=item.get("image", {}).get("imageUrl"),
        )
        listings.append(listing)

    return listings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def search_ebay_sold(
    query: str,
    limit: int = 20,
    condition: str = "NEW",
) -> list[eBayListing]:
    """Search eBay for sold/completed listings to find real market prices.

    Scraping is the primary path. If eBay API credentials are configured,
    the Browse API is tried first (better structured data) and scraping
    is the fallback.

    Args:
        query: Search query (product name, UPC, or keywords)
        limit: Maximum results to return
        condition: "NEW", "USED", or "" for any

    Returns:
        List of eBayListing with sold prices
    """
    client_id = getattr(settings, "EBAY_CLIENT_ID", "")
    client_secret = getattr(settings, "EBAY_CLIENT_SECRET", "")
    if client_id and client_secret:
        listings = await _search_ebay_sold_api(query, limit=limit, condition=condition)
        if listings:
            return listings
        # Fall through to scraping if the API returns nothing

    return await _scrape_ebay_sold(query, limit=limit, condition=condition)


async def get_ebay_market_price(query: str, limit: int = 10) -> Optional[Decimal]:
    """Get the median sold price for a product on eBay.

    This is the key function for arbitrage — it tells you what
    the item actually sells for on eBay.

    Args:
        query: Product name or UPC
        limit: Number of sold listings to analyze

    Returns:
        Median sold price, or None if no data
    """
    listings = await search_ebay_sold(query, limit=limit)
    if not listings:
        return None

    # Filter to only items with positive seller feedback (quality filter)
    quality_listings = [
        l for l in listings
        if l.seller_feedback_pct is None or l.seller_feedback_pct >= 95.0
    ]
    if not quality_listings:
        quality_listings = listings

    prices = sorted(l.price for l in quality_listings)
    n = len(prices)
    if n == 0:
        return None

    if n % 2 == 0:
        median = (prices[n // 2 - 1] + prices[n // 2]) / 2
    else:
        median = prices[n // 2]

    return median.quantize(Decimal("0.01"))
