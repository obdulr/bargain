"""Affiliate link injection service.

Appends affiliate tracking parameters to retailer URLs so the platform
earns commission on qualifying purchases. Falls back to plain URLs if
affiliate IDs are not configured.
"""
import urllib.parse
from app.core.config import settings


def add_amazon_affiliate(url: str, asin: str = "") -> str:
    """Add Amazon Associates tag to an Amazon product URL."""
    if not settings.AMAZON_ASSOCIATES_TAG:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}tag={settings.AMAZON_ASSOCIATES_TAG}"


def add_ebay_affiliate(url: str) -> str:
    """Add eBay Partner Network tracking to an eBay URL."""
    if not settings.EBAY_PARTNER_NETWORK_ID:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}campid={settings.EBAY_PARTNER_NETWORK_ID}"


def add_walmart_affiliate(url: str) -> str:
    """Add Walmart affiliate tracking."""
    if not settings.WALMART_AFFILIATE_ID:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}affid={settings.WALMART_AFFILIATE_ID}"


def add_target_affiliate(url: str) -> str:
    """Add Target affiliate tracking."""
    if not settings.TARGET_AFFILIATE_ID:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}affid={settings.TARGET_AFFILIATE_ID}"


def add_bestbuy_affiliate(url: str) -> str:
    """Add Best Buy affiliate tracking."""
    if not settings.BESTBUY_AFFILIATE_ID:
        return url
    separator = "&" if "?" in url else "?"
    return f"{url}{separator}affid={settings.BESTBUY_AFFILIATE_ID}"


def detect_retailer(url: str) -> str:
    """Detect the retailer from a URL. Returns lowercase retailer name or ''."""
    if not url:
        return ""
    url_lower = url.lower()
    if "amazon." in url_lower:
        return "amazon"
    if "ebay." in url_lower:
        return "ebay"
    if "walmart." in url_lower:
        return "walmart"
    if "target." in url_lower:
        return "target"
    if "bestbuy." in url_lower or "best buy" in url_lower:
        return "bestbuy"
    return ""


def add_affiliate_tag(url: str, retailer: str = "", asin: str = "") -> str:
    """Auto-detect retailer from URL and apply the correct affiliate tag.

    Tries Impact.com affiliate links first (for supported retailers like
    Walmart, ADOR, Eufy, etc.), then falls back to direct affiliate tags
    (Amazon Associates, eBay Partner Network, etc.).

    Falls back to the plain URL when no affiliate ID is configured or the
    retailer is unsupported.
    """
    if not url:
        return url

    # Don't affiliate-tag deal aggregator URLs — they're not retailer sites
    aggregator_domains = ["slickdeals.net", "dansdeals.com", "techbargains.com",
                          "bensbargains.com", "dealnews.com"]
    url_lower = url.lower()
    if any(domain in url_lower for domain in aggregator_domains):
        return url

    detected = retailer.lower() if retailer else detect_retailer(url)

    # Try Impact.com first (covers Walmart, ADOR, Eufy, Lenovo, etc.)
    try:
        from app.services.impact_affiliate import add_impact_affiliate
        impact_url = add_impact_affiliate(url, detected)
        if impact_url != url:
            return impact_url
    except Exception:
        pass

    # Fall back to direct affiliate tags
    if detected == "amazon":
        return add_amazon_affiliate(url, asin)
    if detected == "ebay":
        return add_ebay_affiliate(url)
    if detected == "walmart":
        return add_walmart_affiliate(url)
    if detected == "target":
        return add_target_affiliate(url)
    if detected == "bestbuy":
        return add_bestbuy_affiliate(url)
    return url
