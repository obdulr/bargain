from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
from app.core.config import settings
from app.services.http_client import ScrapingClient


async def fetch_price(url: str) -> tuple[Decimal | None, str | None]:
    """Fetch a product page and try to extract the current price.

    Uses the anti-detection ScrapingClient with rotating user agents,
    rate limiting, and retry logic instead of a plain httpx client.
    """
    proxy = getattr(settings, "SCRAPER_PROXY_URL", "") or None
    rate_limit = getattr(settings, "SCRAPER_RATE_LIMIT_SECONDS", 2.0)
    max_retries = getattr(settings, "SCRAPER_MAX_RETRIES", 3)

    async with ScrapingClient(
        max_retries=max_retries,
        rate_limit_seconds=rate_limit,
        proxy_url=proxy,
    ) as client:
        html = await client.get_html(url)

    if not html:
        return None, None

    soup = BeautifulSoup(html, "lxml")

    # Try common price meta tags and selectors
    selectors = [
        "meta[property='product:price:amount']",
        "meta[itemprop='price']",
        "[data-testid='price']",
        ".a-price .a-offscreen",
        ".price",
        ".current-price",
        ".sale-price",
    ]

    for selector in selectors:
        element = soup.select_one(selector)
        if element:
            price_text = element.get("content") or element.get_text(strip=True)
            if price_text:
                price = _parse_price(price_text)
                if price is not None:
                    return price, None

    return None, None


def _parse_price(text: str) -> Decimal | None:
    """Parse a price string into a Decimal."""
    # Remove currency symbols and whitespace, keep digits, dot, comma
    cleaned = "".join(c for c in text if c.isdigit() or c in ".,").strip()
    if not cleaned:
        return None

    # Handle comma as decimal separator
    if cleaned.count(",") == 1 and cleaned.count(".") == 0:
        cleaned = cleaned.replace(",", ".")
    elif cleaned.count(",") > 0 and cleaned.count(".") > 0:
        cleaned = cleaned.replace(",", "")

    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None
