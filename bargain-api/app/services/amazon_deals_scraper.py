"""Amazon Today's Deals Scraper.

Scrapes Amazon's Gold Box / Today's Deals page to find real, currently-active
discounted products. These are genuine deals that Amazon is promoting — not
manually curated or fabricated data.

Extracts:
- ASIN, title, image URL
- Deal price (current sale price)
- Original/list price (struck-through price)
- Discount percentage
- Deal type (lightning deal, deal of the day, etc.)

Stores deals in the ArbitrageDeal table with deal_tier="clearance" so they
appear on the homepage deals feed.
"""
import asyncio
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Optional
from urllib.parse import urljoin, urlparse, parse_qs

from bs4 import BeautifulSoup

from app.core.config import settings
from app.services.http_client import ScrapingClient
from app.services.affiliate_service import add_affiliate_tag
from app.services.scraper import _parse_price

logger = logging.getLogger(__name__)

# Amazon Today's Deals URLs
GOLD_BOX_URL = "https://www.amazon.com/gp/goldbox"
DEALS_PAGE_URL = "https://www.amazon.com/deals"

# Amazon trending products URLs
MOVERS_SHAKERS_URL = "https://www.amazon.com/gp/movers-and-shakers"
HOT_NEW_RELEASES_URL = "https://www.amazon.com/gp/new-releases"


@dataclass
class AmazonDeal:
    """A real deal found on Amazon's Today's Deals page."""
    asin: str
    title: str
    deal_price: Decimal
    original_price: Optional[Decimal] = None
    discount_percent: Optional[int] = None
    image_url: Optional[str] = None
    url: str = ""
    deal_type: str = "deal"
    category: Optional[str] = None
    is_prime: bool = False

    def __post_init__(self):
        if not self.url:
            self.url = add_affiliate_tag(
                f"https://www.amazon.com/dp/{self.asin}", "amazon", self.asin
            )


def _extract_asin_from_url(url: str) -> Optional[str]:
    """Extract ASIN from an Amazon URL."""
    if not url:
        return None
    match = re.search(r"/dp/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    match = re.search(r"/product/([A-Z0-9]{10})", url)
    if match:
        return match.group(1)
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    if "asin" in params:
        return params["asin"][0]
    return None


def _parse_deal_cards(html: str) -> list[AmazonDeal]:
    """Parse deal cards from the Gold Box / Today's Deals page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    deals: list[AmazonDeal] = []

    # Amazon's Gold Box page has /dp/ links inside containers with prices.
    for link in soup.find_all("a", href=re.compile(r"/dp/[A-Z0-9]{10}")):
        try:
            deal = _parse_deal_from_link(link)
            if deal:
                deals.append(deal)
        except Exception as e:
            logger.debug(f"Failed to parse deal from link: {e}")
            continue

    # Deduplicate by ASIN (keep highest discount)
    seen: dict[str, AmazonDeal] = {}
    for deal in deals:
        if deal.asin not in seen:
            seen[deal.asin] = deal
        elif (deal.discount_percent or 0) > (seen[deal.asin].discount_percent or 0):
            seen[deal.asin] = deal

    return list(seen.values())


def _parse_deal_from_link(link) -> Optional[AmazonDeal]:
    """Parse a deal from an anchor tag that links to a /dp/ product page."""
    href = link.get("href", "")
    asin = _extract_asin_from_url(href)
    if not asin:
        return None

    title = link.get_text(strip=True)
    if not title or len(title) < 5:
        return None

    # Clean title — Amazon sometimes appends deal metadata to the link text
    # e.g. "Product Name37% offLimited time deal$335.98$33598List:$529.99"
    # We cut at the first occurrence of "% off" or "Limited time" or a price
    title = re.split(r'\s*\d+%?\s*off', title)[0]
    title = re.split(r'Limited time deal', title, flags=re.IGNORECASE)[0]
    title = re.split(r'List:\$', title)[0]
    title = re.split(r'Typical:\$', title)[0]
    title = title.strip()
    if not title or len(title) < 5:
        return None

    # Walk up to find the container with prices (usually 2-3 levels up)
    container = link.parent
    for _ in range(4):
        if container is None:
            break
        prices = container.select(".a-price .a-offscreen")
        if len(prices) >= 2:
            break
        container = container.parent

    if container is None:
        container = link.parent

    # Extract prices
    deal_price = None
    original_price = None

    price_els = container.select(".a-price .a-offscreen")
    for el in price_els:
        text = el.get_text(strip=True)
        price = _parse_price(text)
        if price and price > 0:
            if deal_price is None:
                deal_price = price
            elif original_price is None and price > deal_price:
                original_price = price

    # Look for struck-through (original) price
    strike_el = container.select_one(
        '[data-a-strike="true"] .a-offscreen, '
        '.a-text-price.a-text-strike .a-offscreen'
    )
    if strike_el:
        text = strike_el.get_text(strip=True)
        price = _parse_price(text)
        if price and price > 0:
            original_price = price

    if not deal_price:
        return None

    # If we only found one price, try siblings
    if not original_price:
        for el in container.select(".a-offscreen, .a-color-secondary"):
            text = el.get_text(strip=True)
            price = _parse_price(text)
            if price and price > deal_price:
                original_price = price
                break

    # Discount percentage
    discount_percent = None
    if original_price and original_price > deal_price:
        discount_percent = int(round((1 - deal_price / original_price) * 100))

    # Image
    image_url = None
    img = container.select_one("img")
    if img:
        image_url = img.get("src") or img.get("data-src") or ""
        if image_url and not image_url.startswith("http"):
            image_url = urljoin("https://www.amazon.com", image_url)

    # Deal type
    deal_type = "deal"
    container_text = container.get_text(" ", strip=True).lower()
    if "lightning" in container_text:
        deal_type = "lightning"
    elif "deal of the day" in container_text:
        deal_type = "deal_of_day"
    elif "coupon" in container_text:
        deal_type = "coupon"

    is_prime = "prime" in container_text

    return AmazonDeal(
        asin=asin,
        title=title[:500],
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        image_url=image_url,
        deal_type=deal_type,
        is_prime=is_prime,
    )


async def fetch_amazon_image_for_asin(asin: str, client: ScrapingClient) -> Optional[str]:
    """Fetch the product image URL from an Amazon product page.

    Uses a longer delay between requests to avoid rate limiting.
    Returns the image URL or None if the page couldn't be fetched.
    """
    url = f"https://www.amazon.com/dp/{asin}"
    html = await client.get_html(url, referer="https://www.amazon.com")
    if not html:
        return None

    soup = BeautifulSoup(html, "html.parser")

    # Try og:image meta tag (most reliable)
    og = soup.select_one('meta[property="og:image"]')
    if og:
        content = og.get("content", "")
        if content and "media-amazon" in content:
            return content

    # Try main product image selectors
    for selector in [
        "#landingImage",
        "#imgBlkFront",
        "#main-image",
        "img[data-old-hires]",
        "#imgTagWrapperId img",
    ]:
        img = soup.select_one(selector)
        if img:
            src = img.get("data-old-hires") or img.get("src") or ""
            if src and "media-amazon" in src and "transparent" not in src:
                return src

    return None


async def scrape_amazon_deals(max_deals: int = 50) -> list[AmazonDeal]:
    """Scrape Amazon's Today's Deals page for real active deals."""
    logger.info("Scraping Amazon Today's Deals page...")
    all_deals: list[AmazonDeal] = []

    async with ScrapingClient(rate_limit_seconds=3.0) as client:
        html = await client.get_html(GOLD_BOX_URL, referer="https://www.amazon.com")
        if html:
            deals = _parse_deal_cards(html)
            all_deals.extend(deals)
            logger.info(f"Found {len(deals)} deals on Gold Box page")

        if len(all_deals) < max_deals:
            html = await client.get_html(DEALS_PAGE_URL, referer="https://www.amazon.com")
            if html:
                deals = _parse_deal_cards(html)
                existing_asins = {d.asin for d in all_deals}
                new_deals = [d for d in deals if d.asin not in existing_asins]
                all_deals.extend(new_deals)
                logger.info(f"Found {len(new_deals)} additional deals on /deals page")

    # Sort by discount percentage (highest first)
    # Note: We don't filter by discount here — the API endpoint filters at query time.
    # This lets us keep all deals in the database and adjust the threshold without re-scraping.
    all_deals.sort(key=lambda d: d.discount_percent or 0, reverse=True)
    return all_deals[:max_deals]


async def scrape_gold_box(max_deals: int = 50) -> list[AmazonDeal]:
    """Scrape Amazon's Gold Box page only."""
    logger.info("Scraping Amazon Gold Box page...")
    deals: list[AmazonDeal] = []
    async with ScrapingClient(rate_limit_seconds=3.0) as client:
        html = await client.get_html(GOLD_BOX_URL, referer="https://www.amazon.com")
        if html:
            deals = _parse_deal_cards(html)
            logger.info(f"Found {len(deals)} deals on Gold Box page")
    deals.sort(key=lambda d: d.discount_percent or 0, reverse=True)
    return deals[:max_deals]


async def scrape_todays_deals(max_deals: int = 50) -> list[AmazonDeal]:
    """Scrape Amazon's Today's Deals (/deals) page only."""
    logger.info("Scraping Amazon Today's Deals page...")
    deals: list[AmazonDeal] = []
    async with ScrapingClient(rate_limit_seconds=3.0) as client:
        html = await client.get_html(DEALS_PAGE_URL, referer="https://www.amazon.com")
        if html:
            deals = _parse_deal_cards(html)
            logger.info(f"Found {len(deals)} deals on /deals page")
    deals.sort(key=lambda d: d.discount_percent or 0, reverse=True)
    return deals[:max_deals]


def _parse_trending_cards(html: str, source: str = "trending") -> list[AmazonDeal]:
    """Parse product cards from Movers & Shakers / Hot New Releases pages.

    These pages list trending products with BSR rank, category, price, and
    (sometimes) an original/list price. Products may not always show a
    discount — in that case discount_percent is 0.
    """
    soup = BeautifulSoup(html, "html.parser")
    deals: list[AmazonDeal] = []

    for link in soup.find_all("a", href=re.compile(r"/dp/[A-Z0-9]{10}")):
        try:
            deal = _parse_trending_from_link(link, source)
            if deal:
                deals.append(deal)
        except Exception as e:
            logger.debug(f"Failed to parse trending card from link: {e}")
            continue

    # Deduplicate by ASIN (keep highest discount)
    seen: dict[str, AmazonDeal] = {}
    for deal in deals:
        if deal.asin not in seen:
            seen[deal.asin] = deal
        elif (deal.discount_percent or 0) > (seen[deal.asin].discount_percent or 0):
            seen[deal.asin] = deal

    return list(seen.values())


def _parse_trending_from_link(link, source: str = "trending") -> Optional[AmazonDeal]:
    """Parse a single trending product card from an anchor tag.

    Handles Movers & Shakers and Hot New Releases page structures. Tries to
    extract BSR rank and category from the card text in addition to
    price/title/image.
    """
    href = link.get("href", "")
    asin = _extract_asin_from_url(href)
    if not asin:
        return None

    title = link.get_text(strip=True)
    if not title or len(title) < 5:
        return None

    # Clean title of trailing metadata
    title = re.split(r'Limited time deal', title, flags=re.IGNORECASE)[0]
    title = re.split(r'List:\$', title)[0]
    title = re.split(r'Typical:\$', title)[0]
    title = re.split(r'#\d+', title)[0]
    title = title.strip()
    if not title or len(title) < 5:
        return None

    # Walk up to find the card container with prices/rank
    container = link.parent
    for _ in range(5):
        if container is None:
            break
        if container.select(".a-price .a-offscreen") or container.select_one(".p13n-price"):
            break
        container = container.parent

    if container is None:
        container = link.parent

    container_text = container.get_text(" ", strip=True)
    container_lower = container_text.lower()

    # Extract prices
    deal_price = None
    original_price = None

    price_els = container.select(".a-price .a-offscreen")
    for el in price_els:
        text = el.get_text(strip=True)
        price = _parse_price(text)
        if price and price > 0:
            if deal_price is None:
                deal_price = price
            elif original_price is None and price > deal_price:
                original_price = price

    # Struck-through original price
    strike_el = container.select_one(
        '[data-a-strike="true"] .a-offscreen, '
        '.a-text-price.a-text-strike .a-offscreen'
    )
    if strike_el:
        text = strike_el.get_text(strip=True)
        price = _parse_price(text)
        if price and price > 0:
            original_price = price

    # Fallback: try .p13n-price or .a-color-price
    if not deal_price:
        for sel in [".p13n-price", ".a-color-price"]:
            el = container.select_one(sel)
            if el:
                price = _parse_price(el.get_text(strip=True))
                if price and price > 0:
                    deal_price = price
                    break

    if not deal_price:
        return None

    # Discount percentage (0 if no original price shown)
    discount_percent = 0
    if original_price and original_price > deal_price:
        discount_percent = int(round((1 - deal_price / original_price) * 100))

    # BSR rank — Movers & Shakers shows a rank like "#42 in Electronics"
    bsr = None
    rank_match = re.search(r'#(\d[\d,]*)\s+in\s+([^#\n|]+)', container_text)
    if rank_match:
        try:
            bsr = int(rank_match.group(1).replace(",", ""))
        except ValueError:
            bsr = None

    # Category — from the rank string or a category link in the card
    category = None
    if rank_match:
        category = rank_match.group(2).strip().rstrip(".,;")
        category = re.split(r'\s+(?:See|&gt;|>)', category)[0].strip()
    cat_link = container.select_one("a[href*='bestsellers'], a[href*='new-releases']")
    if not category and cat_link:
        category = cat_link.get_text(strip=True)

    # Image
    image_url = None
    img = container.select_one("img")
    if img:
        image_url = img.get("src") or img.get("data-src") or ""
        if image_url and not image_url.startswith("http"):
            image_url = urljoin("https://www.amazon.com", image_url)

    is_prime = "prime" in container_lower

    return AmazonDeal(
        asin=asin,
        title=title[:500],
        deal_price=deal_price,
        original_price=original_price,
        discount_percent=discount_percent,
        image_url=image_url,
        deal_type=source,
        category=category,
        is_prime=is_prime,
    )


def _extract_category_links(html: str, base_url: str, limit: int = 5) -> list[str]:
    """Extract top category links from a Movers & Shakers / Hot New Releases page.

    These pages have a left-nav or category list with links to per-category
    listings. Returns up to `limit` absolute URLs.
    """
    soup = BeautifulSoup(html, "html.parser")
    links: list[str] = []
    seen_paths: set[str] = set()

    base_path = urlparse(base_url).path
    for a in soup.find_all("a", href=True):
        href = a["href"]
        absolute = urljoin("https://www.amazon.com", href)
        parsed = urlparse(absolute)
        path = parsed.path
        if path.startswith(base_path) and len(path) > len(base_path) + 1:
            if path not in seen_paths:
                seen_paths.add(path)
                links.append(absolute)
        if len(links) >= limit:
            break

    return links


async def scrape_movers_and_shakers(max_deals: int = 50) -> list[AmazonDeal]:
    """Scrape Amazon's Movers & Shakers page for trending products.

    Movers & Shakers features products with the biggest BSR (Best Sellers
    Rank) jumps — i.e. products gaining sales velocity. Returns AmazonDeal
    objects with deal_type="movers_shakers" and discount_percent=0 when no
    original price is shown.
    """
    logger.info("Scraping Amazon Movers & Shakers page...")
    all_deals: list[AmazonDeal] = []

    async with ScrapingClient(rate_limit_seconds=3.0) as client:
        html = await client.get_html(MOVERS_SHAKERS_URL, referer="https://www.amazon.com")
        if not html:
            logger.warning("No HTML returned from Movers & Shakers page")
            return []

        deals = _parse_trending_cards(html, source="movers_shakers")
        all_deals.extend(deals)
        logger.info(f"Found {len(deals)} deals on Movers & Shakers main page")

        # Scrape top category pages if we need more deals
        if len(all_deals) < max_deals:
            category_links = _extract_category_links(html, MOVERS_SHAKERS_URL, limit=5)
            for cat_url in category_links:
                if len(all_deals) >= max_deals:
                    break
                try:
                    cat_html = await client.get_html(cat_url, referer=MOVERS_SHAKERS_URL)
                    if cat_html:
                        cat_deals = _parse_trending_cards(cat_html, source="movers_shakers")
                        existing_asins = {d.asin for d in all_deals}
                        new_deals = [d for d in cat_deals if d.asin not in existing_asins]
                        all_deals.extend(new_deals)
                        logger.info(
                            f"Found {len(new_deals)} deals in Movers & Shakers category: {cat_url}"
                        )
                except Exception as e:
                    logger.debug(f"Failed to scrape Movers & Shakers category {cat_url}: {e}")
                    continue

    logger.info(f"Movers & Shakers: {len(all_deals)} total deals found")
    all_deals.sort(key=lambda d: d.discount_percent or 0, reverse=True)
    return all_deals[:max_deals]


async def scrape_hot_new_releases(max_deals: int = 50) -> list[AmazonDeal]:
    """Scrape Amazon's Hot New Releases page for trending new products.

    Hot New Releases features newly launched products that are gaining
    traction. Returns AmazonDeal objects with deal_type="hot_new_release"
    and discount_percent=0 when no original price is shown.
    """
    logger.info("Scraping Amazon Hot New Releases page...")
    all_deals: list[AmazonDeal] = []

    async with ScrapingClient(rate_limit_seconds=3.0) as client:
        html = await client.get_html(HOT_NEW_RELEASES_URL, referer="https://www.amazon.com")
        if not html:
            logger.warning("No HTML returned from Hot New Releases page")
            return []

        deals = _parse_trending_cards(html, source="hot_new_release")
        all_deals.extend(deals)
        logger.info(f"Found {len(deals)} deals on Hot New Releases main page")

        # Scrape top category pages if we need more deals
        if len(all_deals) < max_deals:
            category_links = _extract_category_links(html, HOT_NEW_RELEASES_URL, limit=5)
            for cat_url in category_links:
                if len(all_deals) >= max_deals:
                    break
                try:
                    cat_html = await client.get_html(cat_url, referer=HOT_NEW_RELEASES_URL)
                    if cat_html:
                        cat_deals = _parse_trending_cards(cat_html, source="hot_new_release")
                        existing_asins = {d.asin for d in all_deals}
                        new_deals = [d for d in cat_deals if d.asin not in existing_asins]
                        all_deals.extend(new_deals)
                        logger.info(
                            f"Found {len(new_deals)} deals in Hot New Releases category: {cat_url}"
                        )
                except Exception as e:
                    logger.debug(f"Failed to scrape Hot New Releases category {cat_url}: {e}")
                    continue

    logger.info(f"Hot New Releases: {len(all_deals)} total deals found")
    all_deals.sort(key=lambda d: d.discount_percent or 0, reverse=True)
    return all_deals[:max_deals]


async def scrape_all_amazon_deals(max_deals_per_source: int = 50) -> list[AmazonDeal]:
    """Scrape all Amazon deal sources: Gold Box, Today's Deals, Movers & Shakers, Hot New Releases.

    Runs all four scrapers concurrently, collects results, and deduplicates
    by ASIN (keeping the entry with the highest discount_percent). Failed
    sources are logged and skipped so one failure doesn't block the others.
    """
    tasks = [
        scrape_gold_box(max_deals=max_deals_per_source),
        scrape_todays_deals(max_deals=max_deals_per_source),
        scrape_movers_and_shakers(max_deals=max_deals_per_source),
        scrape_hot_new_releases(max_deals=max_deals_per_source),
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    all_deals: list[AmazonDeal] = []
    for result in results:
        if isinstance(result, Exception):
            logger.error(f"Scrape failed: {result}")
            continue
        all_deals.extend(result)

    # Deduplicate by ASIN (keep highest discount)
    seen: dict[str, AmazonDeal] = {}
    for deal in all_deals:
        if deal.asin not in seen:
            seen[deal.asin] = deal
        elif (deal.discount_percent or 0) > (seen[deal.asin].discount_percent or 0):
            seen[deal.asin] = deal

    logger.info(
        f"scrape_all_amazon_deals: {len(all_deals)} raw deals, "
        f"{len(seen)} unique after dedup"
    )
    return list(seen.values())


def _deal_tier_for(deal: AmazonDeal) -> str:
    """Determine the deal_tier for a deal based on its type.

    - lightning deals -> "glitch"
    - movers & shakers / hot new releases -> "trending"
    - everything else -> "clearance"
    """
    if deal.deal_type == "lightning":
        return "glitch"
    if deal.deal_type in ("movers_shakers", "hot_new_release"):
        return "trending"
    return "clearance"


def save_deals_to_database(deals: list[AmazonDeal], db_session) -> int:
    """Save scraped deals to the ArbitrageDeal table."""
    from app.db.models import ArbitrageDeal
    from app.services.deal_scorer import calculate_deal_score

    saved = 0
    for deal in deals:
        try:
            existing = (
                db_session.query(ArbitrageDeal)
                .filter(
                    ArbitrageDeal.asin == deal.asin,
                    ArbitrageDeal.status == "active",
                )
                .first()
            )
            if existing:
                existing.buy_price = deal.deal_price
                existing.sell_price = deal.original_price or deal.deal_price
                existing.historical_avg = deal.original_price
                existing.title = deal.title
                existing.image_url = deal.image_url
                existing.buy_url = deal.url
                existing.detected_at = datetime.utcnow()
                existing.deal_tier = _deal_tier_for(deal)
                existing.is_profitable = True
                existing.net_profit = (
                    deal.original_price - deal.deal_price
                    if deal.original_price
                    else Decimal("0")
                )
                existing.roi = (
                    float((deal.original_price - deal.deal_price) / deal.original_price)
                    if deal.original_price and deal.original_price > 0
                    else 0
                )
                existing.score = calculate_deal_score(existing)
                db_session.commit()
                saved += 1
                continue

            sell_price = deal.original_price or deal.deal_price
            net_profit = (
                deal.original_price - deal.deal_price
                if deal.original_price
                else Decimal("0")
            )
            roi = (
                float(net_profit / deal.original_price)
                if deal.original_price and deal.original_price > 0
                else 0
            )

            new_deal = ArbitrageDeal(
                asin=deal.asin,
                title=deal.title,
                image_url=deal.image_url,
                buy_url=deal.url,
                buy_platform="amazon",
                retailer="amazon",
                deal_source="online",
                buy_price=deal.deal_price,
                sell_platform="amazon",
                sell_price=sell_price,
                historical_avg=deal.original_price,
                deal_tier=_deal_tier_for(deal),
                net_profit=net_profit,
                roi=roi,
                is_profitable=True,
                status="active",
                detected_at=datetime.utcnow(),
                category=deal.category,
            )
            db_session.add(new_deal)
            new_deal.score = calculate_deal_score(new_deal)
            db_session.commit()
            saved += 1

        except Exception as e:
            logger.warning(f"Failed to save deal for ASIN {deal.asin}: {e}")
            db_session.rollback()

    logger.info(f"Saved {saved} deals to database")
    return saved


async def update_missing_images(db_session, max_updates: int = 20) -> int:
    """Fetch and update images for deals that are missing them.

    Iterates through active deals without image_url and fetches the
    image from Amazon's product page. Rate-limited to avoid blocking.
    """
    from app.db.models import ArbitrageDeal

    deals_without_images = (
        db_session.query(ArbitrageDeal)
        .filter(
            ArbitrageDeal.status == "active",
            ArbitrageDeal.retailer == "amazon",
            (ArbitrageDeal.image_url == None) | (ArbitrageDeal.image_url == ""),
        )
        .limit(max_updates)
        .all()
    )

    if not deals_without_images:
        logger.info("No deals missing images")
        return 0

    logger.info(f"Fetching images for {len(deals_without_images)} deals...")
    updated = 0

    async with ScrapingClient(rate_limit_seconds=2.0) as client:
        for deal in deals_without_images:
            try:
                image_url = await fetch_amazon_image_for_asin(deal.asin, client)
                if image_url:
                    deal.image_url = image_url
                    db_session.commit()
                    updated += 1
                    logger.info(f"Got image for {deal.asin}: {image_url[:60]}")
                else:
                    logger.debug(f"No image found for {deal.asin}")
            except Exception as e:
                logger.warning(f"Failed to fetch image for {deal.asin}: {e}")
                db_session.rollback()

    logger.info(f"Updated {updated} deal images")
    return updated
