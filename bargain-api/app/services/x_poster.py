"""X (Twitter) Auto-Posting Service.

Automatically posts deals to the @bargain4huntrs X account when new deals
are scraped. Uses OAuth 1.0a authentication with the X API v2.

Required env vars:
  X_CONSUMER_KEY        — API Key (Consumer Key)
  X_CONSUMER_SECRET     — API Key Secret (Consumer Secret)
  X_ACCESS_TOKEN        — Access Token for @bargain4huntrs
  X_ACCESS_TOKEN_SECRET — Access Token Secret
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)

X_API_BASE = "https://api.twitter.com/2"
X_UPLOAD_BASE = "https://upload.twitter.com/1.1/media"
X_OAUTH_TOKEN_URL = "https://api.twitter.com/oauth2/token"


@dataclass
class XPost:
    """A deal post for X."""
    text: str
    deal_url: str
    image_url: Optional[str] = None


def is_configured() -> bool:
    """Check if X API credentials are configured."""
    return bool(
        settings.X_CONSUMER_KEY
        and settings.X_CONSUMER_SECRET
        and settings.X_ACCESS_TOKEN
        and settings.X_ACCESS_TOKEN_SECRET
    )


def _format_deal_tweet(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    deal_tier: str = "clearance",
) -> str:
    """Format a deal into a tweet (max 280 characters).

    Examples:
        🔥 50% OFF — Samsung Galaxy Buds2 Pro
        $99.99 (was $199.99) at Amazon
        Save $100 → [affiliate link]
        #deals #clearance

        ⚡ PRICE ERROR — Def Leppard: Pyromania CD
        $5 (was $35) at Amazon — 86% OFF
        Save $30 → [affiliate link]
        #priceerror #deal
    """
    # Retailer display name
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
    }
    retailer_name = retailer_names.get(retailer, retailer.replace("_", " ").title())

    # Emoji based on deal type
    if deal_tier == "glitch":
        prefix = "⚡ PRICE ERROR"
        hashtags = "#priceerror #deal"
    elif deal_tier == "clearance":
        prefix = f"🔥 {discount_percent}% OFF"
        hashtags = "#deals #clearance"
    else:
        prefix = f"🔥 {discount_percent}% OFF"
        hashtags = "#deals #bargain"

    # Truncate title to fit within 280 chars
    # Reserve space for: prefix + price line + link + hashtags
    # Rough budget: 280 - len(prefix) - 60 (price line) - 23 (link) - 20 (hashtags) - formatting
    max_title_len = 80
    short_title = title[:max_title_len].strip()
    if len(title) > max_title_len:
        short_title += "…"

    # Build price line
    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        price_line = f"${deal_price:.0f} (was ${original_price:.0f}) at {retailer_name}\nSave ${savings:.0f}"
    else:
        price_line = f"${deal_price:.0f} at {retailer_name}"

    tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}\n\n{hashtags}"

    # Ensure under 280 chars
    if len(tweet) > 280:
        # Truncate title further
        excess = len(tweet) - 280
        short_title = title[: max(20, max_title_len - excess - 1)].strip() + "…"
        tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}\n\n{hashtags}"
        if len(tweet) > 280:
            # Last resort: cut hashtags
            tweet = f"{prefix}\n{short_title}\n{price_line}\n\n{deal_url}"

    return tweet


async def _download_image(url: str) -> Optional[bytes]:
    """Download an image from a URL. Returns bytes or None."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, follow_redirects=True)
            if resp.status_code == 200 and resp.content:
                # Verify it's an image
                content_type = resp.headers.get("content-type", "")
                if "image" in content_type or resp.content[:4] in (b"\x89PNG", b"\xff\xd8\xff\xe0", b"\xff\xd8\xff\xe1"):
                    return resp.content
    except Exception as e:
        logger.warning(f"Failed to download image {url}: {e}")
    return None


async def _upload_media(image_bytes: bytes) -> Optional[str]:
    """Upload an image to X and return the media_id.

    Uses the v1.1 media upload endpoint (v2 doesn't support media upload yet).
    """
    if not is_configured():
        return None

    auth = (
        settings.X_CONSUMER_KEY,
        settings.X_CONSUMER_SECRET,
        settings.X_ACCESS_TOKEN,
        settings.X_ACCESS_TOKEN_SECRET,
    )

    try:
        import tweepy
        # Use tweepy for OAuth 1.0a media upload (simpler than manual signing)
        auth_handler = tweepy.OAuth1UserHandler(
            auth[0], auth[1], auth[2], auth[3]
        )
        api = tweepy.API(auth_handler)
        # Upload media
        import io
        media = api.media_upload(filename="deal.jpg", file=io.BytesIO(image_bytes))
        return str(media.media_id)
    except ImportError:
        # tweepy not installed — use manual HTTP with httpx
        # We need to use OAuth 1.0a signed request for media upload
        # This is complex without a library, so we'll skip images for now
        logger.info("tweepy not installed — posting without image")
        return None
    except Exception as e:
        logger.warning(f"Failed to upload media to X: {e}")
        return None


async def post_tweet(
    text: str,
    image_url: Optional[str] = None,
) -> dict:
    """Post a tweet to the @bargain4huntrs account.

    Args:
        text: The tweet text (max 280 chars).
        image_url: Optional image URL to attach. Will be downloaded and uploaded.

    Returns:
        Dict with tweet ID and status, or error info.
    """
    if not is_configured():
        return {"status": "error", "error": "X API not configured"}

    # Download and upload image if provided
    media_id = None
    if image_url:
        image_bytes = await _download_image(image_url)
        if image_bytes:
            media_id = await _upload_media(image_bytes)

    # Post tweet using OAuth 1.0a
    # X API v2 requires OAuth 1.0a user context for posting
    try:
        import tweepy
        auth_handler = tweepy.OAuth1UserHandler(
            settings.X_CONSUMER_KEY,
            settings.X_CONSUMER_SECRET,
            settings.X_ACCESS_TOKEN,
            settings.X_ACCESS_TOKEN_SECRET,
        )
        api = tweepy.API(auth_handler)

        if media_id:
            tweet = api.update_status(status=text, media_ids=[media_id])
        else:
            tweet = api.update_status(status=text)

        logger.info(f"Posted tweet {tweet.id}: {text[:60]}...")
        return {
            "status": "success",
            "tweet_id": str(tweet.id),
            "url": f"https://x.com/bargain4huntrs/status/{tweet.id}",
        }

    except ImportError:
        # Fallback: use httpx with OAuth 1.0a manual signing
        return await _post_tweet_httpx(text, media_id)
    except Exception as e:
        logger.error(f"Failed to post tweet: {e}")
        return {"status": "error", "error": str(e)}


async def _post_tweet_httpx(text: str, media_id: Optional[str] = None) -> dict:
    """Post a tweet using httpx with OAuth 1.0a signature.

    Fallback when tweepy is not installed. Uses manual OAuth 1.0a signing.
    """
    try:
        from requests_oauthlib import OAuth1
        import requests

        auth = OAuth1(
            settings.X_CONSUMER_KEY,
            settings.X_CONSUMER_SECRET,
            settings.X_ACCESS_TOKEN,
            settings.X_ACCESS_TOKEN_SECRET,
        )

        payload = {"text": text}
        if media_id:
            payload["media"] = {"media_ids": [media_id]}

        # Use v2 endpoint
        resp = requests.post(
            f"{X_API_BASE}/tweets",
            json=payload,
            auth=auth,
            headers={"Content-Type": "application/json"},
        )

        if resp.status_code in (200, 201):
            data = resp.json()
            tweet_id = data.get("data", {}).get("id", "")
            logger.info(f"Posted tweet {tweet_id}: {text[:60]}...")
            return {
                "status": "success",
                "tweet_id": tweet_id,
                "url": f"https://x.com/bargain4huntrs/status/{tweet_id}",
            }
        else:
            logger.error(f"X API error: {resp.status_code} — {resp.text}")
            return {"status": "error", "error": f"{resp.status_code}: {resp.text}"}

    except ImportError:
        return {"status": "error", "error": "Neither tweepy nor requests-oauthlib installed"}
    except Exception as e:
        logger.error(f"Failed to post tweet via httpx: {e}")
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
    """Format a deal as a tweet and post it to X.

    Args:
        title: Product title.
        deal_price: Current sale price.
        original_price: Original/retail price (before discount).
        discount_percent: Discount percentage (e.g. 50 for 50% off).
        retailer: Retailer key (amazon, home_depot, etc.).
        deal_url: Affiliate link to the deal.
        deal_tier: "glitch", "clearance", or "arbitrage".
        image_url: Optional product image URL.

    Returns:
        Dict with tweet ID and status, or error info.
    """
    if not is_configured():
        return {"status": "error", "error": "X API not configured"}

    # Format the tweet
    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    # Post it
    return await post_tweet(tweet_text, image_url=image_url)
