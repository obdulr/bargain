"""Reddit poster using the Reddit API (OAuth2).

Posts deals to deal-focused subreddits like r/deals, r/buildapcsales,
r/dealsreddit. Uses Reddit's OAuth2 API via httpx (no PRAW dependency
needed — keeps the backend lightweight).

Requires:
  REDDIT_CLIENT_ID      - Reddit app client ID
  REDDIT_CLIENT_SECRET  - Reddit app client secret
  REDDIT_USERNAME       - Reddit account username
  REDDIT_PASSWORD       - Reddit account password
  REDDIT_USER_AGENT     - User agent string (e.g. "bargainhuntrs/1.0")

Get credentials at: https://www.reddit.com/prefs/apps
Create a "script" type app. Free, instant approval.
"""

import logging
from typing import Optional

import httpx

from app.core.config import settings
from app.services.utm_service import add_utm_parameters

logger = logging.getLogger(__name__)

REDDIT_API_BASE = "https://oauth.reddit.com"
REDDIT_AUTH_URL = "https://www.reddit.com/api/v1/access_token"

# Subreddits to post deals to (configurable via env)
DEFAULT_SUBREDDITS = "deals,buildapcsales,DealsReddit"


def is_configured() -> bool:
    """Check if Reddit posting is configured."""
    return bool(
        settings.REDDIT_CLIENT_ID
        and settings.REDDIT_CLIENT_SECRET
        and settings.REDDIT_USERNAME
        and settings.REDDIT_PASSWORD
    )


def _get_subreddits() -> list[str]:
    """Get the list of subreddits to post to."""
    subs_str = settings.REDDIT_SUBREDDITS or DEFAULT_SUBREDDITS
    return [s.strip() for s in subs_str.split(",") if s.strip()]


async def _get_access_token() -> Optional[str]:
    """Get an OAuth2 access token from Reddit."""
    try:
        auth = httpx.BasicAuth(
            username=settings.REDDIT_CLIENT_ID,
            password=settings.REDDIT_CLIENT_SECRET,
        )
        data = {
            "grant_type": "password",
            "username": settings.REDDIT_USERNAME,
            "password": settings.REDDIT_PASSWORD,
        }
        headers = {"User-Agent": settings.REDDIT_USER_AGENT or "bargainhuntrs/1.0"}

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                REDDIT_AUTH_URL,
                auth=auth,
                data=data,
                headers=headers,
            )
            if resp.status_code == 200:
                token = resp.json().get("access_token")
                if token:
                    logger.info("Reddit: access token obtained")
                    return token
                logger.warning("Reddit: no access_token in response")
            else:
                logger.warning(f"Reddit: auth failed {resp.status_code}: {resp.text[:200]}")
        return None
    except Exception as e:
        logger.error(f"Reddit: auth error: {e}")
        return None


def _format_deal_title(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
) -> str:
    """Format a deal title for Reddit (max 300 chars)."""
    retailer_name = retailer.replace("_", " ").title()

    if original_price and original_price > deal_price:
        price_str = f"${deal_price:.0f} (was ${original_price:.0f}) - {discount_percent}% off at {retailer_name}"
    else:
        price_str = f"${deal_price:.0f} at {retailer_name}"

    short_title = title[:200]
    if len(title) > 200:
        short_title += "..."

    reddit_title = f"[DEAL] {short_title} — {price_str}"

    if len(reddit_title) > 300:
        reddit_title = reddit_title[:297] + "..."

    return reddit_title


def _format_deal_body(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    image_url: Optional[str] = None,
) -> str:
    """Format the deal body/self-text for Reddit."""
    retailer_name = retailer.replace("_", " ").title()

    campaign = f"deal_alert_{__import__('datetime').datetime.utcnow().strftime('%Y-%m-%d')}"
    tagged_url = add_utm_parameters(deal_url, "reddit", "social", campaign)

    body = f"""**{title}**

**Price:** ${deal_price:.0f}"""
    if original_price and original_price > deal_price:
        savings = original_price - deal_price
        body += f" (was ${original_price:.0f} — save ${savings:.0f}, {discount_percent}% off)"
    body += f"\n\n**Retailer:** {retailer_name}\n\n"

    if image_url:
        body += f"![img]({image_url})\n\n"

    body += f"**Link:** {tagged_url}\n\n"
    body += "---\n"
    body += "*Posted by [BargainHuntrs](https://www.bargainhuntrs.com) — real-time deal alerts and arbitrage intelligence.*"

    return body


async def post_to_subreddit(
    subreddit: str,
    title: str,
    body: str,
    image_url: Optional[str] = None,
    access_token: Optional[str] = None,
) -> dict:
    """Post a link/text submission to a specific subreddit."""
    token = access_token
    if not token:
        token = await _get_access_token()
        if not token:
            return {"status": "error", "error": "Failed to get Reddit access token", "subreddit": subreddit}

    try:
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": settings.REDDIT_USER_AGENT or "bargainhuntrs/1.0",
        }

        # If we have an image URL, post as a link post (Reddit handles images better this way)
        # Otherwise post as a self post with body text
        if image_url and image_url.startswith("http"):
            data = {
                "kind": "link",
                "sr": f"r/{subreddit}",
                "title": title,
                "url": image_url,
                "api_type": "json",
            }
        else:
            data = {
                "kind": "self",
                "sr": f"r/{subreddit}",
                "title": title,
                "text": body,
                "api_type": "json",
            }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                f"{REDDIT_API_BASE}/api/submit",
                data=data,
                headers=headers,
            )

            if resp.status_code == 200:
                result = resp.json()
                if result.get("json", {}).get("errors"):
                    errors = result["json"]["errors"]
                    error_msg = "; ".join(str(e) for e in errors)
                    logger.warning(f"Reddit: r/{subreddit} post error: {error_msg}")
                    return {"status": "error", "error": error_msg, "subreddit": subreddit}
                else:
                    post_data = result.get("json", {}).get("data", {})
                    post_id = post_data.get("id", "")
                    logger.info(f"Reddit: posted to r/{subreddit} (id: {post_id})")
                    return {"status": "success", "post_id": post_id, "subreddit": subreddit}
            else:
                error_text = resp.text[:200]
                logger.warning(f"Reddit: r/{subreddit} failed {resp.status_code}: {error_text}")
                return {"status": "error", "error": f"HTTP {resp.status_code}: {error_text}", "subreddit": subreddit}

    except Exception as e:
        logger.error(f"Reddit: r/{subreddit} error: {e}")
        return {"status": "error", "error": str(e), "subreddit": subreddit}


async def post_deal_to_reddit(
    title: str,
    deal_price: float,
    original_price: Optional[float],
    discount_percent: int,
    retailer: str,
    deal_url: str,
    image_url: Optional[str] = None,
    deal_tier: str = "clearance",
) -> dict:
    """Post a deal to all configured subreddits.

    Returns a summary of all posting attempts.
    """
    if not is_configured():
        return {"status": "error", "error": "Reddit posting not configured"}

    subreddits = _get_subreddits()
    reddit_title = _format_deal_title(title, deal_price, original_price, discount_percent, retailer)
    reddit_body = _format_deal_body(
        title, deal_price, original_price, discount_percent, retailer, deal_url, image_url
    )

    # Get one access token and reuse it
    token = await _get_access_token()
    if not token:
        return {"status": "error", "error": "Failed to get Reddit access token"}

    results = []
    success_count = 0
    for sub in subreddits:
        result = await post_to_subreddit(sub, reddit_title, reddit_body, image_url, token)
        results.append(result)
        if result.get("status") == "success":
            success_count += 1

    return {
        "status": "success" if success_count > 0 else "error",
        "subreddits_posted": success_count,
        "subreddits_failed": len(subreddits) - success_count,
        "results": results,
    }
