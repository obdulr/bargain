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
import random
from datetime import datetime
from typing import Optional

import httpx

from app.core.config import settings
from app.services.utm_service import add_utm_parameters

logger = logging.getLogger(__name__)

BUFFER_API_URL = "https://api.buffer.com/graphql"
BUFFER_PENDING_URL = "https://api.buffer.com/1/pending.json"

FALLBACK_IMAGE_URL = getattr(settings, "FALLBACK_IMAGE_URL", "") or \
    "https://www.bargainhuntrs.com/logos/profile-icon-dark.png"


async def _verify_image_url(url: str) -> bool:
    """Verify that an image URL is reachable and returns an image.

    Does a HEAD request with a 5-second timeout. Returns True only if the
    response status is 200 and the content-type starts with "image/".
    """
    if not url:
        return False
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.head(url)
            if resp.status_code != 200:
                logger.warning(f"Image verification failed (HTTP {resp.status_code}): {url}")
                return False
            content_type = resp.headers.get("content-type", "").lower()
            if not content_type.startswith("image/"):
                logger.warning(f"Image verification failed (content-type '{content_type}'): {url}")
                return False
            return True
    except Exception as e:
        logger.warning(f"Image verification error for {url}: {e}")
        return False


async def get_buffer_queue_count(api_key: str, channel_id: str) -> int:
    """Query Buffer's REST API for the number of pending posts in the queue.

    Uses Buffer's pending updates endpoint:
      GET https://api.buffer.com/1/pending.json?access_token={api_key}

    Returns the count of pending updates. On error, returns 0 so that
    posting is still attempted (fail-open) rather than blocking forever.
    """
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                BUFFER_PENDING_URL,
                params={"access_token": api_key},
            )
            if resp.status_code == 200:
                data = resp.json()
                # The endpoint returns a list of pending updates
                updates = data if isinstance(data, list) else data.get("updates", [])
                return len(updates)
            else:
                logger.warning(
                    f"Buffer pending API returned HTTP {resp.status_code}: {resp.text[:200]}"
                )
                return 0
    except Exception as e:
        logger.warning(f"Failed to query Buffer queue count: {e}")
        return 0

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


# Hashtag sets per deal tier — randomly picked for variety
HASHTAG_SETS = {
    "clearance": [
        "#deals #clearance",
        "#DealAlert #ClearanceDeals",
        "#bargain #deals",
        "#AmazonDeals #SaveMoney",
        "#DealOfTheDay #Clearance",
    ],
    "glitch": [
        "#priceerror #deal",
        "#PriceError #GlitchDeal",
        "#PriceMistake #DealAlert",
        "#ErrorDeal #Bargain",
        "#Glitch #DealOfTheDay",
    ],
    "default": [
        "#deals #bargain",
        "#DealAlert #BargainHunt",
        "#SaveMoney #Deals",
        "#BargainHuntrs #Deals",
        "#DealOfTheDay #Bargain",
    ],
}

# Prefix variety by discount level — randomly picked for variety
PREFIX_SETS = {
    "75+": ["⚡ PRICE ERROR", "🚨 INSANE DEAL", "🔥 GLITCH ALERT", "💥 STEAL DEAL"],
    "50-74": ["🔥 MEGA DEAL", "🔥 HUGE SAVINGS", "⚡ BIG DISCOUNT", "💯 MAJOR DEAL"],
    "25-49": ["🔥 HOT DEAL", "💰 GREAT PRICE", "✨ NICE FIND", "🎯 GOOD DEAL"],
    "<25": ["💡 QUICK DEAL", "📌 SAVING", "✅ DEAL", "🏷️ MARKDOWN"],
}

# Call-to-action lines — added 50% of the time for variety
CTA_LINES = [
    "Run, don't walk! 🏃",
    "Limited time only ⏰",
    "Stock won't last! 📦",
    "Grab it before it's gone! ⚡",
    "This will sell out fast! 🔥",
    "Don't sleep on this! 😴❌",
]


def _pick_prefix(discount_percent: int, deal_tier: str) -> str:
    """Pick a randomized prefix based on discount level and deal tier."""
    if deal_tier == "glitch" or discount_percent >= 75:
        return random.choice(PREFIX_SETS["75+"])
    if discount_percent >= 50:
        return random.choice(PREFIX_SETS["50-74"])
    if discount_percent >= 25:
        return random.choice(PREFIX_SETS["25-49"])
    return random.choice(PREFIX_SETS["<25"])


def _format_deal_tweet(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
) -> str:
    """Format a deal into a tweet (max 280 characters) with varied formatting."""
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

    # Randomized prefix based on discount level / tier
    prefix = _pick_prefix(discount_percent, deal_tier)

    # Randomized hashtags per tier
    tier_key = deal_tier if deal_tier in HASHTAG_SETS else "default"
    hashtags = random.choice(HASHTAG_SETS[tier_key])

    max_title_len = 80
    short_title = title[:max_title_len].strip()
    if len(title) > max_title_len:
        short_title += "…"

    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        price_line = f"${deal_price:.0f} (was ${original_price:.0f}) at {retailer_name}\nSave ${savings:.0f}"
    else:
        price_line = f"${deal_price:.0f} at {retailer_name}"

    # Random CTA ~50% of the time
    cta = f" — {random.choice(CTA_LINES)}" if random.random() < 0.5 else ""

    # Tag outgoing deal link with UTM parameters for X/Twitter tracking
    campaign = f"deal_alert_{datetime.utcnow().strftime('%Y-%m-%d')}"
    deal_url = add_utm_parameters(deal_url, "twitter", "social", campaign)

    tweet = f"{prefix}\n{short_title}\n{price_line}{cta}\n\n{deal_url}\n\n{hashtags}"

    if len(tweet) > 280:
        excess = len(tweet) - 280
        short_title = title[: max(20, max_title_len - excess - 1)].strip() + "…"
        tweet = f"{prefix}\n{short_title}\n{price_line}{cta}\n\n{deal_url}\n\n{hashtags}"
        if len(tweet) > 280:
            tweet = f"{prefix}\n{short_title}\n{price_line}{cta}\n\n{deal_url}"

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
    # X/Twitter also gets images for better engagement
    # Verify the image URL before sending to Buffer; fall back to a branded
    # image if the deal image is missing or fails verification.
    img_to_use = image_url
    if img_to_use:
        if not await _verify_image_url(img_to_use):
            logger.warning(
                f"Image verification failed for {service}, using fallback image"
            )
            img_to_use = FALLBACK_IMAGE_URL
    else:
        # No image provided — use the branded fallback for all services
        img_to_use = FALLBACK_IMAGE_URL

    if img_to_use:
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

    # Check Buffer free plan queue limit before posting.
    # The Buffer free plan only allows 10 scheduled posts in the queue.
    # If the queue is full, skip posting to avoid silent failures.
    max_queue = getattr(settings, "BUFFER_MAX_QUEUE", 10)
    primary_channel_id = channels[0][0]
    queue_count = await get_buffer_queue_count(api_key, primary_channel_id)
    if queue_count >= max_queue:
        logger.warning(
            f"Buffer queue full ({queue_count}/{max_queue}). Skipping post to avoid errors."
        )
        return {
            "status": "queue_full",
            "queue_count": queue_count,
            "max_queue": max_queue,
            "error": f"Buffer queue full ({queue_count}/{max_queue})",
        }

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
