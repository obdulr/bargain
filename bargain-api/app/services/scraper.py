from bs4 import BeautifulSoup
from decimal import Decimal, InvalidOperation
import httpx
from app.core.config import settings


async def fetch_price(url: str) -> tuple[Decimal | None, str | None]:
    """Fetch a product page and try to extract the current price."""
    headers = {"User-Agent": settings.USER_AGENT}
    async with httpx.AsyncClient(headers=headers, timeout=30.0) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except Exception:
            return None, None

    soup = BeautifulSoup(response.text, "html.parser")

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
