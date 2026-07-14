"""
Coupon Scraper Service

Fetches real promo codes from the Impact affiliate network API.
When Impact credentials are not configured, returns an empty list
(no fake/generated codes).

To enable real coupons:
1. Sign up at https://app.impact.com as a publisher/partner
2. Apply to retailer affiliate programs (Home Depot, Amazon, etc.)
3. Set env vars: IMPACT_ACCOUNT_SID, IMPACT_AUTH_TOKEN, IMPACT_PROGRAM_IDS
"""

from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
from typing import Optional
import asyncio
import logging

from app.core.config import settings
from app.services import impact_api

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
    source: str = "impact"  # impact, manual
    source_url: str = ""
    expires_at: Optional[datetime] = None


# Retailers we support (used by the frontend for filtering)
SUPPORTED_RETAILERS = [
    "amazon", "walmart", "target", "bestbuy", "homedepot",
    "newegg", "costco", "ebay", "samsclub", "kohls",
    "macys", "lowes",
]


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
        if coupon.min_purchase and original_price < coupon.min_purchase:
            discount = Decimal("0")
    elif coupon.discount_type == "free_shipping":
        discount = Decimal("0")
    else:
        discount = Decimal("0")

    effective_price = (original_price - discount).quantize(Decimal("0.01"))
    if effective_price < Decimal("0"):
        effective_price = Decimal("0")

    return effective_price, discount


# ─── Main scrape orchestrator ───────────────────────────────────────────────

async def scrape_all_coupons(retailers: Optional[list[str]] = None) -> list[ScrapedCoupon]:
    """Fetch coupons from Impact.com and public RSS feeds.

    Args:
        retailers: Optional list of retailer names to filter by.

    Returns:
        List of ScrapedCoupon objects with real promo codes.
    """
    coupons: list[ScrapedCoupon] = []

    # Try Impact.com first
    if impact_api.is_configured():
        try:
            impact_promos = await impact_api.fetch_promo_codes()
            for promo in impact_promos:
                if retailers and promo.retailer not in retailers:
                    continue
                coupon = ScrapedCoupon(
                    code=promo.code,
                    retailer=promo.retailer,
                    title=promo.title,
                    description=promo.description,
                    discount_type=promo.discount_type,
                    discount_value=promo.discount_value,
                    min_purchase=promo.min_purchase,
                    max_discount=promo.max_discount,
                    category=promo.category,
                    product_url=promo.tracking_url,
                    source="impact",
                    source_url=promo.tracking_url,
                    expires_at=promo.end_date,
                )
                coupons.append(coupon)
        except Exception as e:
            logger.error(f"Failed to fetch coupons from Impact: {e}")

    # Also scrape public RSS feeds (always — no API key needed)
    try:
        from app.services.public_coupon_scraper import scrape_public_coupons
        public_coupons = await scrape_public_coupons()
        for pc in public_coupons:
            if retailers and pc.retailer not in retailers:
                continue
            coupon = ScrapedCoupon(
                code=pc.code,
                retailer=pc.retailer,
                title=pc.title,
                description=pc.description,
                discount_type=pc.discount_type,
                discount_value=pc.discount_value,
                category=pc.category,
                product_url=pc.source_url,
                source="rss",
                source_url=pc.source_url,
                expires_at=pc.expires_at,
            )
            coupons.append(coupon)
    except Exception as e:
        logger.error(f"Failed to scrape public coupon feeds: {e}")

    logger.info(f"Fetched {len(coupons)} coupons (Impact + public RSS)")
    return coupons


def is_coupon_source_configured() -> bool:
    """Check if a coupon data source is available (Impact API or public RSS feeds)."""
    return True  # Public RSS feeds are always available
