"""Buffer API Integration for Multi-Platform Auto-Posting.

Posts deals directly to Buffer, which posts them to:
  - X (@bargain4huntrs)
  - Instagram (@bargainhuntrs)
  - Facebook (Bargain Huntrs)

Runs 24/7 on the Railway server — no computer, browser, or Make.com needed.

Env vars:
  BUFFER_API_KEY      — Buffer API access token
  BUFFER_CHANNEL_ID   — Buffer channel ID for X account (primary)
  BUFFER_IG_CHANNEL_ID — Buffer channel ID for Instagram
  BUFFER_FB_CHANNEL_ID — Buffer channel ID for Facebook
"""
import asyncio
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BUFFER_API_URL = "https://api.buffer.com/graphql"

# All Buffer channel IDs — posts go to all configured channels
def _get_all_channel_ids() -> list[str]:
    """Get all configured Buffer channel IDs."""
    ids = []
    if getattr(settings, "BUFFER_CHANNEL_ID", ""):
        ids.append(settings.BUFFER_CHANNEL_ID)  # X/Twitter
    if getattr(settings, "BUFFER_IG_CHANNEL_ID", ""):
        ids.append(settings.BUFFER_IG_CHANNEL_ID)  # Instagram
    if getattr(settings, "BUFFER_FB_CHANNEL_ID", ""):
        ids.append(settings.BUFFER_FB_CHANNEL_ID)  # Facebook
    return ids


def is_configured() -> bool:
    """Check if Buffer API is configured."""
    return bool(getattr(settings, "BUFFER_API_KEY", "")) and \
           bool(getattr(settings, "BUFFER_CHANNEL_ID", ""))


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
        "ador": "ADOR",
        "eufy": "Eufy",
        "belkin": "Belkin",
        "lenovo": "Lenovo",
        "woot": "Woot",
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


async def _post_to_channel(api_key: str, channel_id: str, text: str, image_url: Optional[str] = None, service: str = "twitter") -> dict:
    """Post to a single Buffer channel via GraphQL API."""
    mutation = """
    mutation CreatePost($input: CreatePostInput!) {
      createPost(input: $input) {
        __typename
        ... on PostActionSuccess {
          post {
            id
            status
          }
        }
        ... on MutationError {
          message
        }
      }
    }
    """

    input_data = {
        "channelId": channel_id,
        "text": text,
        "schedulingType": "automatic",
        "mode": "addToQueue",
        "assets": [],
    }

    # Instagram and Facebook require metadata with post type
    metadata = {}
    if service == "instagram":
        metadata["instagram"] = {"type": "post", "shouldShareToFeed": True}
    elif service == "facebook":
        metadata["facebook"] = {"type": "post"}

    # Instagram requires at least one image
    # Facebook works better with an image too
    img_to_use = image_url
    if not img_to_use and service == "instagram":
        img_to_use = "https://www.bargainhuntrs.com/logos/profile-icon-dark.png"

    if img_to_use and service in ("instagram", "facebook"):
        input_data["assets"] = [{"image": {"url": img_to_use}}]

    if metadata:
        input_data["metadata"] = metadata

    variables = {"input": input_data}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                BUFFER_API_URL,
                json={"query": mutation, "variables": variables},
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
            )

            if resp.status_code == 200:
                data = resp.json()

                if data.get("errors"):
                    error_msg = data["errors"][0].get("message", "Unknown error")
                    logger.error(f"Buffer GraphQL error ({service}): {error_msg}")
                    return {"status": "error", "error": error_msg, "channel_id": channel_id, "service": service}

                result = data.get("data", {}).get("createPost", {})

                if result.get("__typename") == "PostActionSuccess":
                    post = result.get("post", {})
                    logger.info(f"Buffer post created: {post.get('id')} ({service})")
                    return {
                        "status": "success",
                        "post_id": post.get("id"),
                        "channel_id": channel_id,
                        "service": service,
                    }
                else:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"Buffer API error ({service}): {error_msg}")
                    return {"status": "error", "error": error_msg, "channel_id": channel_id, "service": service}
            else:
                logger.error(f"Buffer API HTTP error ({service}): {resp.status_code} {resp.text[:200]}")
                return {"status": "error", "error": f"HTTP {resp.status_code}", "channel_id": channel_id, "service": service}

    except Exception as e:
        logger.error(f"Failed to post to Buffer ({service}): {e}")
        return {"status": "error", "error": str(e), "channel_id": channel_id, "service": service}


async def post_to_buffer(tweet_text: str, image_url: Optional[str] = None) -> dict:
    """Post to all configured Buffer channels (X, Instagram, Facebook).

    Buffer will post to each platform automatically.
    """
    if not is_configured():
        return {"status": "error", "error": "BUFFER_API_KEY or BUFFER_CHANNEL_ID not set"}

    api_key = settings.BUFFER_API_KEY

    # Build channel list with service types
    channels = []
    if getattr(settings, "BUFFER_CHANNEL_ID", ""):
        channels.append((settings.BUFFER_CHANNEL_ID, "twitter"))
    if getattr(settings, "BUFFER_IG_CHANNEL_ID", ""):
        channels.append((settings.BUFFER_IG_CHANNEL_ID, "instagram"))
    if getattr(settings, "BUFFER_FB_CHANNEL_ID", ""):
        channels.append((settings.BUFFER_FB_CHANNEL_ID, "facebook"))

    if not channels:
        return {"status": "error", "error": "No Buffer channels configured"}

    # Post to all channels concurrently
    tasks = [_post_to_channel(api_key, cid, tweet_text, image_url, svc) for cid, svc in channels]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = [r for r in results if isinstance(r, dict) and r.get("status") == "success"]
    failures = [r for r in results if isinstance(r, dict) and r.get("status") == "error"]

    if successes:
        return {
            "status": "success",
            "post_id": successes[0].get("post_id"),
            "channels_posted": len(successes),
            "channels_failed": len(failures),
            "results": results,
        }
    else:
        return {
            "status": "error",
            "error": "; ".join(f.get("error", "?") for f in failures) or "All channels failed",
            "results": results,
        }


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
    """Format a deal as a post and send it to all social platforms via Buffer.

    Posts to X (@bargain4huntrs), Instagram (@bargainhuntrs), and
    Facebook (Bargain Huntrs) simultaneously.
    """
    # Ensure deal URL has affiliate tag
    try:
        from app.services.affiliate_service import add_affiliate_tag
        deal_url = add_affiliate_tag(deal_url, retailer)
    except Exception:
        pass

    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    result = await post_to_buffer(tweet_text, image_url=image_url)

    if result.get("status") == "success":
        return {
            "status": "success",
            "post_id": result.get("post_id"),
            "channels_posted": result.get("channels_posted", 0),
            "channels_failed": result.get("channels_failed", 0),
            "tweet_text": tweet_text,
        }
    else:
        return {
            "status": "error",
            "error": result.get("error"),
            "tweet_text": tweet_text,
        }
