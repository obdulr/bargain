"""Discord webhook poster.

Posts deals to Discord channels via webhooks. No bot account or
app review needed — just create a webhook in any Discord channel.

Requires:
  DISCORD_WEBHOOK_URL  - Webhook URL from Discord channel settings
                         (can be comma-separated for multiple channels)

Setup:
  1. Open Discord server → Channel Settings → Integrations → Webhooks
  2. Click "New Webhook"
  3. Name it "BargainHuntrs"
  4. Copy the webhook URL
  5. Set DISCORD_WEBHOOK_URL in .env
"""

import logging
from datetime import datetime
from typing import Optional

import httpx

from app.core.config import settings
from app.services.utm_service import add_utm_parameters

logger = logging.getLogger(__name__)

# Discord webhook rate limit: 30 messages per 60 seconds per webhook
# We stay well under this


def is_configured() -> bool:
    """Check if Discord webhook posting is configured."""
    return bool(settings.DISCORD_WEBHOOK_URL)


def _get_webhook_urls() -> list[str]:
    """Get all configured webhook URLs (comma-separated)."""
    urls_str = settings.DISCORD_WEBHOOK_URL or ""
    return [u.strip() for u in urls_str.split(",") if u.strip() and u.strip().startswith("http")]


def _get_tier_color(deal_tier: str, discount_percent: int) -> int:
    """Get Discord embed color based on deal tier/discount."""
    if deal_tier == "glitch" or discount_percent >= 75:
        return 0x7C3AED  # Purple for price errors/glitches
    if discount_percent >= 50:
        return 0xEF4444  # Red for hot deals
    if discount_percent >= 25:
        return 0xF59E0B  # Orange for good deals
    return 0x10B981  # Green for standard deals


def _build_embed(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    image_url: Optional[str] = None,
    deal_tier: str = "clearance",
) -> dict:
    """Build a Discord rich embed for a deal."""
    retailer_name = retailer.replace("_", " ").title()
    color = _get_tier_color(deal_tier, discount_percent)

    campaign = f"deal_alert_{datetime.utcnow().strftime('%Y-%m-%d')}"
    tagged_url = add_utm_parameters(deal_url, "discord", "social", campaign)

    # Build description
    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        description = f"**${deal_price:.0f}** ~~${original_price:.0f}~~ — Save ${savings:.0f} ({discount_percent}% off)"
    else:
        description = f"**${deal_price:.0f}** at {retailer_name}"

    # Tier badge
    if deal_tier == "glitch":
        description = f"⚠️ **PRICE ERROR** ⚠️\n{description}"
    elif discount_percent >= 50:
        description = f"🔥 **HOT DEAL** 🔥\n{description}"

    embed: dict = {
        "title": title[:256],
        "description": description,
        "url": tagged_url,
        "color": color,
        "fields": [
            {"name": "Retailer", "value": retailer_name, "inline": True},
            {"name": "Discount", "value": f"{discount_percent}%", "inline": True},
            {"name": "Deal Tier", "value": deal_tier.title(), "inline": True},
        ],
        "footer": {"text": "BargainHuntrs — Real-time deal alerts", "icon_url": "https://www.bargainhuntrs.com/icon-192.png"},
        "timestamp": datetime.utcnow().isoformat(),
    }

    if image_url and image_url.startswith("http"):
        # Only set image if it's a real image URL (not SVG placeholder)
        if not image_url.endswith(".svg") and "placeholder" not in image_url:
            embed["image"] = {"url": image_url}

    return embed


async def post_to_webhook(webhook_url: str, embed: dict) -> dict:
    """Post an embed to a single Discord webhook."""
    try:
        payload = {
            "username": "BargainHuntrs",
            "embeds": [embed],
        }

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(webhook_url, json=payload)

            if resp.status_code in (200, 204):
                logger.info("Discord: posted to webhook successfully")
                return {"status": "success"}
            else:
                error_text = resp.text[:200]
                logger.warning(f"Discord: webhook failed {resp.status_code}: {error_text}")
                return {"status": "error", "error": f"HTTP {resp.status_code}: {error_text}"}

    except Exception as e:
        logger.error(f"Discord: webhook error: {e}")
        return {"status": "error", "error": str(e)}


async def post_deal_to_discord(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    image_url: Optional[str] = None,
    deal_tier: str = "clearance",
) -> dict:
    """Post a deal to all configured Discord webhooks.

    Returns a summary of all posting attempts.
    """
    if not is_configured():
        return {"status": "error", "error": "Discord webhook not configured"}

    webhooks = _get_webhook_urls()
    if not webhooks:
        return {"status": "error", "error": "No valid webhook URLs configured"}

    embed = _build_embed(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        image_url=image_url,
        deal_tier=deal_tier,
    )

    results = []
    success_count = 0
    for webhook_url in webhooks:
        result = await post_to_webhook(webhook_url, embed)
        results.append(result)
        if result.get("status") == "success":
            success_count += 1

    return {
        "status": "success" if success_count > 0 else "error",
        "webhooks_posted": success_count,
        "webhooks_failed": len(webhooks) - success_count,
        "results": results,
    }
