"""Pinterest poster using the Pinterest API v5.

Posts deals as Pins to a configured Pinterest board. Pinterest v5
creates pins directly from image URLs — no separate upload step.

Requires:
  PINTEREST_ACCESS_TOKEN - OAuth access token (user context)
  PINTEREST_BOARD_ID     - The board ID to pin to

Setup:
  1. Go to https://developers.pinterest.com/
  2. Create an app and get an access token
  3. Find your board ID (via the API or Pinterest app)
  4. Set PINTEREST_ACCESS_TOKEN and PINTEREST_BOARD_ID in .env

Pinterest API v5 docs: https://developers.pinterest.com/docs/api/v5/
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from app.core.config import settings
from app.services.utm_service import add_utm_parameters

logger = logging.getLogger(__name__)

PINTEREST_API_BASE = "https://api.pinterest.com/v5"

# Pinterest limits: title max 100 chars, description max 500 chars
MAX_TITLE_LENGTH = 100
MAX_DESCRIPTION_LENGTH = 500


def is_configured() -> bool:
    """Check if Pinterest posting is configured."""
    return bool(settings.PINTEREST_ACCESS_TOKEN and settings.PINTEREST_BOARD_ID)


def _build_pin_title(title: str) -> str:
    """Build a pin title (max 100 chars)."""
    return title[:MAX_TITLE_LENGTH]


def _build_pin_description(
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
) -> str:
    """Build a pin description (max 500 chars)."""
    retailer_name = retailer.replace("_", " ").title()

    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        price_line = f"${deal_price:.0f} (was ${original_price:.0f}) — Save ${savings:.0f} ({discount_percent}% off) at {retailer_name}"
    else:
        price_line = f"${deal_price:.0f} at {retailer_name}"

    description = f"{price_line}\n\nFind more deals at BargainHuntrs.com"
    return description[:MAX_DESCRIPTION_LENGTH]


def _build_pin_link(deal_url: str) -> str:
    """Build the pin link with UTM parameters."""
    campaign = f"deal_alert_{datetime.utcnow().strftime('%Y-%m-%d')}"
    return add_utm_parameters(deal_url, "pinterest", "social", campaign)


async def post_deal_to_pinterest(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    image_url: Optional[str] = None,
    deal_tier: str = "clearance",
) -> dict:
    """Post a deal as a Pin to Pinterest via API v5.

    Returns dict with:
      - status: "success" or "error"
      - pin_id: str (on success)
      - error: str (on failure)
    """
    if not is_configured():
        return {"status": "error", "error": "Pinterest posting not configured"}

    if not image_url or not image_url.startswith("http"):
        return {"status": "error", "error": "A valid image URL is required to create a Pin"}

    # Pinterest rejects SVG and placeholder images
    if image_url.endswith(".svg") or "placeholder" in image_url:
        return {"status": "error", "error": "Image URL must be a real image (not SVG/placeholder)"}

    try:
        pin_title = _build_pin_title(title)
        pin_description = _build_pin_description(
            deal_price=deal_price,
            original_price=original_price,
            discount_percent=discount_percent,
            retailer=retailer,
        )
        pin_link = _build_pin_link(deal_url) if deal_url else None

        payload: dict = {
            "board_id": settings.PINTEREST_BOARD_ID,
            "title": pin_title,
            "description": pin_description,
            "media_source": {
                "source_type": "image_url",
                "url": image_url,
            },
        }

        if pin_link:
            payload["link"] = pin_link

        headers = {
            "Authorization": f"Bearer {settings.PINTEREST_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "User-Agent": "BargainHuntrs/1.0 (https://www.bargainhuntrs.com)",
        }

        max_retries = 3
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                    resp = await client.post(
                        f"{PINTEREST_API_BASE}/pins",
                        json=payload,
                        headers=headers,
                    )

                    if resp.status_code in (200, 201):
                        data = resp.json()
                        pin_id = data.get("id", "")
                        logger.info(f"Pinterest: pin created (id: {pin_id})")
                        return {"status": "success", "pin_id": pin_id, "data": data}

                    if resp.status_code == 429:
                        import asyncio

                        retry_after = resp.headers.get("Retry-After", "5")
                        try:
                            wait = min(float(retry_after), 30.0)
                        except ValueError:
                            wait = 5.0 * (attempt + 1)

                        if attempt < max_retries - 1:
                            logger.warning(
                                f"Pinterest: 429 rate limited, retrying in {wait}s "
                                f"(attempt {attempt+1}/{max_retries})"
                            )
                            await asyncio.sleep(wait)
                            continue

                        error_text = resp.text[:300]
                        logger.warning(f"Pinterest: rate limited after {max_retries} retries: {error_text}")
                        return {"status": "error", "error": f"HTTP 429 rate limited (retried {max_retries}x): {error_text}"}

                    error_text = resp.text[:300]
                    logger.warning(f"Pinterest: pin creation failed {resp.status_code}: {error_text}")
                    return {"status": "error", "error": f"HTTP {resp.status_code}: {error_text}"}

            except httpx.HTTPError as e:
                if attempt < max_retries - 1:
                    import asyncio

                    logger.warning(f"Pinterest: network error on attempt {attempt+1}, retrying: {e}")
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                logger.error(f"Pinterest: network error after {max_retries} retries: {e}")
                return {"status": "error", "error": str(e)}

        return {"status": "error", "error": "Max retries exceeded"}

    except Exception as e:
        logger.error(f"Pinterest: post error: {e}")
        return {"status": "error", "error": str(e)}
