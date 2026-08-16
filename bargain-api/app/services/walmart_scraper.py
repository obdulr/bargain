"""Walmart Scraper — requires an unblocking proxy to function at all.

Unlike Amazon (which serves normal HTML to cloud IPs, just with occasional
soft blocks/captchas), Walmart drops connections from datacenter/cloud IP
ranges outright. Verified: direct requests to walmart.com from Render-class
cloud IPs get 0 bytes back (connection refused/timeout), not even a 403.

Because of that, this module is a no-op (returns empty results, logs why)
unless ``SCRAPER_PROXY_URL`` is configured with a residential/unblocking
proxy (e.g. ScraperAPI, Zyte API, Bright Data). It never pretends to have
live data it doesn't have.

Walmart's product pages are Next.js-rendered and embed all product data as
JSON in a ``<script id="__NEXT_DATA__">`` tag, so once a page actually loads
we parse that JSON directly instead of relying on CSS selectors that change
frequently.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime, timedelta
from typing import Optional
import json
import logging
import re

from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.scraper import _parse_price
from app.services.deal_criteria import PriceHistory
from app.services.affiliate_service import add_affiliate_tag
from app.services.http_client import ScrapingClient

logger = logging.getLogger(__name__)

WALMART_BASE_URL = "https://www.walmart.com"
# Walmart's deals/clearance hub — item cards are embedded in __NEXT_DATA__.
WALMART_DEALS_URL = "https://www.walmart.com/shop/deals"


@dataclass
class WalmartProduct:
    """Walmart product data."""
    item_id: str
    title: str
    brand: Optional[str] = None
    category: Optional[str] = None
    current_price: Optional[Decimal] = None
    original_price: Optional[Decimal] = None
    image_url: Optional[str] = None
    url: str = ""
    price_history: PriceHistory = field(default_factory=PriceHistory)
    in_stock: bool = True

    def __post_init__(self):
        if not self.url:
            self.url = add_affiliate_tag(
                f"{WALMART_BASE_URL}/ip/{self.item_id}", "walmart"
            )


def _has_proxy_configured() -> bool:
    return bool(getattr(settings, "SCRAPER_PROXY_URL", ""))


def save_price_snapshot(
    item_id: str,
    price: Decimal,
    retailer: str = "walmart",
    db_session=None,
) -> None:
    """Save a price snapshot to the database (same pattern as the Amazon scraper)."""
    if db_session is None or price is None:
        return
    try:
        from app.db.models import PriceSnapshot

        snapshot = PriceSnapshot(
            item_id=item_id,
            retailer=retailer,
            price=price,
            currency="USD",
        )
        db_session.add(snapshot)
        db_session.commit()
    except Exception as e:
        logger.warning(f"Failed to save price snapshot for Walmart item {item_id}: {e}")
        try:
            db_session.rollback()
        except Exception:
            pass


def get_price_history_from_db(item_id: str, days: int = 90, db_session=None) -> PriceHistory:
    """Load our own accumulated price history for a Walmart item."""
    history = PriceHistory()
    if db_session is None:
        return history
    try:
        from app.db.models import PriceSnapshot

        cutoff = datetime.utcnow() - timedelta(days=days)
        rows = (
            db_session.query(PriceSnapshot)
            .filter(
                PriceSnapshot.item_id == item_id,
                PriceSnapshot.retailer == "walmart",
                PriceSnapshot.timestamp >= cutoff,
            )
            .order_by(PriceSnapshot.timestamp.asc())
            .all()
        )
        for row in rows:
            if row.price is not None:
                history.prices.append((row.timestamp, Decimal(str(row.price))))
    except Exception as e:
        logger.warning(f"Failed to load price history for Walmart item {item_id}: {e}")

    return history


def _extract_next_data(html: str) -> Optional[dict]:
    """Extract and parse Walmart's ``__NEXT_DATA__`` JSON blob from a page."""
    soup = BeautifulSoup(html, "lxml")
    script = soup.select_one("script#__NEXT_DATA__")
    if not script or not script.string:
        return None
    try:
        return json.loads(script.string)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse Walmart __NEXT_DATA__ JSON")
        return None


def _find_key_recursive(obj, target_keys: set, max_depth: int = 12) -> Optional[dict]:
    """Depth-first search for the first dict containing any of ``target_keys``.

    Walmart's Next.js data tree is deeply nested and its shape shifts between
    page templates, so we search for recognizable product fields rather than
    hardcoding a fixed path.
    """
    if max_depth <= 0:
        return None
    if isinstance(obj, dict):
        if target_keys & obj.keys():
            return obj
        for value in obj.values():
            found = _find_key_recursive(value, target_keys, max_depth - 1)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_key_recursive(item, target_keys, max_depth - 1)
            if found is not None:
                return found
    return None


def _parse_product_from_next_data(data: dict, item_id: str) -> Optional[WalmartProduct]:
    """Extract product fields from Walmart's __NEXT_DATA__ tree for a PDP."""
    node = _find_key_recursive(data, {"priceInfo", "name"})
    if not node:
        return None

    title = node.get("name") or ""

    price = None
    original_price = None
    price_info = node.get("priceInfo") or {}
    current = price_info.get("currentPrice") or {}
    was = price_info.get("wasPrice") or {}
    if isinstance(current, dict) and current.get("price") is not None:
        price = Decimal(str(current["price"]))
    if isinstance(was, dict) and was.get("price") is not None:
        original_price = Decimal(str(was["price"]))

    brand = node.get("brand")

    image_url = None
    image_info = node.get("imageInfo") or {}
    if isinstance(image_info, dict):
        image_url = image_info.get("thumbnailUrl") or image_info.get("allImages", [{}])[0].get("url") if image_info.get("allImages") else image_info.get("thumbnailUrl")

    availability = node.get("availabilityStatus") or ""
    in_stock = availability.upper() != "OUT_OF_STOCK" if availability else True

    category = None
    category_path = node.get("category") or {}
    if isinstance(category_path, dict):
        path = category_path.get("path") or []
        if path:
            category = path[-1].get("name") if isinstance(path[-1], dict) else None

    if not title and price is None:
        return None

    return WalmartProduct(
        item_id=item_id,
        title=title or f"Walmart Item {item_id}",
        brand=brand,
        category=category,
        current_price=price,
        original_price=original_price,
        image_url=image_url,
        in_stock=in_stock,
    )


async def fetch_walmart_product(item_id: str, db_session=None) -> Optional[WalmartProduct]:
    """Fetch a single Walmart product's current price and details.

    Requires ``SCRAPER_PROXY_URL`` to be configured — see module docstring.
    Returns None immediately (no request attempted) if no proxy is set, so
    callers can distinguish "not configured" from "blocked" via the logs.
    """
    if not _has_proxy_configured():
        logger.info(
            "Walmart scraper skipped (no SCRAPER_PROXY_URL configured — "
            "direct requests to walmart.com from cloud IPs are dropped)"
        )
        return None

    url = f"{WALMART_BASE_URL}/ip/{item_id}"
    proxy = settings.SCRAPER_PROXY_URL
    rate_limit = getattr(settings, "SCRAPER_RATE_LIMIT_SECONDS", 2.0)
    max_retries = getattr(settings, "SCRAPER_MAX_RETRIES", 3)

    async with ScrapingClient(
        max_retries=max_retries,
        rate_limit_seconds=rate_limit,
        proxy_url=proxy,
    ) as client:
        html = await client.get_html(url, referer=WALMART_BASE_URL)

    if not html:
        logger.warning(f"Failed to fetch Walmart page for item {item_id}")
        return None

    next_data = _extract_next_data(html)
    if not next_data:
        logger.warning(f"No __NEXT_DATA__ found for Walmart item {item_id} (possible block/redesign)")
        return None

    product = _parse_product_from_next_data(next_data, item_id)
    if not product:
        logger.warning(f"No product data extracted for Walmart item {item_id}")
        return None

    if product.current_price is not None:
        save_price_snapshot(item_id, product.current_price, retailer="walmart", db_session=db_session)

    product.price_history = get_price_history_from_db(item_id, days=90, db_session=db_session)
    if product.current_price is not None and not any(
        p == product.current_price for _, p in product.price_history.prices
    ):
        product.price_history.prices.append((datetime.utcnow(), product.current_price))

    return product


def _extract_item_id_from_url(url: str) -> Optional[str]:
    """Extract a Walmart item ID from a product URL (last numeric path segment)."""
    if not url:
        return None
    match = re.search(r"/ip/(?:[^/]+/)?(\d+)", url)
    return match.group(1) if match else None


async def search_walmart_deals(
    max_deals: int = 50,
    min_discount: int = 15,
    db_session=None,
) -> list[WalmartProduct]:
    """Scrape Walmart's deals hub for discounted, in-stock products.

    Requires ``SCRAPER_PROXY_URL``. Returns an empty list (not an error) when
    no proxy is configured or the fetch fails, matching the rest of the
    scraper stack's graceful-degradation pattern.
    """
    if not _has_proxy_configured():
        logger.info("Walmart deal search skipped (no SCRAPER_PROXY_URL configured)")
        return []

    proxy = settings.SCRAPER_PROXY_URL
    rate_limit = getattr(settings, "SCRAPER_RATE_LIMIT_SECONDS", 2.0)
    max_retries = getattr(settings, "SCRAPER_MAX_RETRIES", 3)

    async with ScrapingClient(
        max_retries=max_retries,
        rate_limit_seconds=rate_limit,
        proxy_url=proxy,
    ) as client:
        html = await client.get_html(WALMART_DEALS_URL, referer=WALMART_BASE_URL)

    if not html:
        logger.warning("Failed to fetch Walmart deals page")
        return []

    next_data = _extract_next_data(html)
    if not next_data:
        logger.warning("No __NEXT_DATA__ found on Walmart deals page (possible block/redesign)")
        return []

    # The deals hub lists many item "tiles" rather than a single product node.
    # Search for the first list of dicts that look like product tiles.
    items_node = _find_key_recursive(next_data, {"itemStacks"})
    tiles = []
    if items_node:
        for stack in items_node.get("itemStacks", []):
            tiles.extend(stack.get("items", []))
    else:
        # Fallback: some templates expose a flat "items" list directly.
        items_node = _find_key_recursive(next_data, {"items"})
        if items_node:
            tiles = items_node.get("items", [])

    products: list[WalmartProduct] = []
    for tile in tiles:
        if not isinstance(tile, dict):
            continue
        item_id = str(tile.get("usItemId") or tile.get("id") or tile.get("itemId") or "")
        if not item_id:
            continue

        price_info = tile.get("priceInfo") or {}
        current = price_info.get("currentPrice") or {}
        was = price_info.get("wasPrice") or {}
        price = Decimal(str(current["price"])) if isinstance(current, dict) and current.get("price") is not None else None
        original_price = Decimal(str(was["price"])) if isinstance(was, dict) and was.get("price") is not None else None

        if price is None:
            continue
        if original_price and original_price > price:
            discount = int(round((1 - float(price) / float(original_price)) * 100))
            if discount < min_discount:
                continue

        image_url = tile.get("imageInfo", {}).get("thumbnailUrl") if isinstance(tile.get("imageInfo"), dict) else None

        product = WalmartProduct(
            item_id=item_id,
            title=(tile.get("name") or f"Walmart Item {item_id}")[:500],
            brand=tile.get("brand"),
            current_price=price,
            original_price=original_price,
            image_url=image_url,
        )
        if price is not None:
            save_price_snapshot(item_id, price, retailer="walmart", db_session=db_session)
        products.append(product)
        if len(products) >= max_deals:
            break

    logger.info(f"Walmart deals: {len(products)} discounted in-stock products found")
    return products


def save_walmart_deals_to_database(products: list[WalmartProduct], db_session) -> int:
    """Save scraped Walmart deals to the ArbitrageDeal table.

    Mirrors ``amazon_deals_scraper.save_deals_to_database`` — the ``asin``
    column is reused as a generic per-source item key (prefixed to avoid
    colliding with real Amazon ASINs or Impact.com deal IDs).
    """
    from app.db.models import ArbitrageDeal
    from app.services.deal_scorer import calculate_deal_score

    saved = 0
    for product in products:
        deal_key = f"walmart_{product.item_id}"[:36]
        try:
            existing = (
                db_session.query(ArbitrageDeal)
                .filter(
                    ArbitrageDeal.asin == deal_key,
                    ArbitrageDeal.status == "active",
                )
                .first()
            )
            sell_price = product.original_price or product.current_price
            net_profit = (
                product.original_price - product.current_price
                if product.original_price
                else Decimal("0")
            )
            roi = (
                float(net_profit / product.original_price)
                if product.original_price and product.original_price > 0
                else 0
            )
            tier = "clearance"
            if product.original_price and product.current_price:
                discount = (product.original_price - product.current_price) / product.original_price
                if discount >= Decimal("0.70"):
                    tier = "glitch"

            if existing:
                existing.buy_price = product.current_price
                existing.sell_price = sell_price
                existing.historical_avg = product.original_price
                existing.title = product.title
                existing.image_url = product.image_url
                existing.buy_url = product.url
                existing.detected_at = datetime.utcnow()
                existing.deal_tier = tier
                existing.is_profitable = True
                existing.net_profit = net_profit
                existing.roi = roi
                existing.score = calculate_deal_score(existing)
                db_session.commit()
                saved += 1
                continue

            new_deal = ArbitrageDeal(
                asin=deal_key,
                title=product.title,
                image_url=product.image_url,
                buy_url=product.url,
                buy_platform="walmart",
                retailer="walmart",
                deal_source="in_store",
                buy_price=product.current_price,
                sell_platform="walmart",
                sell_price=sell_price,
                historical_avg=product.original_price,
                deal_tier=tier,
                net_profit=net_profit,
                roi=roi,
                is_profitable=True,
                status="active",
                detected_at=datetime.utcnow(),
                category=product.category,
            )
            db_session.add(new_deal)
            new_deal.score = calculate_deal_score(new_deal)
            db_session.commit()
            saved += 1

        except Exception as e:
            logger.warning(f"Failed to save Walmart deal for item {product.item_id}: {e}")
            db_session.rollback()

    logger.info(f"Saved {saved} Walmart deals to database")
    return saved
