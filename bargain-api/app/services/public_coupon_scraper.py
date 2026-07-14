"""
Public Coupon Scraper — fetches promo codes from free RSS/JSON feeds.

Sources:
  - Slickdeals coupons RSS
  - RetailMeNot public coupon pages (RSS when available)
  - DealNews coupon feed
  - TechBargains coupons

No API key required — these are public feeds.
"""
import asyncio
import logging
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


@dataclass
class PublicCoupon:
    """A coupon scraped from a public feed."""
    code: str
    retailer: str
    title: str
    description: Optional[str] = None
    discount_type: str = "percentage"
    discount_value: Decimal = Decimal("0")
    category: Optional[str] = None
    source: str = "rss"
    source_url: str = ""
    expires_at: Optional[datetime] = None


# RSS feeds with coupon/promo code data
COUPON_FEEDS = [
    {
        "name": "Slickdeals Coupons",
        "url": "https://slickdeals.net/rss.php?mode=coupons",
        "retailer_field": "merchant",
    },
    {
        "name": "DealNews Coupons",
        "url": "https://dealnews.com/coupons/rss.xml",
        "retailer_field": "merchant",
    },
    {
        "name": "TechBargains Coupons",
        "url": "https://techbargains.com/rss.xml",
        "retailer_field": "merchant",
    },
]


def _parse_discount(text: str) -> tuple[str, Decimal]:
    """Extract discount type and value from text."""
    text_lower = text.lower()
    if "free shipping" in text_lower:
        return "free_shipping", Decimal("0")
    pct_match = re.search(r'(\d+)\s*%\s*off', text_lower)
    if pct_match:
        return "percentage", Decimal(pct_match.group(1))
    dollar_match = re.search(r'\$(\d+(?:\.\d+)?)\s*off', text_lower)
    if dollar_match:
        return "fixed", Decimal(dollar_match.group(1))
    return "percentage", Decimal("0")


def _normalize_retailer(name: str) -> str:
    """Normalize retailer name to a standard key."""
    name_lower = name.lower().strip()
    mapping = {
        "amazon": "amazon",
        "walmart": "walmart",
        "target": "target",
        "best buy": "best_buy",
        "bestbuy": "best_buy",
        "newegg": "newegg",
        "ebay": "ebay",
        "costco": "costco",
        "home depot": "home_depot",
        "homedepot": "home_depot",
        "lowes": "lowes",
        "kohls": "kohls",
        "macys": "macys",
        "sams club": "samsclub",
        "samsclub": "samsclub",
        "overstock": "overstock",
        "adorama": "adorama",
        "bh photo": "bhphoto",
        "b&h": "bhphoto",
        "monoprice": "monoprice",
        "woot": "woot",
    }
    for key, val in mapping.items():
        if key in name_lower:
            return val
    return name_lower.replace(" ", "_").replace(".", "")[:30]


def _extract_coupon_code(text: str) -> Optional[str]:
    """Try to extract a coupon code from text.

    Coupon codes are typically:
      - After "Code:" or "Use code" or "Promo:"
      - Uppercase alphanumeric strings 4-15 chars
    """
    # Look for explicit "Code:" patterns
    patterns = [
        r'(?:code|promo|coupon)[:\s]+([A-Z0-9]{3,15})\b',
        r'(?:use code|enter code|with code)\s+([A-Z0-9]{3,15})\b',
        r'\b([A-Z]{2,4}\d{2,6})\b',  # e.g. SAVE20, DEAL50
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            code = match.group(1).upper()
            # Filter out common false positives
            if code not in ("HTTP", "HTTPS", "HTML", "XML", "RSS", "USD"):
                return code
    return None


async def _scrape_feed(feed: dict) -> list[PublicCoupon]:
    """Scrape a single RSS feed for coupons."""
    coupons = []
    try:
        async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
            resp = await client.get(feed["url"], headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            })
            if resp.status_code != 200:
                logger.debug(f"{feed['name']}: HTTP {resp.status_code}")
                return []

            soup = BeautifulSoup(resp.content, "xml")
            items = soup.find_all("item")

            for item in items:
                title = item.find("title")
                title_text = title.text.strip() if title else ""

                link = item.find("link")
                link_text = link.text.strip() if link else ""

                desc = item.find("description")
                desc_text = desc.text.strip() if desc else ""

                # Try to find retailer from the feed
                retailer_name = ""
                merchant = item.find("merchant") or item.find("dc:creator") or item.find("author")
                if merchant:
                    retailer_name = merchant.text.strip()
                if not retailer_name:
                    # Try to extract from title
                    for known in ["Amazon", "Walmart", "Target", "Best Buy", "eBay",
                                  "Newegg", "Costco", "Home Depot", "Lowe's", "Kohl's",
                                  "Macy's", "Overstock", "Adorama", "Woot"]:
                        if known.lower() in title_text.lower():
                            retailer_name = known
                            break

                if not retailer_name:
                    # Try domain from link
                    if link_text:
                        domain = urlparse(link_text).netloc.lower()
                        for known in ["amazon", "walmart", "target", "bestbuy",
                                      "ebay", "newegg", "costco", "homedepot",
                                      "lowes", "kohls", "macys", "overstock"]:
                            if known in domain:
                                retailer_name = known
                                break

                if not retailer_name:
                    continue

                retailer = _normalize_retailer(retailer_name)

                # Try to extract coupon code
                full_text = f"{title_text} {desc_text}"
                code = _extract_coupon_code(full_text)

                if not code:
                    # Generate a placeholder code for deals that mention a coupon
                    # but don't show the code (common in RSS feeds)
                    if "coupon" in full_text.lower() or "promo" in full_text.lower():
                        code = "SEE_SITE"
                    else:
                        continue

                discount_type, discount_value = _parse_discount(full_text)

                coupons.append(PublicCoupon(
                    code=code,
                    retailer=retailer,
                    title=title_text[:200],
                    description=desc_text[:500] if desc_text else None,
                    discount_type=discount_type,
                    discount_value=discount_value,
                    category=feed["name"],
                    source="rss",
                    source_url=link_text,
                ))

    except Exception as e:
        logger.debug(f"{feed['name']} scrape error: {e}")

    logger.info(f"{feed['name']}: {len(coupons)} coupons found")
    return coupons


async def scrape_public_coupons() -> list[PublicCoupon]:
    """Scrape coupons from all public RSS feeds."""
    all_coupons = []
    tasks = [_scrape_feed(feed) for feed in COUPON_FEEDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for result in results:
        if isinstance(result, list):
            all_coupons.extend(result)

    # Deduplicate by (retailer, code) pair
    seen = set()
    unique = []
    for c in all_coupons:
        key = (c.retailer, c.code)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    logger.info(f"Public coupon scrape: {len(unique)} unique coupons from {len(all_coupons)} total")
    return unique
