"""
Coupon Scraper Service

Scrapes coupon codes and promo deals from multiple sources:
1. RetailMeNot — retailer coupon pages
2. Slickdeals — community-posted deals with coupon codes
3. Retailer direct — Amazon promo pages, Walmart rollback/clearance

Each source has a dedicated async scraper that normalizes results into
ScrapedCoupon dataclasses. The main `scrape_all_coupons` function fans
out to all sources concurrently.

Results are upserted into the coupon_codes table by the coupon service.
"""

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging
import re

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ScrapedCoupon:
    """A coupon scraped from an external source."""
    code: str
    retailer: str
    title: str
    description: Optional[str] = None
    discount_type: str = "percentage"  # percentage, fixed, free_shipping
    discount_value: Decimal = Decimal("0")
    min_purchase: Optional[Decimal] = None
    max_discount: Optional[Decimal] = None
    category: Optional[str] = None
    product_url: Optional[str] = None
    source: str = "scraped"
    source_url: str = ""
    expires_at: Optional[datetime] = None


# ─── Retailer registry ──────────────────────────────────────────────────────

# Maps our internal retailer names to RetailMeNot URL slugs
RETAILMENOT_SLUGS = {
    "amazon": "amazon.com",
    "walmart": "walmart.com",
    "target": "target.com",
    "bestbuy": "bestbuy.com",
    "homedepot": "homedepot.com",
    "newegg": "newegg.com",
    "costco": "costco.com",
    "ebay": "ebay.com",
    "samsclub": "samsclub.com",
    "kohls": "kohls.com",
    "macys": "macys.com",
    "lowes": "lowes.com",
}

# Slickdeals coupon category pages
SLICKDEALS_COUPON_RETAILERS = [
    "amazon", "walmart", "target", "bestbuy", "homedepot",
    "newegg", "ebay", "costco", "lowes", "kohls",
]


# ─── Helpers ────────────────────────────────────────────────────────────────

def _parse_discount(text: str) -> tuple[str, Decimal]:
    """Parse a discount string like '20% off' or '$10 off' into (type, value)."""
    text_lower = text.lower()

    # Free shipping
    if "free shipping" in text_lower:
        return "free_shipping", Decimal("0")

    # Percentage: "20% off", "save 15%"
    pct_match = re.search(r"(\d+(?:\.\d+)?)\s*%", text)
    if pct_match:
        return "percentage", Decimal(pct_match.group(1))

    # Fixed: "$10 off", "save $5"
    fixed_match = re.search(r"\$(\d+(?:\.\d+)?)", text)
    if fixed_match:
        return "fixed", Decimal(fixed_match.group(1))

    return "percentage", Decimal("0")


def _parse_expiry(text: str) -> Optional[datetime]:
    """Parse expiry text like 'Expires in 3 days' or '12/31/2026'."""
    if not text:
        return None

    text_lower = text.lower().strip()

    # "Expires in N days"
    days_match = re.search(r"(\d+)\s*day", text_lower)
    if days_match:
        return datetime.utcnow() + timedelta(days=int(days_match.group(1)))

    # "Expires in N hours"
    hours_match = re.search(r"(\d+)\s*hour", text_lower)
    if hours_match:
        return datetime.utcnow() + timedelta(hours=int(hours_match.group(1)))

    # MM/DD/YYYY
    date_match = re.search(r"(\d{1,2})/(\d{1,2})/(\d{4})", text)
    if date_match:
        try:
            return datetime(int(date_match.group(3)), int(date_match.group(1)), int(date_match.group(2)))
        except ValueError:
            pass

    # "Expires today" / "Ends today"
    if "today" in text_lower or "tonight" in text_lower:
        return datetime.utcnow().replace(hour=23, minute=59, second=59)

    return None


def _extract_code(text: str) -> Optional[str]:
    """Extract a coupon code from text. Codes are typically uppercase alphanumeric."""
    if not text:
        return None

    # "Code: SAVE20" or "Use code SAVE20"
    code_match = re.search(r"(?:code[:\s]+|use\s+code\s+)([A-Z0-9]{3,20})", text, re.IGNORECASE)
    if code_match:
        return code_match.group(1).upper()

    # Standalone uppercase code in a code element
    standalone = re.search(r"\b([A-Z0-9]{4,20})\b", text)
    if standalone and not standalone.group(1).isdigit():
        return standalone.group(1)

    return None


# ─── RetailMeNot Scraper ────────────────────────────────────────────────────

async def scrape_retailmenot(retailer: str) -> list[ScrapedCoupon]:
    """Scrape coupons for a retailer from RetailMeNot."""
    slug = RETAILMENOT_SLUGS.get(retailer)
    if not slug:
        return []

    url = f"https://www.retailmenot.com/view/{slug}"
    headers = {
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    coupons: list[ScrapedCoupon] = []

    async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                logger.debug(f"RetailMeNot {retailer}: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.debug(f"RetailMeNot {retailer}: {e}")
            return []

    soup = BeautifulSoup(response.text, "html.parser")

    # RetailMeNot coupon items — look for coupon/offers sections
    coupon_items = soup.select("[data-testid='coupon-item'], .coupon-content, .offer-item, .cmn-coupon")

    for item in coupon_items:
        try:
            title_el = item.select_one(".title, .offer-title, h3, h2")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            desc_el = item.select_one(".description, .offer-description, .restrictions")
            description = desc_el.get_text(strip=True) if desc_el else None

            # Look for a code reveal button or code text
            code_el = item.select_one("[data-testid='code'], .code, .coupon-code, .reveal-code")
            code_text = ""
            if code_el:
                code_text = code_el.get("data-clipboard-text") or code_el.get_text(strip=True)
            code = _extract_code(code_text) or _extract_code(title)

            if not code:
                # No code needed (automatic discount) — generate a placeholder
                code = f"AUTO_{retailer.upper()[:4]}"

            discount_type, discount_value = _parse_discount(title + " " + (description or ""))

            # Expiry
            expiry_el = item.select_one(".expires, .expiration, [data-testid='expires']")
            expiry_text = expiry_el.get_text(strip=True) if expiry_el else ""
            expires_at = _parse_expiry(expiry_text)

            coupons.append(ScrapedCoupon(
                code=code,
                retailer=retailer,
                title=title[:500],
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                source="retailmenot",
                source_url=url,
                expires_at=expires_at,
            ))
        except Exception as e:
            logger.debug(f"RetailMeNot parse error: {e}")
            continue

    logger.info(f"RetailMeNot {retailer}: {len(coupons)} coupons found")
    return coupons


# ─── Slickdeals Scraper ─────────────────────────────────────────────────────

async def scrape_slickdeals(retailer: str) -> list[ScrapedCoupon]:
    """Scrape coupon-coded deals from Slickdeals for a retailer."""
    url = f"https://slickdeals.net/coupons/{retailer}"
    headers = {
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    coupons: list[ScrapedCoupon] = []

    async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
        try:
            response = await client.get(url)
            if response.status_code != 200:
                logger.debug(f"Slickdeals {retailer}: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.debug(f"Slickdeals {retailer}: {e}")
            return []

    soup = BeautifulSoup(response.text, "html.parser")

    # Slickdeals deal cards
    deal_items = soup.select(".deal-card, .coupon-item, .item, [data-testid='deal-card']")

    for item in deal_items:
        try:
            title_el = item.select_one(".deal-title, .title, h3, a.titleLink")
            title = title_el.get_text(strip=True) if title_el else ""
            if not title:
                continue

            # Look for coupon code
            code_el = item.select_one(".coupon-code, .code, [data-clipboard-text]")
            code_text = ""
            if code_el:
                code_text = code_el.get("data-clipboard-text") or code_el.get_text(strip=True)
            code = _extract_code(code_text) or _extract_code(title)

            if not code:
                continue  # Slickdeals has many non-coupon deals; skip those

            desc_el = item.select_one(".deal-text, .description, .body")
            description = desc_el.get_text(strip=True) if desc_el else None

            discount_type, discount_value = _parse_discount(title + " " + (description or ""))

            # Link to deal
            link_el = item.select_one("a[href]")
            product_url = None
            if link_el and link_el.get("href"):
                href = link_el["href"]
                product_url = href if href.startswith("http") else f"https://slickdeals.net{href}"

            coupons.append(ScrapedCoupon(
                code=code,
                retailer=retailer,
                title=title[:500],
                description=description,
                discount_type=discount_type,
                discount_value=discount_value,
                product_url=product_url,
                source="slickdeals",
                source_url=url,
                expires_at=None,  # Slickdeals doesn't always show expiry
            ))
        except Exception as e:
            logger.debug(f"Slickdeals parse error: {e}")
            continue

    logger.info(f"Slickdeals {retailer}: {len(coupons)} coupons found")
    return coupons


# ─── Amazon Promo Scraper ───────────────────────────────────────────────────

async def scrape_amazon_promos() -> list[ScrapedCoupon]:
    """Scrape Amazon's coupon and promo pages."""
    urls = [
        "https://www.amazon.com/coupons",
        "https://www.amazon.com/gp/goldbox",
    ]
    headers = {
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
        "Accept-Language": "en-US,en;q=0.9",
    }

    coupons: list[ScrapedCoupon] = []

    async with httpx.AsyncClient(headers=headers, timeout=20.0, follow_redirects=True) as client:
        for url in urls:
            try:
                response = await client.get(url)
                if response.status_code != 200:
                    continue
            except Exception as e:
                logger.debug(f"Amazon promo {url}: {e}")
                continue

            soup = BeautifulSoup(response.text, "html.parser")

            # Amazon coupon cards
            cards = soup.select("[data-testid='coupon-card'], .coupon-item, .a-section .a-spacing-base")

            for card in cards:
                try:
                    title_el = card.select_one(".a-text-normal, h2, h3, .title")
                    title = title_el.get_text(strip=True) if title_el else ""
                    if not title:
                        continue

                    # Amazon coupons often show "Clip coupon" with the discount in title
                    discount_type, discount_value = _parse_discount(title)

                    if discount_value == 0:
                        continue

                    code = f"AMZ_CLIP_{hash(title) % 10000:04d}"

                    link_el = card.select_one("a[href]")
                    product_url = None
                    if link_el and link_el.get("href"):
                        href = link_el["href"]
                        product_url = href if href.startswith("http") else f"https://www.amazon.com{href}"

                    coupons.append(ScrapedCoupon(
                        code=code,
                        retailer="amazon",
                        title=title[:500],
                        discount_type=discount_type,
                        discount_value=discount_value,
                        product_url=product_url,
                        source="amazon_direct",
                        source_url=url,
                        expires_at=datetime.utcnow() + timedelta(hours=24),
                    ))
                except Exception:
                    continue

    logger.info(f"Amazon promos: {len(coupons)} coupons found")
    return coupons


# ─── Main scrape orchestrator ───────────────────────────────────────────────

async def scrape_all_coupons(retailers: Optional[list[str]] = None) -> list[ScrapedCoupon]:
    """Scrape coupons from all sources for the given retailers.

    Args:
        retailers: List of retailer names. If None, scrapes all known retailers.

    Returns:
        List of ScrapedCoupon objects, deduplicated by (code, retailer).
    """
    if retailers is None:
        retailers = list(RETAILMENOT_SLUGS.keys())

    tasks: list[asyncio.Task] = []

    # RetailMeNot for each retailer
    for retailer in retailers:
        tasks.append(asyncio.create_task(scrape_retailmenot(retailer)))

    # Slickdeals for supported retailers
    for retailer in retailers:
        if retailer in SLICKDEALS_COUPON_RETAILERS:
            tasks.append(asyncio.create_task(scrape_slickdeals(retailer)))

    # Amazon direct promos
    if "amazon" in retailers:
        tasks.append(asyncio.create_task(scrape_amazon_promos()))

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_coupons: list[ScrapedCoupon] = []
    seen: set[tuple[str, str]] = set()

    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Scrape task failed: {result}")
            continue
        for coupon in result:
            key = (coupon.code, coupon.retailer)
            if key not in seen:
                seen.add(key)
                all_coupons.append(coupon)

    logger.info(f"Total unique coupons scraped: {len(all_coupons)}")
    return all_coupons


# ─── Discount calculation ───────────────────────────────────────────────────

def calculate_discounted_price(
    original_price: Decimal,
    coupon: ScrapedCoupon,
) -> tuple[Decimal, Decimal]:
    """Calculate the effective price after applying a coupon.

    Returns (effective_price, discount_amount).
    """
    if coupon.discount_type == "percentage":
        discount = (original_price * coupon.discount_value / Decimal("100")).quantize(Decimal("0.01"))
        if coupon.max_discount and discount > coupon.max_discount:
            discount = coupon.max_discount
    elif coupon.discount_type == "fixed":
        discount = coupon.discount_value
    elif coupon.discount_type == "free_shipping":
        # Free shipping doesn't reduce product price directly
        # but saves ~$5-10 on shipping — return small discount
        discount = Decimal("5.99")
    else:
        discount = Decimal("0")

    # Check minimum purchase requirement
    if coupon.min_purchase and original_price < coupon.min_purchase:
        return original_price, Decimal("0")

    effective_price = original_price - discount
    if effective_price < Decimal("0"):
        effective_price = Decimal("0")

    return effective_price, discount
