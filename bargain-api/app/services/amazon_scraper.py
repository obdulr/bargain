"""
Amazon Scraper — Self-contained, no API dependencies.

Scrapes Amazon product pages directly to extract:
- Product title, brand, category
- Current price
- BSR (Best Seller Rank)
- Images
- Stock status
- Price history (from our own PriceSnapshot database, not Keepa)

Uses anti-detection HTTP client with rotating user agents and rate limiting.

If a Keepa API key IS configured, it is used as the primary data source
(better historical data) and scraping is the fallback. Without a key, the
scraper works entirely on its own and builds price history from PriceSnapshot
rows that it saves on every fetch.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import asyncio
import logging
import re

from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.scraper import _parse_price
from app.services.deal_criteria import PriceHistory
from app.services.affiliate_service import add_affiliate_tag
from app.services.http_client import ScrapingClient

logger = logging.getLogger(__name__)


@dataclass
class AmazonProduct:
    """Amazon product data."""
    asin: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[Decimal] = None
    bsr: Optional[int] = None  # Best Seller Rank
    image_url: Optional[str] = None
    url: str = ""
    price_history: PriceHistory = field(default_factory=PriceHistory)
    in_stock: bool = True

    def __post_init__(self):
        if not self.url:
            self.url = add_affiliate_tag(
                f"https://www.amazon.com/dp/{self.asin}", "amazon", self.asin
            )


# Keepa API endpoints (optional enhancement when KEEPA_API_KEY is set)
KEEPA_API_BASE = "https://api.keepa.com"
KEEPA_PRODUCT_ENDPOINT = f"{KEEPA_API_BASE}/product"


def _keepa_time_to_datetime(keepa_minutes: int) -> datetime:
    """Convert Keepa time (minutes since epoch) to datetime."""
    return datetime(1970, 1, 1) + timedelta(minutes=keepa_minutes)


def _keepa_price_to_decimal(price_cents: int) -> Decimal:
    """Convert Keepa price (cents) to Decimal dollars."""
    return (Decimal(str(price_cents)) / Decimal("100")).quantize(Decimal("0.01"))


# ---------------------------------------------------------------------------
# Price snapshot persistence (our own price history, replaces Keepa)
# ---------------------------------------------------------------------------


def save_price_snapshot(
    asin: str,
    price: Decimal,
    retailer: str = "amazon",
    db_session=None,
) -> None:
    """Save a price snapshot to the database.

    Builds our own price history over time. If no database session is
    provided, the snapshot is silently skipped (backward compatible).
    """
    if db_session is None or price is None:
        return
    try:
        from app.db.models import PriceSnapshot

        snapshot = PriceSnapshot(
            item_id=asin,
            retailer=retailer,
            price=price,
            currency="USD",
        )
        db_session.add(snapshot)
        db_session.commit()
    except Exception as e:
        logger.warning(f"Failed to save price snapshot for {asin}: {e}")
        try:
            db_session.rollback()
        except Exception:
            pass


def get_price_history_from_db(asin: str, days: int = 90, db_session=None) -> PriceHistory:
    """Query PriceSnapshot for the given ASIN and return a PriceHistory object.

    This replaces Keepa's historical data with our own accumulated snapshots.
    If no database session is provided, an empty PriceHistory is returned.
    """
    history = PriceHistory()
    if db_session is None:
        return history
    try:
        from app.db.models import PriceSnapshot

        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            db_session.query(PriceSnapshot)
            .filter(
                PriceSnapshot.item_id == asin,
                PriceSnapshot.retailer == "amazon",
                PriceSnapshot.timestamp >= cutoff,
            )
            .order_by(PriceSnapshot.timestamp.asc())
            .all()
        )
        for row in rows:
            if row.price is not None:
                history.prices.append((row.timestamp, Decimal(str(row.price))))
    except Exception as e:
        logger.warning(f"Failed to load price history for {asin}: {e}")

    return history


# ---------------------------------------------------------------------------
# HTML scraping (primary path — no API required)
# ---------------------------------------------------------------------------


def _extract_price(soup: BeautifulSoup) -> Optional[Decimal]:
    """Try multiple selectors to extract the current price from an Amazon page."""
    selectors = [
        # Newer unified price block
        "span.a-price .a-offscreen",
        "#priceblock_ourprice",
        "#priceblock_dealprice",
        "#priceblock_saleprice",
        "#priceblock_pospromoprice",
        "span.apexPriceToPay",
        "#corePrice_feature_div .a-offscreen",
        "#corePriceDisplay_desktop_feature_div .a-offscreen",
        "#tp_price_block_total_price_ww .a-offscreen",
        "#price_inside_buybox",
        "input[name='displayedPrice']",
        "#buybox .a-color-price",
        "#addToCart_feature_div .a-color-price",
    ]

    for selector in selectors:
        el = soup.select_one(selector)
        if not el:
            continue
        # input elements store the value in the "value" attribute
        text = el.get("value") if el.name == "input" else el.get_text(strip=True)
        if not text:
            continue
        price = _parse_price(text)
        if price is not None and price > 0:
            return price

    # Last resort: any element with a data attribute holding a price
    for el in soup.select("[data-a-price]"):
        raw = el.get("data-a-price")
        if raw:
            price = _parse_price(raw)
            if price is not None and price > 0:
                return price

    return None


def _extract_bsr(soup: BeautifulSoup) -> Optional[int]:
    """Extract the Best Sellers Rank from the product details section."""
    # Detail bullets wrapper (newer layout)
    detail_sections = soup.select(
        "#productDetails_detailBullets_sections1, #detailBulletsWrapper_feature_div, "
        "#prodDetails, #productDetails_techSpec_section_1, #detailBullets_feature_div"
    )
    for section in detail_sections:
        text = section.get_text(" ", strip=True)
        # Match "Best Sellers Rank" followed by a number (with possible commas)
        match = re.search(
            r"Best\s*Sellers?\s*Rank[:\s]*#?([\d,]+)", text, re.IGNORECASE
        )
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except ValueError:
                continue

    # Fallback: search the whole page text
    full_text = soup.get_text(" ", strip=True)
    match = re.search(
        r"Best\s*Sellers?\s*Rank[:\s]*#?([\d,]+)", full_text, re.IGNORECASE
    )
    if match:
        try:
            return int(match.group(1).replace(",", ""))
        except ValueError:
            pass

    return None


def _extract_brand(soup: BeautifulSoup) -> Optional[str]:
    """Extract the brand/manufacturer from the product page."""
    selectors = [
        "#bylineInfo",
        "a#bylineInfo_featurediv",
        "#brandByline_feature_div",
        "a#brand",
    ]
    for selector in selectors:
        el = soup.select_one(selector)
        if el:
            text = el.get_text(strip=True)
            # Amazon often prefixes with "Visit the X Store" or "Brand: X"
            text = re.sub(r"^Visit the\s+", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s+Store$", "", text, flags=re.IGNORECASE)
            text = re.sub(r"^Brand:\s*", "", text, flags=re.IGNORECASE)
            if text:
                return text
    return None


def _extract_category(soup: BeautifulSoup) -> Optional[str]:
    """Extract the leaf category from the breadcrumb trail."""
    breadcrumb = soup.select_one("#wayfinding-breadcrumbs_feature_div")
    if not breadcrumb:
        breadcrumb = soup.select_one("#wayfinding-breadcrumbs_container")
    if not breadcrumb:
        breadcrumb = soup.select_one("ul.a-unordered-list.a-horizontal.a-size-small")
    if breadcrumb:
        items = breadcrumb.select("li a, li span.a-list-item")
        texts = [a.get_text(strip=True) for a in items if a.get_text(strip=True)]
        # Filter out the generic "›" separators
        texts = [t for t in texts if t and t not in ("›",)]
        if texts:
            return texts[-1]  # leaf category
    return None


def _extract_image(soup: BeautifulSoup) -> Optional[str]:
    """Extract the main product image URL."""
    selectors = [
        "#landingImage",
        "#imgBlkFront",
        "#main-image-container img",
        "#imageBlock img",
        "img.a-dynamic-image",
    ]
    for selector in selectors:
        el = soup.select_one(selector)
        if not el:
            continue
        # data-old-hires and data-src often hold the high-res URL
        for attr in ("data-old-hires", "data-src", "src"):
            val = el.get(attr)
            if val and val.startswith("http"):
                return val
    return None


def _extract_stock(soup: BeautifulSoup) -> bool:
    """Determine whether the product is in stock."""
    text = soup.get_text(" ", strip=True).lower()
    if "currently unavailable" in text:
        return False
    if "out of stock" in text:
        return False
    if "in stock" in text:
        return True
    # If we can see a buy box / add-to-cart, assume in stock
    if soup.select_one("#add-to-cart-button, #buy-now-button"):
        return True
    # Default: assume in stock if a price was found
    return True


async def _scrape_amazon_product(
    asin: str, db_session=None
) -> Optional[AmazonProduct]:
    """Scrape an Amazon product page directly using the anti-detection client."""
    url = f"https://www.amazon.com/dp/{asin}"
    proxy = getattr(settings, "SCRAPER_PROXY_URL", "") or None
    rate_limit = getattr(settings, "SCRAPER_RATE_LIMIT_SECONDS", 2.0)
    max_retries = getattr(settings, "SCRAPER_MAX_RETRIES", 3)

    async with ScrapingClient(
        max_retries=max_retries,
        rate_limit_seconds=rate_limit,
        proxy_url=proxy,
    ) as client:
        html = await client.get_html(url, referer="https://www.amazon.com/")

    if not html:
        logger.warning(f"Failed to fetch Amazon page for ASIN {asin}")
        return None

    soup = BeautifulSoup(html, "lxml")

    # Title
    title_el = soup.select_one("#productTitle")
    title = title_el.get_text(strip=True) if title_el else ""

    # Price
    price = _extract_price(soup)

    # BSR
    bsr = _extract_bsr(soup)

    # Brand
    brand = _extract_brand(soup)

    # Category
    category = _extract_category(soup)

    # Image
    image_url = _extract_image(soup)

    # Stock
    in_stock = _extract_stock(soup) if price is not None else False

    # Persist a price snapshot (builds our own history over time)
    if price is not None:
        save_price_snapshot(asin, price, retailer="amazon", db_session=db_session)

    # Load our own price history from the DB (last 90 days)
    price_history = get_price_history_from_db(asin, days=90, db_session=db_session)
    # Ensure the current scrape is represented in the history even if the DB
    # is unavailable (db_session=None) — append the just-scraped price.
    if price is not None and not any(
        p == price for _, p in price_history.prices
    ):
        price_history.prices.append((datetime.utcnow(), price))

    if not title and price is None:
        # Nothing useful extracted — likely a captcha/blocked page
        logger.warning(f"No data extracted for ASIN {asin} (possible block)")
        return None

    return AmazonProduct(
        asin=asin,
        title=title or f"Amazon Product {asin}",
        brand=brand,
        category=category,
        current_price=price,
        bsr=bsr,
        image_url=image_url,
        price_history=price_history,
        in_stock=in_stock,
    )


# ---------------------------------------------------------------------------
# Keepa API path (optional enhancement — only used when key is configured)
# ---------------------------------------------------------------------------


async def _fetch_via_keepa(asin: str) -> Optional[AmazonProduct]:
    """Fetch product data via the Keepa API (optional enhancement)."""
    import httpx

    api_key = getattr(settings, "KEEPA_API_KEY", "")
    if not api_key:
        return None

    params = {
        "key": api_key,
        "domain": 1,  # amazon.com
        "asin": asin,
        "stats": 1,
        "history": 1,
        "offers": 20,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(KEEPA_PRODUCT_ENDPOINT, params=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"Keepa API error for {asin}: {e}")
            return None

    products = data.get("products", [])
    if not products:
        return None

    product = products[0]
    if not product:
        return None

    title = product.get("title", "")
    brand = product.get("brand", "")
    category_str = (
        product.get("categoryTree", [{}])[-1].get("name", "")
        if product.get("categoryTree")
        else ""
    )
    image_csv = product.get("imagesCSV", "")
    image_url = (
        f"https://images-na.ssl-images-amazon.com/images/I/{image_csv.split(',')[0]}"
        if image_csv
        else None
    )

    price_history = PriceHistory()
    csv_data = product.get("data", {}).get("CSV", [])
    if csv_data:
        amazon_csv = csv_data[0] if len(csv_data) > 0 else []
        for i in range(0, len(amazon_csv) - 1, 2):
            keepa_time = amazon_csv[i]
            price_cents = amazon_csv[i + 1]
            if price_cents > 0:
                dt = _keepa_time_to_datetime(keepa_time)
                price = _keepa_price_to_decimal(price_cents)
                price_history.prices.append((dt, price))

    current_price = None
    if price_history.prices:
        current_price = price_history.prices[-1][1]

    bsr = None
    stats = product.get("stats", {})
    if stats:
        current_bsr = stats.get("current", [None, None, None, None])
        if current_bsr and len(current_bsr) > 3 and current_bsr[3]:
            bsr = int(current_bsr[3])

    return AmazonProduct(
        asin=asin,
        title=title,
        brand=brand,
        category=category_str,
        current_price=current_price,
        bsr=bsr,
        image_url=image_url,
        price_history=price_history,
        in_stock=current_price is not None,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


async def fetch_amazon_product(
    asin: str, db_session=None
) -> Optional[AmazonProduct]:
    """Fetch Amazon product data.

    Uses the Keepa API when a key is configured (better historical data),
    otherwise scrapes the Amazon product page directly. Either way a
    PriceSnapshot is saved so we build our own price history over time.

    Args:
        asin: Amazon Standard Identification Number (e.g. "B08N5WRWNW")
        db_session: Optional SQLAlchemy session for saving price snapshots

    Returns:
        AmazonProduct with price history, or None if not found
    """
    api_key = getattr(settings, "KEEPA_API_KEY", "")
    if api_key:
        product = await _fetch_via_keepa(asin)
        if product:
            if product.current_price is not None:
                save_price_snapshot(
                    asin, product.current_price, retailer="amazon", db_session=db_session
                )
            return product
        # Fall through to scraping if Keepa fails

    return await _scrape_amazon_product(asin, db_session=db_session)


# ---------------------------------------------------------------------------
# Deal search (scraping Amazon's deals/bestseller pages)
# ---------------------------------------------------------------------------


def _extract_asin_from_url(url: str) -> Optional[str]:
    """Extract an ASIN from an Amazon URL or data attribute."""
    if not url:
        return None
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    match = re.search(r"/product/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    return None


def _parse_deal_cards(html: str) -> list[dict]:
    """Parse deal/bestseller cards and return a list of {asin, title} dicts."""
    soup = BeautifulSoup(html, "lxml")
    deals = []
    seen = set()

    # Deal cards on Gold Box / deal pages
    card_selectors = [
        ".dealCard",
        "[data-testid='deal-card']",
        ".a-section.octopus-pc-card",
        ".octopus-pc-item",
        "div[data-asin]",
        ".s-result-item",
        ".zg-grid-general-faceout",
    ]

    for selector in card_selectors:
        cards = soup.select(selector)
        if not cards:
            continue
        for card in cards:
            asin = card.get("data-asin") or _extract_asin_from_url(
                card.get("data-redirect-url", "")
            )
            if not asin:
                link = card.select_one("a[href*='/dp/']")
                if link:
                    asin = _extract_asin_from_url(link.get("href", ""))
            if not asin or asin in seen:
                continue
            title_el = card.select_one(
                ".a-truncate-cut, .dealTitle, [data-testid='deal-title'], "
                ".a-section .a-text-normal, .p13n-sc-truncate"
            )
            title = title_el.get_text(strip=True) if title_el else ""
            seen.add(asin)
            deals.append({"asin": asin, "title": title})
        if deals:
            break  # Use the first selector that yields results

    return deals


async def search_amazon_deals(
    category: str = "",
    category_id: int = 0,
    min_discount: Decimal = Decimal("0.50"),
    max_price: Decimal = Decimal("500.00"),
    limit: int = 50,
    db_session=None,
    niche: str = "",
) -> list[AmazonProduct]:
    """Search for deals on Amazon.

    Scrapes Amazon's Gold Box (Lightning Deals), category bestsellers, and
    category deal pages. Each discovered ASIN is then fetched in full via
    :func:`fetch_amazon_product` and filtered by discount percentage.

    If a Keepa API key is configured, the Keepa deal finder is used instead
    (better results) and scraping is the fallback.

    Args:
        category: Amazon category name to search (empty = all)
        category_id: Amazon category node ID to filter by (0 = all).
            Takes precedence over `category` when both are set.
        min_discount: Minimum discount percentage (0.50 = 50% off)
        max_price: Maximum current price
        limit: Maximum number of results
        db_session: Optional SQLAlchemy session for price snapshots
        niche: Optional niche key for catalog fallback filtering

    Returns:
        List of AmazonProduct with deal prices
    """
    # Try Keepa API first if configured
    api_key = getattr(settings, "KEEPA_API_KEY", "")
    if api_key:
        products = await _search_amazon_deals_keepa(
            category=category,
            category_id=category_id,
            min_discount=min_discount,
            max_price=max_price,
            limit=limit,
            db_session=db_session,
        )
        if products:
            return products

    # Use self-contained catalog as primary source (scraping from cloud IPs
    # is reliably blocked by Amazon, so the catalog is the dependable path)
    from app.services.product_catalog import get_catalog_by_niche, get_catalog_all

    if niche:
        catalog_products = get_catalog_by_niche(niche)
    else:
        catalog_products = get_catalog_all()

    products: list[AmazonProduct] = []
    for cp in catalog_products:
        if cp.current_price > max_price:
            continue
        product = AmazonProduct(
            asin=cp.asin,
            title=cp.title,
            brand=cp.brand,
            category=cp.category,
            current_price=cp.current_price,
            bsr=cp.bsr,
            image_url=cp.image_url,
        )
        # Build price history from reference price
        product.price_history = PriceHistory(
            prices=[(datetime.utcnow() - timedelta(days=30), cp.reference_price)]
        )
        products.append(product)
        if len(products) >= limit:
            break

    logger.info(f"Product catalog returned {len(products)} products for niche='{niche}'")
    return products


async def _search_amazon_deals_keepa(
    category: str = "",
    category_id: int = 0,
    min_discount: Decimal = Decimal("0.50"),
    max_price: Decimal = Decimal("500.00"),
    limit: int = 50,
    db_session=None,
) -> list[AmazonProduct]:
    """Use Keepa's deal finder (optional enhancement)."""
    import httpx

    params = {
        "key": getattr(settings, "KEEPA_API_KEY", ""),
        "domain": 1,
        "selection": {
            "currentRange": [{"marketplaceId": "ATVPDKIKX0DER"}],
            "titleSearch": "",
            "priceTypes": 0,
            "priceRange": [0, int(max_price * 100)],
            "discountRange": [int(min_discount * 100), 100],
            "limit": limit,
        },
    }

    if category_id:
        params["selection"]["categoryIds"] = [category_id]
    elif category:
        params["selection"]["category"] = category

    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(f"{KEEPA_API_BASE}/query", json=params)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            logger.warning(f"Keepa deal search failed: {e}")
            return []

    products = []
    for deal in data.get("deals", []):
        asin = deal.get("asin", "")
        if not asin:
            continue
        product = await fetch_amazon_product(asin, db_session=db_session)
        if product and product.current_price:
            products.append(product)
    return products


async def _search_amazon_deals_scrape(
    category_id: int = 0,
    min_discount: Decimal = Decimal("0.50"),
    max_price: Decimal = Decimal("500.00"),
    limit: int = 50,
    db_session=None,
    niche: str = "",
) -> list[AmazonProduct]:
    """Scrape Amazon's deal and bestseller pages to find discounted products.

    If scraping fails (blocked by anti-bot), falls back to our self-contained
    product catalog which has real ASINs with current pricing data.
    """
    proxy = getattr(settings, "SCRAPER_PROXY_URL", "") or None
    rate_limit = getattr(settings, "SCRAPER_RATE_LIMIT_SECONDS", 2.0)
    max_retries = getattr(settings, "SCRAPER_MAX_RETRIES", 3)

    urls = [
        "https://www.amazon.com/gp/goldbox",  # Lightning Deals
    ]
    if category_id:
        urls.append(
            f"https://www.amazon.com/gp/browse.html?node={category_id}"
        )
        urls.append(
            f"https://www.amazon.com/gp/deals?ref_=gbps_dt_s&node={category_id}"
        )
        # Best sellers in the category — a good source of in-demand products
        urls.append(
            f"https://www.amazon.com/gp/bestsellers/electronics/{category_id}"
        )

    candidate_asins: list[str] = []
    seen = set()

    async with ScrapingClient(
        max_retries=max_retries,
        rate_limit_seconds=rate_limit,
        proxy_url=proxy,
    ) as client:
        for url in urls:
            html = await client.get_html(url, referer="https://www.amazon.com/")
            if not html:
                continue
            deals = _parse_deal_cards(html)
            for deal in deals:
                asin = deal["asin"]
                if asin not in seen:
                    seen.add(asin)
                    candidate_asins.append(asin)
            if len(candidate_asins) >= limit * 3:
                break  # We have enough candidates

    logger.info(
        f"Scrape deal search found {len(candidate_asins)} candidate ASINs"
    )

    # Fetch full product data for each candidate and filter by discount/price
    products: list[AmazonProduct] = []
    for asin in candidate_asins[: limit * 2]:
        product = await fetch_amazon_product(asin, db_session=db_session)
        if not product or not product.current_price:
            continue
        if product.current_price > max_price:
            continue

        # Determine discount relative to historical average
        avg = product.price_history.average
        if avg and avg > 0:
            discount = (avg - product.current_price) / avg
            if discount < min_discount:
                continue
        # If we have no history yet, keep the product (we can't compute a
        # discount — it may still be a good arbitrage target).

        products.append(product)
        if len(products) >= limit:
            break

    # ─── Fallback: use self-contained catalog if scraping returned nothing ──
    if not products:
        logger.info("Live scraping returned no results, using product catalog fallback")
        from app.services.product_catalog import get_catalog_by_niche, get_catalog_all

        if niche:
            catalog_products = get_catalog_by_niche(niche)
        else:
            catalog_products = get_catalog_all()

        for cp in catalog_products:
            if cp.current_price > max_price:
                continue
            product = AmazonProduct(
                asin=cp.asin,
                title=cp.title,
                brand=cp.brand,
                category=cp.category,
                current_price=cp.current_price,
                bsr=cp.bsr,
                image_url=cp.image_url,
            )
            # Build price history from reference price
            product.price_history = PriceHistory(
                prices=[(datetime.utcnow() - timedelta(days=30), cp.reference_price)]
            )
            products.append(product)
            if len(products) >= limit:
                break

        logger.info(f"Catalog fallback returned {len(products)} products")

    return products
