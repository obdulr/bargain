"""Affiliate Network Integrations.

Supports multiple affiliate networks for fetching deals, promo codes,
and generating affiliate tracking links. Each network has its own
auth method and API structure.

Supported Networks:
- Rakuten Advertising (OAuth 2.0, coupon feed API)
- Awin (Bearer token, promotions API)
- CJ Affiliate (Bearer token, link search API)
- Skimlinks (Product key, link conversion API)

Each network requires separate signup and approval. Once approved,
set the environment variables and the scrapers will automatically
pull deals from that network.

Env vars:
  RAKUTEN_WEBSERVICES_TOKEN — Rakuten Web Services token
  RAKUTEN_SECURITY_TOKEN    — Rakuten security token
  AWIN_API_TOKEN            — Awin API bearer token
  AWIN_PUBLISHER_ID         — Awin publisher ID
  CJ_ACCESS_TOKEN           — CJ Affiliate personal access token
  CJ_WEBSITE_ID             — CJ Affiliate website ID
  SKIMLINKS_PRODUCT_KEY     — Skimlinks product key
  SKIMLINKS_CLIENT_ID       — Skimlinks client ID
  SKIMLINKS_CLIENT_SECRET   — Skimlinks client secret
"""
import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class AffiliateDeal:
    """A deal from an affiliate network."""
    title: str
    deal_url: str  # Affiliate tracking URL
    original_url: str  # Original product URL
    retailer: str
    network: str  # Which affiliate network
    deal_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = None
    image_url: Optional[str] = None
    promo_code: Optional[str] = None
    description: str = ""
    expires_at: Optional[datetime] = None


# ============================================================
# Rakuten Advertising
# ============================================================
# API: https://api.linksynergy.com
# Auth: Web Services Token + Security Token
# Coupon Feed: https://api.linksynergy.com/coupon/1.0?token=...&network=1
# Sign up: https://pubhelp.rakutenadvertising.com

RAKUTEN_API_BASE = "https://api.linksynergy.com"


def _rakuten_configured() -> bool:
    return bool(getattr(settings, "RAKUTEN_WEBSERVICES_TOKEN", ""))


async def fetch_rakuten_coupons(max_results: int = 100) -> list[AffiliateDeal]:
    """Fetch coupons/deals from Rakuten Advertising Coupon Feed API.

    Requires RAKUTEN_WEBSERVICES_TOKEN env var.
    """
    if not _rakuten_configured():
        logger.info("Rakuten not configured — skipping")
        return []

    token = settings.RAKUTEN_WEBSERVICES_TOKEN
    deals: list[AffiliateDeal] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Coupon Feed API
            url = f"{RAKUTEN_API_BASE}/coupon/1.0"
            params = {
                "token": token,
                "network": "1",  # US network
                "resultsperpage": str(max_results),
                "pagenumber": "1",
            }
            resp = await client.get(url, params=params)

            if resp.status_code != 200:
                logger.warning(f"Rakuten API error: {resp.status_code}")
                return []

            # Rakuten returns XML
            soup = BeautifulSoup(resp.text, "xml")
            for link in soup.find_all("link"):
                try:
                    title = link.findtext("offername", "")
                    deal_url = link.findtext("clickurl", "")
                    original_url = link.findtext("url", "") or deal_url
                    promo_code = link.findtext("couponcode", "")
                    image = link.findtext("imageurl", "")
                    expires = link.findtext("offerend", "")
                    advertiser = link.findtext("advertisername", "")

                    if not title:
                        continue

                    retailer = _normalize_retailer(advertiser)
                    expires_at = None
                    if expires:
                        try:
                            expires_at = datetime.strptime(expires[:10], "%Y-%m-%d")
                        except (ValueError, TypeError):
                            pass

                    deals.append(AffiliateDeal(
                        title=title[:500],
                        deal_url=deal_url,
                        original_url=original_url,
                        retailer=retailer,
                        network="rakuten",
                        image_url=image if image else None,
                        promo_code=promo_code if promo_code else None,
                        description=f"{advertiser} — {link.findtext('offerdescription', '')}"[:1000],
                        expires_at=expires_at,
                    ))
                except Exception as e:
                    logger.debug(f"Failed to parse Rakuten coupon: {e}")

    except Exception as e:
        logger.error(f"Rakuten fetch failed: {e}")

    logger.info(f"Rakuten: {len(deals)} coupons fetched")
    return deals


# ============================================================
# Awin
# ============================================================
# API: https://api.awin.com
# Auth: Bearer token + Publisher ID
# Promotions: https://api.awin.com/promotions?accessToken=...&publisherId=...
# Sign up: https://ui.awin.com/publisher-signup/en

AWIN_API_BASE = "https://api.awin.com"


def _awin_configured() -> bool:
    return bool(getattr(settings, "AWIN_API_TOKEN", "")) and bool(getattr(settings, "AWIN_PUBLISHER_ID", ""))


async def fetch_awin_promotions(max_results: int = 100) -> list[AffiliateDeal]:
    """Fetch promotions/deals from Awin Promotions API.

    Requires AWIN_API_TOKEN and AWIN_PUBLISHER_ID env vars.
    """
    if not _awin_configured():
        logger.info("Awin not configured — skipping")
        return []

    token = settings.AWIN_API_TOKEN
    publisher_id = settings.AWIN_PUBLISHER_ID
    deals: list[AffiliateDeal] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Promotions API
            url = f"{AWIN_API_BASE}/promotions"
            params = {
                "accessToken": token,
                "publisherId": publisher_id,
                "promotionType": "voucher",  # voucher codes and promotions
                "region": "US",
                "pageSize": str(max_results),
            }
            resp = await client.get(url, params=params)

            if resp.status_code != 200:
                logger.warning(f"Awin API error: {resp.status_code}")
                return []

            data = resp.json()
            for promo in data.get("promotions", [])[:max_results]:
                try:
                    title = promo.get("title", "")
                    deal_url = promo.get("trackingUrl", "") or promo.get("url", "")
                    original_url = promo.get("url", "")
                    promo_code = promo.get("voucherCode", "")
                    image = promo.get("imageUrl", "")
                    advertiser = promo.get("advertiserName", "")
                    expires = promo.get("endDate", "")

                    if not title:
                        continue

                    retailer = _normalize_retailer(advertiser)
                    expires_at = None
                    if expires:
                        try:
                            expires_at = datetime.fromisoformat(expires.replace("Z", ""))
                        except (ValueError, TypeError):
                            pass

                    deals.append(AffiliateDeal(
                        title=title[:500],
                        deal_url=deal_url,
                        original_url=original_url,
                        retailer=retailer,
                        network="awin",
                        image_url=image if image else None,
                        promo_code=promo_code if promo_code else None,
                        description=promo.get("description", "")[:1000],
                        expires_at=expires_at,
                    ))
                except Exception as e:
                    logger.debug(f"Failed to parse Awin promo: {e}")

    except Exception as e:
        logger.error(f"Awin fetch failed: {e}")

    logger.info(f"Awin: {len(deals)} promotions fetched")
    return deals


# ============================================================
# CJ Affiliate
# ============================================================
# API: https://linksearch.api.cj.com/v2/link-search
# Auth: Bearer token (Personal Access Token)
# Sign up: https://signup.cj.com/member/signup/publisher/

CJ_API_BASE = "https://linksearch.api.cj.com/v2"


def _cj_configured() -> bool:
    return bool(getattr(settings, "CJ_ACCESS_TOKEN", "")) and bool(getattr(settings, "CJ_WEBSITE_ID", ""))


async def fetch_cj_links(max_results: int = 100) -> list[AffiliateDeal]:
    """Fetch promotional links from CJ Affiliate Link Search API.

    Requires CJ_ACCESS_TOKEN and CJ_WEBSITE_ID env vars.
    """
    if not _cj_configured():
        logger.info("CJ Affiliate not configured — skipping")
        return []

    token = settings.CJ_ACCESS_TOKEN
    website_id = settings.CJ_WEBSITE_ID
    deals: list[AffiliateDeal] = []

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Link Search API — fetch coupon/sale links
            url = f"{CJ_API_BASE}/link-search"
            headers = {"Authorization": f"Bearer {token}"}
            params = {
                "website-id": website_id,
                "promotion-type": "coupon",
                "page-size": str(max_results),
                "page-number": "1",
            }
            resp = await client.get(url, headers=headers, params=params)

            if resp.status_code != 200:
                logger.warning(f"CJ API error: {resp.status_code}")
                return []

            data = resp.json()
            for link in data.get("data", {}).get("links", [])[:max_results]:
                try:
                    title = link.get("linkName", "") or link.get("clickUrl", "")
                    deal_url = link.get("clickUrl", "")
                    original_url = link.get("destinationUrl", "") or deal_url
                    promo_code = link.get("couponCode", "")
                    image = link.get("imageUrl", "")
                    advertiser = link.get("advertiserName", "")
                    expires = link.get("promotionEndDate", "")

                    if not title:
                        continue

                    retailer = _normalize_retailer(advertiser)
                    expires_at = None
                    if expires:
                        try:
                            expires_at = datetime.fromisoformat(expires.replace("Z", ""))
                        except (ValueError, TypeError):
                            pass

                    deals.append(AffiliateDeal(
                        title=title[:500],
                        deal_url=deal_url,
                        original_url=original_url,
                        retailer=retailer,
                        network="cj",
                        image_url=image if image else None,
                        promo_code=promo_code if promo_code else None,
                        description=link.get("linkDescription", "")[:1000],
                        expires_at=expires_at,
                    ))
                except Exception as e:
                    logger.debug(f"Failed to parse CJ link: {e}")

    except Exception as e:
        logger.error(f"CJ fetch failed: {e}")

    logger.info(f"CJ: {len(deals)} links fetched")
    return deals


# ============================================================
# Skimlinks
# ============================================================
# API: http://api-merchants.skimlinks.com
# Auth: Product Key + Client ID/Secret
# Sign up: https://signup.skimlinks.com/en

SKIMLINKS_MERCHANT_API = "http://api-merchants.skimlinks.com"
SKIMLINKS_PRODUCT_API = "http://api-products.skimlinks.com"


def _skimlinks_configured() -> bool:
    return bool(getattr(settings, "SKIMLINKS_PRODUCT_KEY", ""))


async def fetch_skimlinks_offers(max_results: int = 100) -> list[AffiliateDeal]:
    """Fetch offers from Skimlinks.

    Requires SKIMLINKS_PRODUCT_KEY env var.
    Note: Full merchant API requires Managed tier.
    """
    if not _skimlinks_configured():
        logger.info("Skimlinks not configured — skipping")
        return []

    # Skimlinks doesn't have a direct deals/coupons API for non-managed tiers
    # But we can use the link conversion API to convert regular URLs to affiliate links
    # This is useful for converting scraped deal URLs to affiliate tracking URLs
    logger.info("Skimlinks: link conversion available (no direct deals API for non-managed tier)")
    return []


async def convert_skimlinks_url(url: str) -> str:
    """Convert a regular URL to a Skimlinks affiliate tracking URL.

    Requires SKIMLINKS_PRODUCT_KEY env var.
    """
    if not _skimlinks_configured():
        return url

    # Skimlinks uses a simple URL wrapping mechanism
    # https://go.skimresources.com?id=PRODUCT_KEY&url=ENCODED_URL
    product_key = settings.SKIMLINKS_PRODUCT_KEY
    return f"https://go.skimresources.com?id={product_key}&url={quote(url, safe='')}"


# ============================================================
# Utility Functions
# ============================================================

_RETAILER_MAP = {
    "walmart": "walmart",
    "walmart.com": "walmart",
    "home depot": "home_depot",
    "homedepot.com": "home_depot",
    "the home depot": "home_depot",
    "lowe's": "lowes",
    "lowes": "lowes",
    "lowes.com": "lowes",
    "target": "target",
    "target.com": "target",
    "best buy": "best_buy",
    "bestbuy.com": "best_buy",
    "newegg": "newegg",
    "newegg.com": "newegg",
    "costco": "costco",
    "costco.com": "costco",
    "wayfair": "wayfair",
    "wayfair.com": "wayfair",
    "macys": "macys",
    "macy's": "macys",
    "macy's inc.": "macys",
    "kohl's": "kohls",
    "kohls": "kohls",
    "sephora": "sephora",
    "nordstrom": "nordstrom",
    "adidas": "adidas",
    "nike": "nike",
    "puma": "puma",
    "levi's": "levis",
    "levi strauss": "levis",
    "reebok": "reebok",
    "warby parker": "warby_parker",
    "dyson": "dyson",
    "irobot": "irobot",
    "hellofresh": "hellofresh",
    "godaddy": "godaddy",
    "office depot": "office_depot",
    "officedepot": "office_depot",
    "verizon": "verizon",
    "shein": "shein",
    "fashion nova": "fashion_nova",
}


def _normalize_retailer(name: str) -> str:
    """Normalize a retailer name to our internal key."""
    name_lower = name.lower().strip()
    return _RETAILER_MAP.get(name_lower, name_lower.replace(" ", "_").replace("'", ""))


async def fetch_all_affiliate_deals() -> list[AffiliateDeal]:
    """Fetch deals from all configured affiliate networks.

    Returns combined list of deals from all networks.
    Only networks with configured credentials will be queried.
    """
    tasks = [
        fetch_rakuten_coupons(),
        fetch_awin_promotions(),
        fetch_cj_links(),
        fetch_skimlinks_offers(),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_deals: list[AffiliateDeal] = []
    for result in results:
        if isinstance(result, Exception):
            logger.warning(f"Affiliate network error: {result}")
            continue
        all_deals.extend(result)

    logger.info(f"Total affiliate deals: {len(all_deals)} from all networks")
    return all_deals


def get_configured_networks() -> list[str]:
    """Return list of configured affiliate network names."""
    configured = []
    if _rakuten_configured():
        configured.append("rakuten")
    if _awin_configured():
        configured.append("awin")
    if _cj_configured():
        configured.append("cj")
    if _skimlinks_configured():
        configured.append("skimlinks")
    return configured
