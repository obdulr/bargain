"""Impact Affiliate Network API client.

Fetches real, brand-issued promo codes from the Impact partner API.
Each coupon returned is a genuine code that the retailer has actually
issued — not a generated/fake code.

API docs: https://integrations.impact.com/partner-api-reference/reference/promo-codes/promo-codes

Required env vars:
  IMPACT_ACCOUNT_SID  — Impact Account SID (used as API username)
  IMPACT_AUTH_TOKEN   — Impact Auth Token (used as API password)
  IMPACT_PROGRAM_IDS  — Optional comma-separated program IDs to filter by
"""
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional
import asyncio
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

IMPACT_API_BASE = "https://api.impact.com"
IMPACT_PROMO_CODES_ENDPOINT = "/ImpactPartner/v15/PromoCodes"


@dataclass
class ImpactPromoCode:
    """A real promo code from Impact's API."""
    code: str
    program_name: str  # e.g. "Home Depot"
    retailer: str  # normalized retailer key (e.g. "homedepot")
    title: str
    description: str
    discount_type: str  # percentage, fixed, free_shipping
    discount_value: Decimal
    min_purchase: Optional[Decimal]
    max_discount: Optional[Decimal]
    category: Optional[str]
    tracking_url: str  # affiliate tracking link
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    state: str  # ACTIVE, FUTUREDATE, EXPIRED


# Mapping from Impact program names to our internal retailer keys
_PROGRAM_NAME_TO_RETAILER = {
    "home depot": "homedepot",
    "the home depot": "homedepot",
    "amazon": "amazon",
    "amazon.com": "amazon",
    "walmart": "walmart",
    "walmart.com": "walmart",
    "target": "target",
    "target.com": "target",
    "best buy": "bestbuy",
    "bestbuy": "bestbuy",
    "best buy co inc": "bestbuy",
    "newegg": "newegg",
    "newegg.com": "newegg",
    "costco": "costco",
    "costco.com": "costco",
    "ebay": "ebay",
    "ebay.com": "ebay",
    "sam's club": "samsclub",
    "sams club": "samsclub",
    "samsclub.com": "samsclub",
    "kohl's": "kohls",
    "kohls": "kohls",
    "kohls.com": "kohls",
    "macy's": "macys",
    "macys": "macys",
    "macys.com": "macys",
    "lowe's": "lowes",
    "lowes": "lowes",
    "lowes.com": "lowes",
    "lowe's companies": "lowes",
}


def _normalize_retailer(program_name: str) -> str:
    """Normalize an Impact program name to our internal retailer key."""
    return _PROGRAM_NAME_TO_RETAILER.get(program_name.lower().strip(), "")


def _parse_discount(title: str, description: str) -> tuple[str, Decimal, Optional[Decimal], Optional[Decimal]]:
    """Parse discount type and value from the coupon title/description.
    
    Returns (discount_type, discount_value, min_purchase, max_discount).
    """
    text = f"{title} {description}".lower()
    
    # Free shipping
    if "free shipping" in text or "free delivery" in text:
        return ("free_shipping", Decimal("0"), None, None)
    
    # Percentage off — look for patterns like "20% off", "save 25%"
    import re
    pct_match = re.search(r'(\d+)\s*%\s*(?:off|discount|save)', text)
    if pct_match:
        pct = Decimal(pct_match.group(1))
        max_disc = Decimal("100") if pct <= 50 else None
        return ("percentage", pct, None, max_disc)
    
    # Fixed amount off — look for patterns like "$25 off", "$50 off orders $250+"
    fixed_match = re.search(r'\$(\d+)\s*(?:off|discount|save)', text)
    min_match = re.search(r'(?:orders?|purchase|spend)\s*(?:of\s*)?\$(\d+)', text)
    if fixed_match:
        value = Decimal(fixed_match.group(1))
        min_purchase = Decimal(min_match.group(1)) if min_match else None
        return ("fixed", value, min_purchase, None)
    
    # B1G1 or similar
    if "b1g1" in text or "buy one get one" in text or "bogo" in text:
        return ("percentage", Decimal("50"), None, None)
    
    # Default: treat as a general promotion
    return ("percentage", Decimal("0"), None, None)


def _parse_date(date_str: str) -> Optional[datetime]:
    """Parse an Impact date string (ISO 8601)."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except (ValueError, TypeError):
        return None


def is_configured() -> bool:
    """Check if Impact API credentials are configured."""
    return bool(settings.IMPACT_ACCOUNT_SID and settings.IMPACT_AUTH_TOKEN)


async def fetch_promo_codes(
    program_ids: Optional[list[str]] = None,
    page_size: int = 100,
    max_pages: int = 10,
) -> list[ImpactPromoCode]:
    """Fetch real promo codes from the Impact API.
    
    Args:
        program_ids: Optional list of Impact program IDs to filter by.
                     If None, fetches from all approved programs.
        page_size: Number of results per page (max 1000 per Impact docs).
        max_pages: Maximum number of pages to fetch (safety limit).
    
    Returns:
        List of ImpactPromoCode objects with real, active promo codes.
    
    Raises:
        RuntimeError: If Impact credentials are not configured.
        httpx.HTTPError: If the API request fails.
    """
    if not is_configured():
        raise RuntimeError(
            "Impact API not configured. Set IMPACT_ACCOUNT_SID and IMPACT_AUTH_TOKEN."
        )
    
    auth = (settings.IMPACT_ACCOUNT_SID, settings.IMPACT_AUTH_TOKEN)
    
    # Build program ID filter
    program_filter = ""
    if program_ids:
        program_filter = ",".join(program_ids)
    
    # Also check env var for program IDs
    if not program_ids and settings.IMPACT_PROGRAM_IDS:
        program_ids = [p.strip() for p in settings.IMPACT_PROGRAM_IDS.split(",") if p.strip()]
        program_filter = ",".join(program_ids)
    
    all_promos: list[ImpactPromoCode] = []
    
    async with httpx.AsyncClient(auth=auth, timeout=30.0) as client:
        for page in range(1, max_pages + 1):
            params = {
                "PageSize": str(page_size),
                "Page": str(page),
                "State": "ACTIVE",  # Only active promo codes
            }
            if program_filter:
                params["ProgramId"] = program_filter
            
            try:
                response = await client.get(
                    f"{IMPACT_API_BASE}{IMPACT_PROMO_CODES_ENDPOINT}",
                    params=params,
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(f"Impact API error: {e.response.status_code} — {e.response.text}")
                break
            except httpx.HTTPError as e:
                logger.error(f"Impact API request failed: {e}")
                break
            
            data = response.json()
            promos = data.get("@items", [])
            total = data.get("@total", 0)
            
            for promo in promos:
                promo_code = _parse_promo_code(promo)
                if promo_code:
                    all_promos.append(promo_code)
            
            logger.info(f"Impact API page {page}: got {len(promos)} promos (total: {total})")
            
            # Check if we've fetched everything
            if len(promos) < page_size or len(all_promos) >= total:
                break
    
    logger.info(f"Fetched {len(all_promos)} active promo codes from Impact")
    return all_promos


def _parse_promo_code(raw: dict) -> Optional[ImpactPromoCode]:
    """Parse a raw Impact API promo code response into our dataclass."""
    try:
        code = raw.get("Code", "")
        if not code:
            return None
        
        program = raw.get("Program", {})
        program_name = program.get("Name", "")
        retailer = _normalize_retailer(program_name)
        
        # Skip coupons from retailers we don't support
        if not retailer:
            logger.debug(f"Skipping promo from unsupported program: {program_name}")
            return None
        
        deal = raw.get("Deal", {})
        title = deal.get("Name", "") or deal.get("Description", "") or "Promo Code"
        description = deal.get("Description", "") or ""
        
        discount_type, discount_value, min_purchase, max_discount = _parse_discount(title, description)
        
        # Get the affiliate tracking URL
        tracking_url = raw.get("TrackingUrl", "") or deal.get("Url", "") or ""
        
        # Parse dates
        start_date = _parse_date(raw.get("StartDate", ""))
        end_date = _parse_date(raw.get("EndDate", ""))
        state = raw.get("State", "ACTIVE")
        
        return ImpactPromoCode(
            code=code,
            program_name=program_name,
            retailer=retailer,
            title=title,
            description=description,
            discount_type=discount_type,
            discount_value=discount_value,
            min_purchase=min_purchase,
            max_discount=max_discount,
            category=None,  # Impact doesn't provide a category field directly
            tracking_url=tracking_url,
            start_date=start_date,
            end_date=end_date,
            state=state,
        )
    except Exception as e:
        logger.warning(f"Failed to parse Impact promo code: {e}")
        return None
