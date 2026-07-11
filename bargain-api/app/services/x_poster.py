"""Make.com Webhook Integration for X Auto-Posting.

Sends deal tweets to a Make.com webhook, which then posts them to X
via Buffer. This runs 24/7 on our Railway server — no computer or
browser needed.

Setup:
1. Create a Make.com scenario: Webhook → Buffer → X
2. Set the webhook URL as env var: MAKE_WEBHOOK_URL
3. The API automatically sends new deals to the webhook

Env vars:
  MAKE_WEBHOOK_URL — The Make.com webhook URL
"""
import asyncio
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


def is_configured() -> bool:
    """Check if Make.com webhook URL is configured."""
    return bool(getattr(settings, "MAKE_WEBHOOK_URL", ""))


def _format_deal_tweet(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
) -> str:
    """Format a deal into a tweet (max 280 characters)."""
    retailer_names = {
        "amazon": "Amazon",
        "ebay": "eBay",
        "walmart": "Walmart",
        "home_depot": "Home Depot",
        "target": "Target",
        "best_buy": "Best Buy",
        "newegg": "Newegg",
        "costco": "Costco",
        "lowes": "Lowe's",
        "ace_hardware": "Ace Hardware",
        "corsair": "Corsair",
        "overstock": "Overstock",
        "bhphoto": "B&H Photo",
    }
    retailer_name = retailer_names.get(retailer, retailer.replace("_", " ").title())

    if deal_tier == "glitch":
        prefix = "⚡ PRICE ERROR"
        hashtags = "#priceerror #deal"
    elif deal_tier == "clearance":
        prefix = f"🔥 {discount_percent}% OFF"
        hashtags = "#deals #clearance"
    else:
        prefix = f"🔥 {discount_percent}% OFF"
        hashtags = "#deals #bargain"

    max_title_len = 80
    short_title = title[:max_title_len].strip()
    if len(title) > max_title_len:
        short_title += "…"

    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        price_line = f"${deal_price:.0f} (was ${original_price:.0f}) at {retailer_name}\nSave ${savings:.0f}"
    else:
        price_line = f"${deal_price:.0f} at {retailer_name}"

    tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}\n\n{hashtags}"

    if len(tweet) > 280:
        excess = len(tweet) - 280
        short_title = title[: max(20, max_title_len - excess - 1)].strip() + "…"
        tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}\n\n{hashtags}"
        if len(tweet) > 280:
            tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}"

    return tweet


async def send_deal_to_make(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
    image_url: Optional[str] = None,
) -> dict:
    """Send a deal to Make.com webhook for X posting via Buffer.

    Returns dict with status and tweet text.
    """
    if not is_configured():
        return {"status": "error", "error": "MAKE_WEBHOOK_URL not configured"}

    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    payload = {
        "text": tweet_text,
        "title": title,
        "price": deal_price,
        "original_price": original_price,
        "discount": discount_percent,
        "retailer": retailer,
        "url": deal_url,
        "image_url": image_url,
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                settings.MAKE_WEBHOOK_URL,
                json=payload,
            )
            if resp.status_code in (200, 201, 202):
                logger.info(f"Deal sent to Make.com: {title[:50]}")
                return {"status": "success", "tweet_text": tweet_text}
            else:
                logger.warning(f"Make.com webhook error: {resp.status_code}")
                return {"status": "error", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        logger.error(f"Failed to send to Make.com: {e}")
        return {"status": "error", "error": str(e)}


async def post_deal_to_x(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
    image_url: Optional[str] = None,
) -> dict:
    """Post a deal to X via Make.com webhook.

    This is the main entry point — called by the API endpoints.
    Sends the deal to Make.com, which posts it to X via Buffer.
    Runs 24/7 on the Railway server, no computer needed.
    """
    return await send_deal_to_make(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
        image_url=image_url,
    )
