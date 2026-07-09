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
    all_deals.sort(key=lambda d: d.discount_percent or 0, reverse=True)
    return all_deals[:max_deals]


def save_deals_to_database(deals: list[AmazonDeal], db_session) -> int:
    """Save scraped deals to the ArbitrageDeal table."""
    from app.db.models import ArbitrageDeal

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
                existing.deal_tier = "glitch" if deal.deal_type == "lightning" else "clearance"
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
                buy_price=deal.deal_price,
                sell_platform="amazon",
                sell_price=sell_price,
                historical_avg=deal.original_price,
                deal_tier="glitch" if deal.deal_type == "lightning" else "clearance",
                net_profit=net_profit,
                roi=roi,
                is_profitable=True,
                status="active",
                detected_at=datetime.utcnow(),
                category=deal.category,
            )
            db_session.add(new_deal)
            db_session.commit()
            saved += 1

        except Exception as e:
            logger.warning(f"Failed to save deal for ASIN {deal.asin}: {e}")
            db_session.rollback()

    logger.info(f"Saved {saved} deals to database")
    return saved
