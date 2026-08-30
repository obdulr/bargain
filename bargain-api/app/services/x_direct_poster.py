"""Direct X/Twitter poster using X API v2.

Posts deals directly to X/Twitter without Buffer, bypassing the
free-tier queue limit (10 posts). The X API v2 free tier allows
1,500 posts/month (~50/day).

Requires:
  X_API_KEY            - Consumer API key (app)
  X_API_SECRET         - Consumer API secret (app)
  X_ACCESS_TOKEN       - Access token (user)
  X_ACCESS_TOKEN_SECRET - Access token secret (user)
  X_BEARER_TOKEN       - Bearer token (app, read-only)

Get these from: https://developer.x.com/en/portal/dashboard
Free tier: 1,500 posts/month, post creation enabled.
"""

import logging
import os
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse

import httpx

from app.core.config import settings
from app.services.utm_service import add_utm_parameters

logger = logging.getLogger(__name__)

X_API_BASE = "https://api.x.com/2"
X_UPLOAD_BASE = "https://upload.x.com/1.1/media"

# Rate limit: 1,500 posts/month on free tier
# We self-impose ~50/day to stay safe
MAX_POSTS_PER_DAY = 50


def is_configured() -> bool:
    """Check if X direct posting is configured."""
    return bool(
        settings.X_API_KEY
        and settings.X_API_SECRET
        and settings.X_ACCESS_TOKEN
        and settings.X_ACCESS_TOKEN_SECRET
    )


def _get_oauth1_headers() -> dict:
    """Build OAuth 1.0a headers for X API requests.

    Uses httpx-oauth if available, otherwise falls back to manual
    header construction. X API v2 post creation requires OAuth 1.0a
    with user context (access token).
    """
    # We use httpx with OAuth1 — simpler than building the header manually
    return {
        "Authorization": f"Bearer {settings.X_BEARER_TOKEN}",
    }


async def _upload_media(image_url: str, client: httpx.AsyncClient) -> Optional[str]:
    """Upload an image to X and return the media_id.

    X requires images to be uploaded separately before referencing
    them in a tweet. We download the image from the URL and upload
    it to X's media endpoint.
    """
    try:
        # Security: validate image URL to prevent SSRF
        from urllib.parse import urlparse
        import ipaddress
        parsed = urlparse(image_url)
        if parsed.scheme not in ("http", "https"):
            logger.warning(f"X direct: rejecting non-http image URL")
            return None
        hostname = parsed.hostname or ""
        if not hostname:
            return None
        try:
            ip = ipaddress.ip_address(hostname)
            if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved:
                logger.warning(f"X direct: rejecting internal IP image URL")
                return None
        except ValueError:
            pass
        if hostname in ("169.254.169.254", "metadata.google.internal", "metadata.azure.com"):
            return None

        # Download the image
        img_resp = await client.get(image_url, timeout=15.0)
        if img_resp.status_code != 200:
            logger.warning(f"X direct: image download failed {img_resp.status_code}")
            return None

        content_type = img_resp.headers.get("content-type", "")
        if "image" not in content_type and not image_url.endswith((".jpg", ".jpeg", ".png", ".gif", ".webp")):
            logger.warning(f"X direct: not an image ({content_type}), skipping media upload")
            return None

        # Determine media category
        if "gif" in content_type or image_url.endswith(".gif"):
            media_category = "tweet_gif"
        elif "png" in content_type or image_url.endswith(".png"):
            media_category = "tweet_image"
        else:
            media_category = "tweet_image"

        # Upload via OAuth1 — this requires the access token, not bearer
        # We'll use the media upload endpoint with multipart form data
        upload_url = f"{X_UPLOAD_BASE}/upload.json"
        files = {"media": img_resp.content}
        data = {"media_category": media_category}

        # Use OAuth1 for media upload
        from httpx_oauth.v1 import OAuth1Client

        async with OAuth1Client(
            client_id=settings.X_API_KEY,
            client_secret=settings.X_API_SECRET,
            token=settings.X_ACCESS_TOKEN,
            token_secret=settings.X_ACCESS_TOKEN_SECRET,
        ) as oauth_client:
            resp = await oauth_client.post(upload_url, data=data, files=files, timeout=30.0)

            if resp.status_code == 200:
                media_id = resp.json().get("media_id_string")
                logger.info(f"X direct: media uploaded (id: {media_id})")
                return media_id
            else:
                logger.warning(f"X direct: media upload failed {resp.status_code}: {resp.text[:200]}")
                return None

    except ImportError:
        logger.warning("httpx-oauth not installed — cannot upload media to X. Install with: pip install httpx-oauth")
        return None
    except Exception as e:
        logger.warning(f"X direct: media upload error: {e}")
        return None


async def post_tweet(
    text: str,
    image_url: Optional[str] = None,
) -> dict:
    """Post a tweet directly via X API v2.

    Returns dict with:
      - status: "success" or "error"
      - tweet_id: str (on success)
      - error: str (on failure)
    """
    if not is_configured():
        return {"status": "error", "error": "X direct posting not configured"}

    try:
        # Build tweet payload
        payload: dict = {"text": text}

        async with httpx.AsyncClient(timeout=30.0) as client:
            # Upload image if provided
            if image_url:
                media_id = await _upload_media(image_url, client)
                if media_id:
                    payload["media"] = {"media_ids": [media_id]}

            # Post the tweet using OAuth 1.0a User Context
            from httpx_oauth.v1 import OAuth1Client

            async with OAuth1Client(
                client_id=settings.X_API_KEY,
                client_secret=settings.X_API_SECRET,
                token=settings.X_ACCESS_TOKEN,
                token_secret=settings.X_ACCESS_TOKEN_SECRET,
            ) as oauth_client:
                resp = await oauth_client.post(
                    f"{X_API_BASE}/tweets",
                    json=payload,
                    timeout=30.0,
                )

                if resp.status_code in (200, 201):
                    data = resp.json()
                    tweet_id = data.get("data", {}).get("id", "")
                    logger.info(f"X direct: tweet posted (id: {tweet_id})")
                    return {"status": "success", "tweet_id": tweet_id, "data": data}
                else:
                    error_text = resp.text[:300]
                    logger.warning(f"X direct: tweet failed {resp.status_code}: {error_text}")
                    return {"status": "error", "error": f"HTTP {resp.status_code}: {error_text}"}

    except ImportError:
        return {"status": "error", "error": "httpx-oauth not installed. Run: pip install httpx-oauth"}
    except Exception as e:
        logger.error(f"X direct: post error: {e}")
        return {"status": "error", "error": str(e)}


async def post_deal_to_x_direct(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    image_url: Optional[str] = None,
    deal_tier: str = "clearance",
) -> dict:
    """Post a deal directly to X/Twitter.

    Reuses the same tweet formatting logic as the Buffer poster
    to keep messaging consistent across channels.
    """
    from app.services.x_poster import _format_deal_tweet

    tweet_text = _format_deal_tweet(
        title=title,
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        retailer=retailer,
        deal_url=deal_url,
        deal_tier=deal_tier,
    )

    return await post_tweet(tweet_text, image_url)
