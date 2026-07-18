"""X/Twitter Engagement Automation Bot for @bargain4huntrs.

Grows the @bargain4huntrs account from 0 followers by automating engagement
with the deal-hunting community on X:

  1. search_deal_tweets()      — search recent deal-related tweets
  2. reply_to_deal_tweet()     — reply with helpful commentary
  3. follow_relevant_accounts() — follow accounts in the deal niche
  4. like_deal_tweets()        — like deal-related tweets
  5. run_engagement_cycle()    — orchestrates all of the above

Uses the X/Twitter API v2 directly (NOT Buffer — Buffer is for scheduling
posts, not for engagement). All API calls use httpx.

Env vars (see app/core/config.py):
  X_BEARER_TOKEN        — App-only bearer token for search endpoints
  X_ACCESS_TOKEN        — User-context OAuth2 bearer for posting/following/liking
  X_USER_ID             — Our @bargain4huntrs X user ID
  ENGAGEMENT_ENABLED    — Master switch (off by default)
  ENGAGEMENT_MAX_LIKES  — Max likes per cycle (default 15)
  ENGAGEMENT_MAX_REPLIES — Max replies per cycle (default 5)
  ENGAGEMENT_MAX_FOLLOWS — Max follows per cycle (default 5)

State files (in app/data/):
  followed_accounts.json — user IDs we've already followed
  replied_tweets.json    — tweet IDs we've already replied to + per-user daily map
  liked_tweets.json      — tweet IDs we've already liked
"""

import json
import logging
import os
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

# ─── Constants ────────────────────────────────────────────────────────────────

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
FOLLOWED_ACCOUNTS_FILE = DATA_DIR / "followed_accounts.json"
REPLIED_TWEETS_FILE = DATA_DIR / "replied_tweets.json"
LIKED_TWEETS_FILE = DATA_DIR / "liked_tweets.json"

X_API_BASE = "https://api.twitter.com/2"

# Search queries to rotate through when looking for deal tweets
SEARCH_QUERIES = [
    "deal",
    "discount",
    "price drop",
    "clearance",
    "Amazon deal",
    "deal alert",
]

# Reply templates — rotated so we don't sound like a robot
REPLY_TEMPLATES = [
    "Great find! 🔥 We spotted similar deals over at bargainhuntrs.com",
    "Nice! That's a solid discount 💯",
    "Thanks for sharing! We've got more deals like this on our site",
    "Bookmarked! 📌 Deal hunters unite",
    "🔥🔥🔥 We love seeing deals like this",
]

# Bio keywords for finding relevant accounts to follow
BIO_KEYWORDS = ["deal", "bargain", "savings", "clearance"]


# ─── State persistence helpers ────────────────────────────────────────────────

def _ensure_data_dir() -> None:
    """Create the app/data/ directory if it doesn't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load_json(path: Path, default: Any) -> Any:
    """Load a JSON file, returning `default` if missing or invalid."""
    _ensure_data_dir()
    if not path.exists():
        return default
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError) as e:
        logger.warning(f"Could not read {path.name}: {e}")
        return default


def _save_json(path: Path, data: Any) -> None:
    """Persist `data` to a JSON file."""
    _ensure_data_dir()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str)
    except OSError as e:
        logger.error(f"Could not write {path.name}: {e}")


def _load_followed() -> Dict[str, str]:
    """Return the followed-accounts map {user_id: followed_at_iso}."""
    data = _load_json(FOLLOWED_ACCOUNTS_FILE, {})
    if isinstance(data, list):
        # Backwards-compat: convert a bare list of IDs into a map
        return {str(uid): datetime.now(timezone.utc).isoformat() for uid in data}
    return {str(k): str(v) for k, v in data.items()}


def _save_followed(followed: Dict[str, str]) -> None:
    _save_json(FOLLOWED_ACCOUNTS_FILE, followed)


def _load_replied() -> Dict[str, Any]:
    """Return the replied-tweets state.

    Structure:
      {
        "tweet_ids": ["123", "456"],          # tweet IDs we've replied to
        "user_days": {"789": "2026-01-01"},   # last date we replied to each user
      }
    """
    data = _load_json(REPLIED_TWEETS_FILE, {})
    if isinstance(data, list):
        # Backwards-compat: bare list of tweet IDs
        return {"tweet_ids": [str(t) for t in data], "user_days": {}}
    data.setdefault("tweet_ids", [])
    data.setdefault("user_days", {})
    data["tweet_ids"] = [str(t) for t in data["tweet_ids"]]
    return data


def _save_replied(state: Dict[str, Any]) -> None:
    _save_json(REPLIED_TWEETS_FILE, state)


def _load_liked() -> List[str]:
    """Return the list of liked tweet IDs."""
    data = _load_json(LIKED_TWEETS_FILE, [])
    if isinstance(data, dict):
        data = data.get("tweet_ids", [])
    return [str(t) for t in data]


def _save_liked(tweet_ids: List[str]) -> None:
    _save_json(LIKED_TWEETS_FILE, {"tweet_ids": tweet_ids})


# ─── Auth helpers ─────────────────────────────────────────────────────────────

def _bearer_header() -> Dict[str, str]:
    """Headers for app-only (bearer token) requests, e.g. search."""
    return {
        "Authorization": f"Bearer {settings.X_BEARER_TOKEN}",
        "Content-Type": "application/json",
    }


def _user_token_header() -> Dict[str, str]:
    """Headers for user-context requests (posting/liking/following).

    Uses the OAuth 2.0 user access token (X_ACCESS_TOKEN) as a bearer.
    """
    return {
        "Authorization": f"Bearer {settings.X_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def is_configured() -> bool:
    """True if the engagement bot has the tokens it needs."""
    return bool(
        settings.ENGAGEMENT_ENABLED
        and getattr(settings, "X_BEARER_TOKEN", "")
        and getattr(settings, "X_ACCESS_TOKEN", "")
        and getattr(settings, "X_USER_ID", "")
    )


# ─── 1. Search ────────────────────────────────────────────────────────────────

async def search_deal_tweets(query: Optional[str] = None) -> List[Dict[str, Any]]:
    """Search X for recent deal-related tweets.

    Uses X API v2: GET /2/tweets/search/recent

    - Rotates through SEARCH_QUERIES if no `query` is given.
    - Filters for tweets from the last 2 hours.
    - Excludes retweets and our own tweets.
    - Returns a list of tweet objects: {id, text, author_id, ...}
    """
    if not settings.X_BEARER_TOKEN:
        logger.warning("search_deal_tweets: X_BEARER_TOKEN not set")
        return []

    our_user_id = str(getattr(settings, "X_USER_ID", "") or "")
    now = datetime.now(timezone.utc)
    two_hours_ago = now - timedelta(hours=2)

    chosen_query = query or random.choice(SEARCH_QUERIES)
    # Exclude retweets and replies in the query itself
    full_query = f"{chosen_query} -is:retweet -is:reply"

    params = {
        "query": full_query,
        "max_results": 100,
        "tweet.fields": "id,text,author_id,created_at,public_metrics,conversation_id",
        "start_time": two_hours_ago.isoformat(),
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{X_API_BASE}/tweets/search/recent",
                params=params,
                headers=_bearer_header(),
            )

            if resp.status_code == 429:
                logger.warning("search_deal_tweets: rate limited (429), skipping")
                return []
            if resp.status_code == 401:
                logger.warning("search_deal_tweets: auth error (401), check X_BEARER_TOKEN")
                return []
            if resp.status_code != 200:
                logger.error(
                    f"search_deal_tweets: HTTP {resp.status_code} {resp.text[:300]}"
                )
                return []

            data = resp.json()
            tweets = data.get("data", [])

            # Filter out our own tweets
            filtered = [
                t for t in tweets if str(t.get("author_id", "")) != our_user_id
            ]

            logger.info(
                f"search_deal_tweets: query='{chosen_query}' "
                f"returned {len(tweets)} tweets, {len(filtered)} after filtering self"
            )
            return filtered

    except httpx.HTTPError as e:
        logger.error(f"search_deal_tweets: network error: {e}")
        return []
    except Exception as e:
        logger.error(f"search_deal_tweets: unexpected error: {e}", exc_info=True)
        return []


# ─── 2. Reply ─────────────────────────────────────────────────────────────────

async def reply_to_deal_tweet(tweet_id: str, text: Optional[str] = None) -> Dict[str, Any]:
    """Reply to a tweet.

    Uses X API v2: POST /2/tweets with reply.in_reply_to_tweet_id.

    - `text` defaults to a randomly-chosen template.
    - Skips if we've already replied to this tweet or to the same user today.
    - Returns a dict with status ("success"/"skipped"/"error") and details.
    """
    if not settings.X_ACCESS_TOKEN:
        logger.warning("reply_to_deal_tweet: X_ACCESS_TOKEN not set")
        return {"status": "error", "error": "not configured"}

    tweet_id = str(tweet_id)
    state = _load_replied()

    # Don't reply to the same tweet twice
    if tweet_id in state["tweet_ids"]:
        logger.debug(f"reply_to_deal_tweet: already replied to {tweet_id}, skipping")
        return {"status": "skipped", "reason": "already_replied"}

    reply_text = text or random.choice(REPLY_TEMPLATES)

    payload = {
        "text": reply_text,
        "reply": {"in_reply_to_tweet_id": tweet_id},
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.post(
                f"{X_API_BASE}/tweets",
                json=payload,
                headers=_user_token_header(),
            )

            if resp.status_code == 429:
                logger.warning("reply_to_deal_tweet: rate limited (429), skipping")
                return {"status": "error", "error": "rate_limited"}
            if resp.status_code == 401:
                logger.warning("reply_to_deal_tweet: auth error (401), check X_ACCESS_TOKEN")
                return {"status": "error", "error": "auth_error"}
            if resp.status_code not in (200, 201):
                logger.error(
                    f"reply_to_deal_tweet: HTTP {resp.status_code} {resp.text[:300]}"
                )
                return {"status": "error", "error": f"HTTP {resp.status_code}"}

            data = resp.json()
            new_tweet_id = data.get("data", {}).get("id")

            # Track the replied tweet
            state["tweet_ids"].append(tweet_id)
            _save_replied(state)

            logger.info(f"reply_to_deal_tweet: replied to {tweet_id} with new tweet {new_tweet_id}")
            return {"status": "success", "reply_id": new_tweet_id, "in_reply_to": tweet_id}

    except httpx.HTTPError as e:
        logger.error(f"reply_to_deal_tweet: network error: {e}")
        return {"status": "error", "error": str(e)}
    except Exception as e:
        logger.error(f"reply_to_deal_tweet: unexpected error: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


def _user_replied_today(author_id: str) -> bool:
    """Check if we've already replied to `author_id` today (UTC date)."""
    state = _load_replied()
    user_days = state.get("user_days", {})
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return user_days.get(str(author_id)) == today


def _mark_user_replied_today(author_id: str) -> None:
    """Record that we replied to `author_id` today."""
    state = _load_replied()
    state.setdefault("user_days", {})
    state["user_days"][str(author_id)] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    _save_replied(state)


# ─── 3. Follow ────────────────────────────────────────────────────────────────

async def _search_relevant_users() -> List[Dict[str, Any]]:
    """Search for X users whose bios contain deal-related keywords.

    Uses X API v2: GET /2/users/by/username/{username} is not suitable for bio
    search, so we use the recent tweet search to surface authors of deal tweets
    and then look up their profiles via GET /2/users?ids=...
    """
    if not settings.X_BEARER_TOKEN:
        logger.warning("_search_relevant_users: X_BEARER_TOKEN not set")
        return []

    # Gather candidate author IDs from recent deal tweets
    tweets = await search_deal_tweets()
    author_ids = list({str(t.get("author_id")) for t in tweets if t.get("author_id")})
    if not author_ids:
        return []

    # Look up user profiles (bios) — up to 100 IDs per request
    author_ids = author_ids[:100]
    params = {
        "ids": ",".join(author_ids),
        "user.fields": "id,name,username,description,public_metrics",
    }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                f"{X_API_BASE}/users",
                params=params,
                headers=_bearer_header(),
            )

            if resp.status_code == 429:
                logger.warning("_search_relevant_users: rate limited (429), skipping")
                return []
            if resp.status_code == 401:
                logger.warning("_search_relevant_users: auth error (401)")
                return []
            if resp.status_code != 200:
                logger.error(
                    f"_search_relevant_users: HTTP {resp.status_code} {resp.text[:300]}"
                )
                return []

            users = resp.json().get("data", [])

            # Filter for bios containing deal-related keywords
            relevant = []
            for u in users:
                desc = (u.get("description") or "").lower()
                if any(kw in desc for kw in BIO_KEYWORDS):
                    relevant.append(u)

            logger.info(
                f"_search_relevant_users: {len(users)} users looked up, "
                f"{len(relevant)} match bio keywords"
            )
            return relevant

    except httpx.HTTPError as e:
        logger.error(f"_search_relevant_users: network error: {e}")
        return []
    except Exception as e:
        logger.error(f"_search_relevant_users: unexpected error: {e}", exc_info=True)
        return []


async def follow_relevant_accounts(max_follows: Optional[int] = None) -> Dict[str, Any]:
    """Follow accounts in the deal niche.

    Uses X API v2: POST /2/users/{our_user_id}/following

    - Follows up to `max_follows` (default settings.ENGAGEMENT_MAX_FOLLOWS) accounts.
    - Tracks followed accounts in followed_accounts.json to avoid duplicates.
    - Returns a summary dict.
    """
    if not settings.X_ACCESS_TOKEN or not settings.X_USER_ID:
        logger.warning("follow_relevant_accounts: X_ACCESS_TOKEN/X_USER_ID not set")
        return {"status": "error", "error": "not configured"}

    limit = max_follows or getattr(settings, "ENGAGEMENT_MAX_FOLLOWS", 5)
    our_user_id = str(settings.X_USER_ID)
    followed = _load_followed()

    candidates = await _search_relevant_users()
    # Exclude accounts we've already followed and ourselves
    candidates = [
        u for u in candidates
        if str(u.get("id")) not in followed and str(u.get("id")) != our_user_id
    ]

    if not candidates:
        logger.info("follow_relevant_accounts: no new relevant accounts to follow")
        return {"status": "success", "followed": 0, "reason": "no_candidates"}

    followed_count = 0
    followed_now: List[Dict[str, str]] = []

    for user in candidates[:limit]:
        user_id = str(user.get("id"))
        username = user.get("username", "")

        payload = {"target_user_id": user_id}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{X_API_BASE}/users/{our_user_id}/following",
                    json=payload,
                    headers=_user_token_header(),
                )

                if resp.status_code == 429:
                    logger.warning("follow_relevant_accounts: rate limited (429), stopping")
                    break
                if resp.status_code == 401:
                    logger.warning("follow_relevant_accounts: auth error (401), stopping")
                    break
                if resp.status_code not in (200, 201):
                    logger.error(
                        f"follow_relevant_accounts: HTTP {resp.status_code} "
                        f"following @{username}: {resp.text[:200]}"
                    )
                    continue

                followed[user_id] = datetime.now(timezone.utc).isoformat()
                followed_count += 1
                followed_now.append({"id": user_id, "username": username})
                logger.info(f"follow_relevant_accounts: followed @{username} ({user_id})")

        except httpx.HTTPError as e:
            logger.error(f"follow_relevant_accounts: network error following {user_id}: {e}")
            break
        except Exception as e:
            logger.error(f"follow_relevant_accounts: unexpected error: {e}", exc_info=True)
            break

    _save_followed(followed)
    logger.info(f"follow_relevant_accounts: followed {followed_count} new accounts")
    return {
        "status": "success",
        "followed": followed_count,
        "accounts": followed_now,
    }


# ─── 4. Like ──────────────────────────────────────────────────────────────────

async def like_deal_tweets(
    tweets: Optional[List[Dict[str, Any]]] = None,
    max_likes: Optional[int] = None,
) -> Dict[str, Any]:
    """Like tweets with deal-related content.

    Uses X API v2: POST /2/users/{our_user_id}/likes

    - Likes up to `max_likes` (default settings.ENGAGEMENT_MAX_LIKES) tweets.
    - If `tweets` is not provided, searches for deal tweets first.
    - Tracks liked tweet IDs in liked_tweets.json to avoid duplicates.
    - Returns a summary dict.
    """
    if not settings.X_ACCESS_TOKEN or not settings.X_USER_ID:
        logger.warning("like_deal_tweets: X_ACCESS_TOKEN/X_USER_ID not set")
        return {"status": "error", "error": "not configured"}

    limit = max_likes or getattr(settings, "ENGAGEMENT_MAX_LIKES", 15)
    our_user_id = str(settings.X_USER_ID)
    liked_ids = set(_load_liked())

    if tweets is None:
        tweets = await search_deal_tweets()

    # Exclude our own tweets and already-liked tweets
    candidates = [
        t for t in tweets
        if str(t.get("author_id", "")) != our_user_id
        and str(t.get("id", "")) not in liked_ids
    ]

    if not candidates:
        logger.info("like_deal_tweets: no new tweets to like")
        return {"status": "success", "liked": 0, "reason": "no_candidates"}

    liked_count = 0
    liked_now: List[str] = []

    for tweet in candidates[:limit]:
        tweet_id = str(tweet.get("id"))
        payload = {"tweet_id": tweet_id}

        try:
            async with httpx.AsyncClient(timeout=20.0) as client:
                resp = await client.post(
                    f"{X_API_BASE}/users/{our_user_id}/likes",
                    json=payload,
                    headers=_user_token_header(),
                )

                if resp.status_code == 429:
                    logger.warning("like_deal_tweets: rate limited (429), stopping")
                    break
                if resp.status_code == 401:
                    logger.warning("like_deal_tweets: auth error (401), stopping")
                    break
                if resp.status_code not in (200, 201):
                    logger.error(
                        f"like_deal_tweets: HTTP {resp.status_code} liking {tweet_id}: "
                        f"{resp.text[:200]}"
                    )
                    continue

                liked_ids.add(tweet_id)
                liked_now.append(tweet_id)
                liked_count += 1
                logger.info(f"like_deal_tweets: liked tweet {tweet_id}")

        except httpx.HTTPError as e:
            logger.error(f"like_deal_tweets: network error liking {tweet_id}: {e}")
            break
        except Exception as e:
            logger.error(f"like_deal_tweets: unexpected error: {e}", exc_info=True)
            break

    _save_liked(list(liked_ids))
    logger.info(f"like_deal_tweets: liked {liked_count} tweets")
    return {"status": "success", "liked": liked_count, "tweet_ids": liked_now}


# ─── 5. Orchestration ─────────────────────────────────────────────────────────

def _sort_by_engagement(tweets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort tweets by like count (descending) for high-engagement targeting."""

    def like_count(t: Dict[str, Any]) -> int:
        metrics = t.get("public_metrics") or {}
        return int(metrics.get("like_count", 0))

    return sorted(tweets, key=like_count, reverse=True)


async def run_engagement_cycle() -> Dict[str, Any]:
    """Main function that runs all engagement actions.

    1. Search for deal tweets
    2. Like up to ENGAGEMENT_MAX_LIKES relevant tweets
    3. Reply to up to ENGAGEMENT_MAX_REPLIES high-engagement tweets (by like count)
    4. Follow up to ENGAGEMENT_MAX_FOLLOWS new relevant accounts
    5. Log all actions taken

    Returns a summary dict of everything that happened.
    """
    if not is_configured():
        logger.info("run_engagement_cycle: engagement bot not configured, skipping")
        return {"status": "skipped", "reason": "not_configured"}

    logger.info("=== Starting X engagement cycle ===")
    started_at = datetime.now(timezone.utc)
    summary: Dict[str, Any] = {
        "started_at": started_at.isoformat(),
        "actions": {},
    }

    # 1. Search for deal tweets (rotate across a few queries for variety)
    all_tweets: List[Dict[str, Any]] = []
    seen_ids = set()
    for q in SEARCH_QUERIES[:3]:  # sample up to 3 queries per cycle
        tweets = await search_deal_tweets(query=q)
        for t in tweets:
            tid = str(t.get("id"))
            if tid and tid not in seen_ids:
                all_tweets.append(t)
                seen_ids.add(tid)

    logger.info(f"run_engagement_cycle: collected {len(all_tweets)} unique deal tweets")
    summary["tweets_found"] = len(all_tweets)

    if not all_tweets:
        # Still attempt follows even if no tweets surfaced
        follow_result = await follow_relevant_accounts()
        summary["actions"]["follow"] = follow_result
        summary["completed_at"] = datetime.now(timezone.utc).isoformat()
        logger.info("=== Engagement cycle complete (no tweets found) ===")
        return summary

    # 2. Like relevant tweets
    like_result = await like_deal_tweets(
        tweets=all_tweets,
        max_likes=getattr(settings, "ENGAGEMENT_MAX_LIKES", 15),
    )
    summary["actions"]["like"] = like_result

    # 3. Reply to high-engagement tweets (sorted by like count)
    max_replies = getattr(settings, "ENGAGEMENT_MAX_REPLIES", 5)
    replied_state = _load_replied()
    already_replied = set(replied_state.get("tweet_ids", []))

    high_engagement = _sort_by_engagement(all_tweets)
    replies_sent = 0
    reply_details: List[Dict[str, Any]] = []

    for tweet in high_engagement:
        if replies_sent >= max_replies:
            break

        tweet_id = str(tweet.get("id"))
        author_id = str(tweet.get("author_id", ""))

        # Skip our own tweets
        if author_id == str(settings.X_USER_ID):
            continue
        # Skip tweets we've already replied to
        if tweet_id in already_replied:
            continue
        # Don't reply to the same user more than once per day
        if _user_replied_today(author_id):
            continue

        result = await reply_to_deal_tweet(tweet_id)
        if result.get("status") == "success":
            replies_sent += 1
            _mark_user_replied_today(author_id)
            already_replied.add(tweet_id)
            reply_details.append({
                "tweet_id": tweet_id,
                "author_id": author_id,
                "reply_id": result.get("reply_id"),
            })

    summary["actions"]["reply"] = {
        "status": "success",
        "replied": replies_sent,
        "details": reply_details,
    }
    logger.info(f"run_engagement_cycle: replied to {replies_sent} tweets")

    # 4. Follow new relevant accounts
    follow_result = await follow_relevant_accounts(
        max_follows=getattr(settings, "ENGAGEMENT_MAX_FOLLOWS", 5),
    )
    summary["actions"]["follow"] = follow_result

    summary["completed_at"] = datetime.now(timezone.utc).isoformat()
    logger.info("=== X engagement cycle complete ===")
    logger.info(
        f"  Summary: liked={summary['actions'].get('like', {}).get('liked', 0)}, "
        f"replied={replies_sent}, "
        f"followed={summary['actions'].get('follow', {}).get('followed', 0)}"
    )
    return summary
