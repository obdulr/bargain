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
    """Fetch real coupons from the Impact affiliate network API.

    Args:
        retailers: Optional list of retailer names to filter by.
                   If None, fetches from all approved programs.

    Returns:
        List of ScrapedCoupon objects with real, working promo codes.
        Returns empty list if Impact is not configured.
    """
    if not impact_api.is_configured():
        logger.warning(
            "Impact API not configured — no coupons to fetch. "
            "Set IMPACT_ACCOUNT_SID and IMPACT_AUTH_TOKEN to enable real coupons."
        )
        return []

    try:
        impact_promos = await impact_api.fetch_promo_codes()
    except Exception as e:
        logger.error(f"Failed to fetch coupons from Impact: {e}")
        return []

    # Convert Impact promos to our ScrapedCoupon format
    coupons: list[ScrapedCoupon] = []
    for promo in impact_promos:
        # Filter by retailer if specified
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
            product_url=promo.tracking_url,  # Use the affiliate tracking URL
            source="impact",
            source_url=promo.tracking_url,
            expires_at=promo.end_date,
        )
        coupons.append(coupon)

    logger.info(f"Fetched {len(coupons)} real coupons from Impact API")
    return coupons


def is_coupon_source_configured() -> bool:
    """Check if a real coupon data source is configured."""
    return impact_api.is_configured()
