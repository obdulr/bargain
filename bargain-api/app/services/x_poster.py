"""Buffer API Integration for X Auto-Posting.

Posts deals directly to Buffer, which posts them to X (@bargain4huntrs).
Runs 24/7 on the Railway server — no computer, browser, or Make.com needed.

Env vars:
  BUFFER_API_KEY     — Buffer API access token
  BUFFER_CHANNEL_ID  — Buffer channel ID for X account
"""
import asyncio
import logging
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

BUFFER_API_URL = "https://api.buffer.com/graphql"


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


async def post_to_buffer(tweet_text: str) -> dict:
    """Post a tweet to Buffer via GraphQL API.

    Buffer will post it to X (@bargain4huntrs) automatically.
    """
    if not is_configured():
        return {"status": "error", "error": "BUFFER_API_KEY or BUFFER_CHANNEL_ID not set"}

    api_key = settings.BUFFER_API_KEY
    channel_id = settings.BUFFER_CHANNEL_ID

    # Buffer GraphQL mutation to create a post
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

    variables = {
        "input": {
            "channelId": channel_id,
            "text": tweet_text,
            "schedulingType": "automatic",
            "mode": "addToQueue",
        }
    }

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

                # Check for GraphQL errors
                if data.get("errors"):
                    error_msg = data["errors"][0].get("message", "Unknown error")
                    logger.error(f"Buffer GraphQL error: {error_msg}")
                    return {"status": "error", "error": error_msg}

                result = data.get("data", {}).get("createPost", {})

                if result.get("__typename") == "PostActionSuccess":
                    post = result.get("post", {})
                    logger.info(f"Buffer post created: {post.get('id')} (status: {post.get('status')})")
                    return {
                        "status": "success",
                        "post_id": post.get("id"),
                        "post_status": post.get("status"),
                    }
                else:
                    error_msg = result.get("message", "Unknown error")
                    logger.error(f"Buffer API error: {error_msg}")
                    return {"status": "error", "error": error_msg}
            else:
                logger.error(f"Buffer API HTTP error: {resp.status_code} {resp.text[:200]}")
                return {"status": "error", "error": f"HTTP {resp.status_code}"}

    except Exception as e:
        logger.error(f"Failed to post to Buffer: {e}")
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
    """Format a deal as a tweet and post it to X via Buffer API.

    Runs 24/7 on the Railway server. No computer, browser, or Make.com needed.
    """
    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    result = await post_to_buffer(tweet_text)

    if result.get("status") == "success":
        return {
            "status": "success",
            "post_id": result.get("post_id"),
            "tweet_text": tweet_text,
        }
    else:
        return {
            "status": "error",
            "error": result.get("error"),
            "tweet_text": tweet_text,
        }
