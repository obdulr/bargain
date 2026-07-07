"""
eBay Scraper — Phase 1

Fetches sold listing prices from eBay using the Browse API.
This gives us the real market sell price for arbitrage calculations.

Requires EBAY_CLIENT_ID and EBAY_CLIENT_SECRET environment variables.
Get credentials at https://developer.ebay.com/my/keys

If no eBay credentials are configured, falls back to scraping sold listings.
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
import httpx
import asyncio
import base64

from app.core.config import settings
from app.services.scraper import _parse_price


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


# eBay API endpoints
EBAY_API_BASE = "https://api.ebay.com"
EBAY_BROWSE_ENDPOINT = f"{EBAY_API_BASE}/buy/browse/v1/item_summary/search"
EBAY_OAUTH_ENDPOINT = f"{EBAY_API_BASE}/identity/v1/oauth2/token"

# Cache for OAuth token
_ebay_token_cache: dict = {"token": None, "expires": 0}


async def _get_ebay_oauth_token() -> Optional[str]:
    """Get eBay OAuth token using client credentials flow."""
    client_id = getattr(settings, "EBAY_CLIENT_ID", "")
    client_secret = getattr(settings, "EBAY_CLIENT_SECRET", "")

    if not client_id or not client_secret:
        return None

    # Return cached token if still valid
    import time
    if _ebay_token_cache["token"] and time.time() < _ebay_token_cache["expires"] - 60:
        return _ebay_token_cache["token"]

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
        except Exception:
            return None

    token = token_data.get("access_token")
    expires_in = token_data.get("expires_in", 7200)
    _ebay_token_cache["token"] = token
    _ebay_token_cache["expires"] = time.time() + expires_in

    return token


async def search_ebay_sold(
    query: str,
    limit: int = 20,
    condition: str = "NEW",
) -> list[eBayListing]:
    """Search eBay for sold/completed listings to find real market prices.

    Uses the Browse API's search endpoint with sold filter.

    Args:
        query: Search query (product name, UPC, or keywords)
        limit: Maximum results to return
        condition: "NEW", "USED", or "" for any

    Returns:
        List of eBayListing with sold prices
    """
    token = await _get_ebay_oauth_token()
    if not token:
        # Fallback: scrape eBay sold listings
        return await _scrape_ebay_sold(query, limit)

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
            response = await client.get(EBAY_BROWSE_ENDPOINT, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception:
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
        feedback_pct = None
        if seller:
            feedback_pct = seller.get("feedbackPercentage")

        listing = eBayListing(
            item_id=item.get("itemId", ""),
            title=item.get("title", ""),
            price=price,
            currency=price_val.get("currency", "USD"),
            url=item.get("itemWebUrl", ""),
            condition=item.get("condition", "New"),
            shipping_cost=shipping,
            seller_feedback_pct=feedback_pct,
            image_url=item.get("image", {}).get("imageUrl"),
        )
        listings.append(listing)

    return listings


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


async def _scrape_ebay_sold(query: str, limit: int = 20) -> list[eBayListing]:
    """Fallback: scrape eBay sold listings from the web interface.

    This is less reliable than the API and may break if eBay changes their HTML.
    """
    from bs4 import BeautifulSoup
    from urllib.parse import quote

    url = f"https://www.ebay.com/sch/i.html?_nkw={quote(query)}&LH_Sold=1&LH_Complete=1&_sop=13"
    headers = {"User-Agent": settings.USER_AGENT}

    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except Exception:
            return []

    soup = BeautifulSoup(response.text, "html.parser")
    listings = []

    items = soup.select(".s-item")[:limit]
    for item in items:
        title_el = item.select_one(".s-item__title")
        price_el = item.select_one(".s-item__price")
        if not title_el or not price_el:
            continue

        title = title_el.get_text(strip=True)
        if title.lower().startswith("shop on ebay"):
            continue

        price = _parse_price(price_el.get_text(strip=True))
        if price is None or price <= 0:
            continue

        link_el = item.select_one(".s-item__link")
        link = link_el.get("href", "") if link_el else ""

        listing = eBayListing(
            item_id="",
            title=title,
            price=price,
            currency="USD",
            url=link,
        )
        listings.append(listing)

    return listings
