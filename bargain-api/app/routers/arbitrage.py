"""
Arbitrage API Router — Phase 1

Endpoints for scanning, viewing, and managing arbitrage opportunities.
"""

from decimal import Decimal
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, ArbitrageDeal, ScanRun, PriceSnapshot
from app.routers.auth import get_current_user
from app.services.arbitrage import (
    find_arbitrage_for_asin,
    scan_amazon_for_arbitrage,
    scan_niche,
    ArbitrageOpportunity,
)
from app.services.profit_calculator import Platform
from app.services.niche_service import get_niche, get_all_niches

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/arbitrage", tags=["arbitrage"])


class ScanRequest(BaseModel):
    asin: Optional[str] = None  # Single ASIN scan
    category: str = ""
    min_discount: float = 0.50  # 50% minimum discount
    max_price: float = 500.00
    limit: int = 20
    sell_platform: str = "ebay"


class DealResponse(BaseModel):
    id: str
    asin: str
    title: str
    image_url: Optional[str] = None
    buy_url: Optional[str] = None
    buy_price: float
    sell_price: float
    historical_avg: Optional[float] = None
    discrepancy: Optional[float] = None
    deal_tier: str
    retailer: Optional[str] = None
    deal_source: Optional[str] = None
    net_profit: Optional[float] = None
    roi: Optional[float] = None
    total_costs: Optional[float] = None
    platform_fee: Optional[float] = None
    bsr: Optional[int] = None
    category: Optional[str] = None
    niche: Optional[str] = None
    is_profitable: bool
    status: str
    detected_at: str


@router.get("/deals/public", response_model=List[DealResponse])
async def list_public_deals(
    tier: Optional[str] = Query(None, description="Filter by deal tier"),
    niche: Optional[str] = Query(None, description="Filter by niche"),
    source: Optional[str] = Query(None, description="Filter by deal source: online, in_store, nearby"),
    limit: int = Query(20, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """Public deals feed — no authentication required.

    Returns active profitable deals for display on the homepage so
    non-logged-in visitors can browse and click affiliate links.
    Use source=nearby to filter for deals at retailers with physical stores.
    """
    query = db.query(ArbitrageDeal).filter(
        ArbitrageDeal.is_profitable == True,
        ArbitrageDeal.status == "active",
        ArbitrageDeal.historical_avg != None,
        ArbitrageDeal.buy_price > 0,
    ).filter(
        ArbitrageDeal.historical_avg > ArbitrageDeal.buy_price
    )

    # Filter to 40%+ discount: buy_price <= historical_avg * 0.60
    # Using Python-side filter since SQL division with Numeric can be tricky
    if tier:
        query = query.filter(ArbitrageDeal.deal_tier == tier)

    if niche:
        query = query.filter(ArbitrageDeal.niche == niche)

    if source == "online":
        query = query.filter(ArbitrageDeal.deal_source == "online")
    elif source == "in_store":
        query = query.filter(ArbitrageDeal.deal_source == "in_store")
    elif source == "nearby":
        # Nearby = deals from retailers with physical stores
        nearby_retailers = [
            "walmart", "target", "best_buy", "bestbuy", "home_depot", "homedepot",
            "lowes", "costco", "samsclub", "sams_club", "kohls", "macys",
            "office_depot", "office_max", "staples", "bed_bath_beyond",
            "petsmart", "petco", "academy", "dick_sporting_goods",
            "tj_maxx", "marshalls", "ross", "ulta", "sephora",
        ]
        query = query.filter(ArbitrageDeal.retailer.in_(nearby_retailers))

    query = query.order_by(ArbitrageDeal.net_profit.desc())
    all_deals = query.all()

    # Apply 20%+ discount filter in Python (lowered from 40% to include
    # Impact.com/Walmart deals which typically have 20-40% discounts)
    min_discount = Decimal("0.20")
    filtered = [
        d for d in all_deals
        if d.historical_avg and d.buy_price
        and (Decimal(str(d.historical_avg)) - Decimal(str(d.buy_price))) / Decimal(str(d.historical_avg)) >= min_discount
    ]

    # Deduplicate by title (keep first occurrence — highest net_profit since sorted)
    seen_titles = set()
    unique_deals = []
    for d in filtered:
        title_key = (d.title or "")[:80].lower().strip()
        if title_key and title_key not in seen_titles:
            seen_titles.add(title_key)
            unique_deals.append(d)

    deals = unique_deals[offset:offset + limit]
    return [_deal_to_response(d) for d in deals]


@router.post("/deals/scrape-amazon", response_model=dict)
async def scrape_amazon_deals_endpoint(
    max_deals: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Scrape Amazon's Today's Deals page for real, currently-active deals.

    Requires authentication (admin/cron trigger). Fetches genuine discounted
    products from Amazon's Gold Box and /deals pages and stores them in the
    database so they appear on the homepage deals feed.
    """
    from app.services.amazon_deals_scraper import scrape_amazon_deals, save_deals_to_database

    try:
        deals = await scrape_amazon_deals(max_deals=max_deals)
        saved = save_deals_to_database(deals, db)
        return {
            "deals_found": len(deals),
            "deals_saved": saved,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape Amazon deals: {str(e)}",
        )


@router.post("/deals/scrape-amazon/public", response_model=dict)
async def scrape_amazon_deals_public(
    max_deals: int = Query(50, le=100),
    db: Session = Depends(get_db),
):
    """Public endpoint to scrape Amazon's Today's Deals — no auth required.

    Used for cron jobs and manual triggers to populate the deals feed.
    """
    from app.services.amazon_deals_scraper import scrape_amazon_deals, save_deals_to_database

    try:
        deals = await scrape_amazon_deals(max_deals=max_deals)
        saved = save_deals_to_database(deals, db)
        return {
            "deals_found": len(deals),
            "deals_saved": saved,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape Amazon deals: {str(e)}",
        )


@router.post("/deals/scrape-slickdeals/public", response_model=dict)
async def scrape_slickdeals_public(
    min_discount: int = Query(40, ge=0, le=90),
    db: Session = Depends(get_db),
):
    """Public endpoint to scrape Slickdeals RSS — no auth required.

    Fetches community-posted deals from Slickdeals' frontpage RSS feed
    and stores those with >= min_discount% discount in the database.
    """
    from app.services.slickdeals_scraper import scrape_slickdeals, save_slickdeals_to_database

    try:
        deals = await scrape_slickdeals(min_discount=min_discount)
        saved = save_slickdeals_to_database(deals, db)
        return {
            "deals_found": len(deals),
            "deals_saved": saved,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to scrape Slickdeals: {str(e)}",
        )


@router.post("/deals/scrape-all/public", response_model=dict)
async def scrape_all_deals_public(
    db: Session = Depends(get_db),
):
    """Public endpoint to scrape all deal sources — no auth required.

    Runs all scrapers (Amazon Gold Box + RSS feeds + affiliate networks)
    and combines the results into the deals database. Used for periodic cron jobs.
    """
    from app.services.amazon_deals_scraper import scrape_amazon_deals, save_deals_to_database
    from app.services.rss_deals_scraper import scrape_all_rss_feeds, save_rss_deals_to_database
    from app.services.affiliate_networks import fetch_all_affiliate_deals, get_configured_networks

    results = {"sources": {}, "total_saved": 0, "status": "success"}

    # Amazon Gold Box
    try:
        amazon_deals = await scrape_amazon_deals(max_deals=50)
        amazon_saved = save_deals_to_database(amazon_deals, db)
        results["sources"]["amazon"] = {
            "found": len(amazon_deals),
            "saved": amazon_saved,
        }
        results["total_saved"] += amazon_saved
    except Exception as e:
        results["sources"]["amazon"] = {"error": str(e)}

    # RSS feeds (Slickdeals, TechBargains, BensBargains, DansDeals)
    try:
        rss_deals = await scrape_all_rss_feeds(min_discount=40)
        rss_saved = save_rss_deals_to_database(rss_deals, db)
        results["sources"]["rss_feeds"] = {
            "found": len(rss_deals),
            "saved": rss_saved,
        }
        results["total_saved"] += rss_saved
    except Exception as e:
        results["sources"]["rss_feeds"] = {"error": str(e)}

    # Affiliate networks (only if configured)
    configured = get_configured_networks()
    if configured:
        try:
            affiliate_deals = await fetch_all_affiliate_deals()
            results["sources"]["affiliate_networks"] = {
                "configured": configured,
                "found": len(affiliate_deals),
            }
        except Exception as e:
            results["sources"]["affiliate_networks"] = {"error": str(e)}
    else:
        results["sources"]["affiliate_networks"] = {
            "configured": [],
            "message": "No affiliate networks configured. Sign up at Rakuten, Awin, or CJ Affiliate."
        }

    # Impact.com products (if configured)
    from app.services.impact_api import fetch_all_impact_deals, _is_configured as impact_configured
    if impact_configured():
        try:
            impact_deals = await fetch_all_impact_deals()
            impact_saved = 0
            impact_errors = 0
            for deal in impact_deals:
                try:
                    if not deal.get("deal_price") or not deal.get("title"):
                        continue

                    deal_id = f"impact_{deal.get('campaign_id', '')}_{abs(hash(deal.get('title', '')))}"[:36]

                    # Check for duplicates
                    existing = db.query(ArbitrageDeal).filter(
                        ArbitrageDeal.asin == deal_id,
                        ArbitrageDeal.status == "active",
                    ).first()
                    if existing:
                        continue

                    orig = deal.get("original_price") or 0
                    buy = deal.get("deal_price") or 0
                    if not buy or buy <= 0:
                        continue

                    tier = "glitch" if (deal.get("discount_percent", 0) or 0) >= 75 else "clearance"
                    new_deal = ArbitrageDeal(
                        asin=deal_id,
                        title=deal.get("title", "")[:500],
                        image_url=deal.get("image_url"),
                        buy_url=deal.get("deal_url"),
                        buy_platform=deal.get("retailer", "unknown"),
                        retailer=deal.get("retailer", "unknown"),
                        deal_source="online",
                        buy_price=buy,
                        sell_platform="impact",
                        sell_price=orig if orig else buy,
                        historical_avg=orig if orig else buy,
                        deal_tier=tier,
                        net_profit=(orig - buy) if orig else 0,
                        roi=float((orig - buy) / orig) if orig and orig > 0 else 0,
                        is_profitable=True,
                        status="active",
                        detected_at=datetime.utcnow(),
                    )
                    db.add(new_deal)
                    db.commit()
                    impact_saved += 1
                except Exception as e:
                    db.rollback()
                    impact_errors += 1
                    if impact_errors <= 3:
                        logger.warning(f"Failed to save Impact deal: {e}")

            results["sources"]["impact"] = {
                "found": len(impact_deals),
                "saved": impact_saved,
                "errors": impact_errors,
            }
            results["total_saved"] += impact_saved
        except Exception as e:
            results["sources"]["impact"] = {"error": str(e)}

    # Auto-post new deals to X via Make.com (if configured)
    from app.services.x_poster import is_configured as x_configured
    if x_configured():
        try:
            # Find deals not yet posted to X
            new_deals = (
                db.query(ArbitrageDeal)
                .filter(
                    ArbitrageDeal.status == "active",
                    ArbitrageDeal.is_profitable == True,
                    ArbitrageDeal.alerted_at == None,
                )
                .order_by(ArbitrageDeal.detected_at.desc())
                .limit(3)
                .all()
            )
            if new_deals:
                from app.services.x_poster import post_deal_to_x
                posted = 0
                for deal in new_deals:
                    discount = 0
                    if deal.historical_avg and deal.historical_avg > deal.buy_price:
                        discount = int(round((1 - float(deal.buy_price) / float(deal.historical_avg)) * 100))
                    result = await post_deal_to_x(
                        title=deal.title,
                        deal_price=float(deal.buy_price),
                        original_price=float(deal.historical_avg) if deal.historical_avg else None,
                        discount_percent=discount,
                        retailer=getattr(deal, "retailer", None) or "amazon",
                        deal_url=deal.buy_url or "",
                        deal_tier=deal.deal_tier,
                        image_url=deal.image_url,
                    )
                    if result.get("status") == "success":
                        posted += 1
                        deal.alerted_at = datetime.utcnow()
                        db.commit()
                results["x_posted"] = posted
            else:
                results["x_posted"] = 0
        except Exception as e:
            results["x_posted"] = 0
            results["x_error"] = str(e)

    return results


@router.post("/deals/update-images/public", response_model=dict)
async def update_deal_images_public(
    max_updates: int = Query(10, le=20),
    db: Session = Depends(get_db),
):
    """Public endpoint to fetch missing deal images — no auth required.

    Iterates through active deals without images and fetches them
    from Amazon product pages. Rate-limited to avoid blocking.
    Keeps max_updates low to avoid Railway timeout.
    """
    from app.services.amazon_deals_scraper import update_missing_images

    try:
        updated = await update_missing_images(db, max_updates=max_updates)
        return {
            "images_updated": updated,
            "status": "success",
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update images: {str(e)}",
        )


@router.post("/deals/{deal_id}/post-to-x/public", response_model=dict)
async def post_deal_to_x_public(
    deal_id: str,
    db: Session = Depends(get_db),
):
    """Post a specific deal to all social platforms — no auth required.

    Only posts deals with affiliate tracking links.
    Posts to X, Instagram, and Facebook via Buffer.
    """
    from app.services.x_poster import post_deal_to_x, is_configured

    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Posting not configured. Set BUFFER_API_KEY env var.",
        )

    deal = db.query(ArbitrageDeal).filter(ArbitrageDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Only post deals with affiliate links
    if not _has_affiliate_link(deal.buy_url):
        raise HTTPException(
            status_code=400,
            detail="This deal does not have an affiliate link and cannot be posted.",
        )

    discount = 0
    if deal.historical_avg and deal.historical_avg > deal.buy_price:
        discount = int(round((1 - float(deal.buy_price) / float(deal.historical_avg)) * 100))

    result = await post_deal_to_x(
        title=deal.title,
        deal_price=float(deal.buy_price),
        original_price=float(deal.historical_avg) if deal.historical_avg else None,
        discount_percent=discount,
        retailer=getattr(deal, "retailer", None) or "amazon",
        deal_url=deal.buy_url or "",
        deal_tier=deal.deal_tier,
        image_url=deal.image_url,
    )

    if result.get("status") == "success":
        deal.alerted_at = datetime.utcnow()
        db.commit()

    return result


def _has_affiliate_link(url: str) -> bool:
    """Check if a URL has an affiliate/tracking link."""
    if not url:
        return False
    url_lower = url.lower()
    # Impact.com tracking domains
    impact_domains = ["sjv.io", "7eer.net", "pxf.io", "evyy.net", "vneoga.net",
                      "elfm.net", "eyjo.net", "gqco.net", "hmxg.net", "ijrn.net",
                      "jewn.net", "jyeh.net", "mtko.net", "tcux.net", "zlvv.net"]
    # Direct affiliate tags
    affiliate_tags = ["tag=bargain0ae", "campid=", "affid=", "goto.walmart.com",
                      "affiliates.abebooks.com"]
    if any(d in url_lower for d in impact_domains):
        return True
    if any(t in url_lower for t in affiliate_tags):
        return True
    return False


@router.post("/deals/post-new-to-x/public", response_model=dict)
async def post_new_deals_to_x_public(
    max_posts: int = Query(5, le=10),
    db: Session = Depends(get_db),
):
    """Post deals that haven't been posted to social media yet — no auth required.

    Only posts deals that have affiliate tracking links.
    Posts to X, Instagram, and Facebook via Buffer.
    """
    from app.services.x_poster import post_deal_to_x, is_configured

    if not is_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Posting not configured. Set BUFFER_API_KEY env var.",
        )

    deals_to_post = (
        db.query(ArbitrageDeal)
        .filter(
            ArbitrageDeal.status == "active",
            ArbitrageDeal.is_profitable == True,
            ArbitrageDeal.alerted_at == None,
        )
        .order_by(ArbitrageDeal.detected_at.desc())
        .limit(max_posts * 3)  # Fetch more to filter for affiliate links
        .all()
    )

    # Only post deals with affiliate links
    affiliate_deals = [d for d in deals_to_post if _has_affiliate_link(d.buy_url)]

    if not affiliate_deals:
        return {"posted": 0, "status": "success", "message": "No new deals with affiliate links to post"}

    results = []
    posted = 0
    for deal in affiliate_deals[:max_posts]:
        discount = 0
        if deal.historical_avg and deal.historical_avg > deal.buy_price:
            discount = int(round((1 - float(deal.buy_price) / float(deal.historical_avg)) * 100))

        result = await post_deal_to_x(
            title=deal.title,
            deal_price=float(deal.buy_price),
            original_price=float(deal.historical_avg) if deal.historical_avg else None,
            discount_percent=discount,
            retailer=getattr(deal, "retailer", None) or "amazon",
            deal_url=deal.buy_url or "",
            deal_tier=deal.deal_tier,
            image_url=deal.image_url,
        )

        if result.get("status") == "success":
            posted += 1
            deal.alerted_at = datetime.utcnow()
            db.commit()
            results.append({
                "deal_id": str(deal.id),
                "title": deal.title[:60],
                "tweet_text": result.get("tweet_text", "")[:100],
            })
        else:
            results.append({
                "deal_id": str(deal.id),
                "title": deal.title[:60],
                "error": result.get("error"),
            })

    return {
        "posted": posted,
        "total": len(deals_to_post),
        "results": results,
        "status": "success",
    }


@router.get("/affiliate-networks/status", response_model=dict)
async def affiliate_networks_status():
    """Check which affiliate networks are configured.

    Returns the status of each affiliate network and signup URLs
    for those that aren't configured yet.
    """
    from app.services.affiliate_networks import get_configured_networks

    configured = get_configured_networks()

    networks = {
        "rakuten": {
            "configured": "rakuten" in configured,
            "signup_url": "https://pubhelp.rakutenadvertising.com/hc/en-us/articles/20898125890573-Publisher-Sign-Up-Process",
            "difficulty": "Easy — open network, no traffic requirements",
            "retailers": "Macy's, Sephora, Nordstrom, Adidas, Nike, Puma",
            "env_vars": ["RAKUTEN_WEBSERVICES_TOKEN", "RAKUTEN_SECURITY_TOKEN"],
        },
        "awin": {
            "configured": "awin" in configured,
            "signup_url": "https://ui.awin.com/publisher-signup/en",
            "difficulty": "Medium — requires $1 deposit (refunded)",
            "retailers": "Walmart, Target, 30K+ merchants (includes former ShareASale)",
            "env_vars": ["AWIN_API_TOKEN", "AWIN_PUBLISHER_ID"],
        },
        "cj": {
            "configured": "cj" in configured,
            "signup_url": "https://signup.cj.com/member/signup/publisher/",
            "difficulty": "Medium-Hard — two-level approval (network + merchants)",
            "retailers": "Lowe's, Wayfair, GoDaddy, Office Depot, Verizon",
            "env_vars": ["CJ_ACCESS_TOKEN", "CJ_WEBSITE_ID"],
        },
        "skimlinks": {
            "configured": "skimlinks" in configured,
            "signup_url": "https://signup.skimlinks.com/en",
            "difficulty": "Medium — manual review (2 business days)",
            "retailers": "Walmart, Best Buy, Home Depot, Wayfair, Kohl's",
            "env_vars": ["SKIMLINKS_PRODUCT_KEY", "SKIMLINKS_CLIENT_ID", "SKIMLINKS_CLIENT_SECRET"],
        },
    }

    return {
        "configured": configured,
        "networks": networks,
        "recommendation": "Sign up for Rakuten first (easiest approval), then Awin and CJ Affiliate.",
    }


@router.get("/niches", response_model=List[dict])
async def list_niches(
    current_user: User = Depends(get_current_user),
):
    """List all available niche categories for deal scanning/filtering."""
    return [
        {
            "key": n.key,
            "name": n.display_name,
            "emoji": n.emoji,
            "description": n.description,
            "typical_margin": n.typical_margin,
        }
        for n in get_all_niches()
    ]


@router.post("/scan/{niche}", response_model=dict)
async def scan_niche_endpoint(
    niche: str,
    max_products: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Scan for arbitrage deals in a specific niche category.

    Uses the niche's Amazon (Keepa) category ID to limit the scan, then
    tags and saves every profitable deal with the niche key.
    """
    if not get_niche(niche):
        raise HTTPException(status_code=404, detail=f"Unknown niche: {niche}")

    scan_run = ScanRun(
        scan_type=f"niche_{niche}",
        status="running",
    )
    db.add(scan_run)
    db.commit()
    db.refresh(scan_run)

    try:
        opportunities = await scan_niche(niche, max_products=max_products)

        scan_run.products_scanned = max_products
        scan_run.deals_found = len(opportunities)
        scan_run.completed_at = datetime.utcnow()
        scan_run.status = "completed"

        saved_deals = []
        for opp in opportunities:
            if opp.is_profitable:
                deal = _save_opportunity(db, opp)
                saved_deals.append(opp.to_dict())

        db.commit()

        return {
            "scan_id": str(scan_run.id),
            "niche": niche,
            "products_scanned": max_products,
            "deals_found": len(opportunities),
            "deals": saved_deals,
        }
    except Exception as e:
        scan_run.status = "failed"
        scan_run.error = str(e)
        scan_run.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.post("/scan", response_model=dict)
async def scan_for_deals(
    body: ScanRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Scan Amazon for arbitrage opportunities.

    If `asin` is provided, scans a single product.
    Otherwise, searches Amazon for discounted products and checks each against eBay.

    Requires Keepa API key for bulk scanning.
    """
    # Create scan run record
    scan_run = ScanRun(
        scan_type=f"amazon_{body.sell_platform}",
        status="running",
    )
    db.add(scan_run)
    db.commit()
    db.refresh(scan_run)

    try:
        if body.asin:
            # Single ASIN scan
            platform = Platform(body.sell_platform) if body.sell_platform else Platform.EBAY
            opportunity = await find_arbitrage_for_asin(body.asin, platform)

            scan_run.products_scanned = 1
            scan_run.completed_at = datetime.utcnow()
            scan_run.status = "completed"

            if opportunity and opportunity.is_profitable:
                # Save to database
                deal = _save_opportunity(db, opportunity)
                scan_run.deals_found = 1
                db.commit()

                return {
                    "scan_id": str(scan_run.id),
                    "products_scanned": 1,
                    "deals_found": 1,
                    "deals": [opportunity.to_dict()],
                }
            else:
                db.commit()
                return {
                    "scan_id": str(scan_run.id),
                    "products_scanned": 1,
                    "deals_found": 0,
                    "deals": [],
                    "message": "No profitable deals found for this ASIN",
                }
        else:
            # Bulk scan
            platform = Platform(body.sell_platform) if body.sell_platform else Platform.EBAY
            opportunities = await scan_amazon_for_arbitrage(
                category=body.category,
                min_discount=Decimal(str(body.min_discount)),
                max_price=Decimal(str(body.max_price)),
                limit=body.limit,
                sell_platform=platform,
            )

            scan_run.products_scanned = body.limit
            scan_run.deals_found = len(opportunities)
            scan_run.completed_at = datetime.utcnow()
            scan_run.status = "completed"

            # Save profitable deals to database
            saved_deals = []
            for opp in opportunities:
                if opp.is_profitable:
                    deal = _save_opportunity(db, opp)
                    saved_deals.append(opp.to_dict())

            db.commit()

            return {
                "scan_id": str(scan_run.id),
                "products_scanned": body.limit,
                "deals_found": len(opportunities),
                "deals": saved_deals,
            }

    except Exception as e:
        scan_run.status = "failed"
        scan_run.error = str(e)
        scan_run.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scan failed: {str(e)}",
        )


@router.get("/deals", response_model=List[DealResponse])
async def list_deals(
    tier: Optional[str] = Query(None, description="Filter by deal tier (glitch, clearance, arbitrage)"),
    niche: Optional[str] = Query(None, description="Filter by niche (electronics, tools_home_improvement, etc.)"),
    min_profit: Optional[float] = Query(None, description="Minimum net profit"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List arbitrage deals, optionally filtered by tier, niche, and minimum profit."""
    query = db.query(ArbitrageDeal).filter(ArbitrageDeal.is_profitable == True)

    if tier:
        query = query.filter(ArbitrageDeal.deal_tier == tier)

    if niche:
        query = query.filter(ArbitrageDeal.niche == niche)

    if min_profit is not None:
        query = query.filter(ArbitrageDeal.net_profit >= Decimal(str(min_profit)))

    query = query.order_by(ArbitrageDeal.net_profit.desc())
    deals = query.offset(offset).limit(limit).all()

    return [_deal_to_response(d) for d in deals]


@router.get("/deals/{deal_id}", response_model=DealResponse)
async def get_deal(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific deal by ID."""
    deal = db.query(ArbitrageDeal).filter(ArbitrageDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")
    return _deal_to_response(deal)


@router.get("/deals/{deal_id}/prediction")
async def get_price_prediction(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ML price prediction for a specific deal. PRO/ENTERPRISE feature.

    Free users receive a basic recommendation only; PRO/ENTERPRISE users
    get the full detailed analysis (confidence, predicted low, volatility,
    deal-quality score).
    """
    deal = db.query(ArbitrageDeal).filter(ArbitrageDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    from app.services.price_predictor import price_predictor

    # Build price history from stored PriceSnapshots for this ASIN
    snapshots = (
        db.query(PriceSnapshot)
        .filter(PriceSnapshot.item_id == deal.asin)
        .order_by(PriceSnapshot.timestamp.asc())
        .limit(100)
        .all()
    )

    price_history = [
        {"timestamp": s.timestamp.isoformat() if s.timestamp else None, "price": float(s.price)}
        for s in snapshots
        if s.price is not None
    ]

    # If we have no snapshot history, synthesize a minimal history from the
    # deal's own buy price / historical average so the predictor still works.
    if len(price_history) < price_predictor.min_data_points:
        synthetic = []
        if deal.historical_avg and deal.buy_price:
            avg = float(deal.historical_avg)
            cur = float(deal.buy_price)
            # Interpolate a few points between historical avg and current price
            steps = price_predictor.min_data_points
            for i in range(steps):
                frac = i / (steps - 1)
                synthetic.append({
                    "timestamp": None,
                    "price": round(avg + (cur - avg) * frac, 2),
                })
        price_history = synthetic

    current_price = float(deal.buy_price) if deal.buy_price else 0.0
    historical_avg = float(deal.historical_avg) if deal.historical_avg else 0.0

    trend = price_predictor.predict_price_trend(price_history)
    quality = price_predictor.score_deal_quality(price_history, current_price, historical_avg)

    tier = (current_user.subscription_tier or "free").lower()
    is_paid = tier in ("pro", "enterprise")

    if is_paid:
        return {
            "deal_id": str(deal.id),
            "asin": deal.asin,
            "current_price": current_price,
            "trend": trend,
            "deal_quality": quality,
            "tier": tier,
        }

    # Free users: basic recommendation only
    return {
        "deal_id": str(deal.id),
        "asin": deal.asin,
        "current_price": current_price,
        "recommendation": trend.get("recommendation", "monitor"),
        "tier": tier,
        "message": "Upgrade to PRO for full price prediction analysis.",
    }


@router.get("/stats", response_model=dict)
async def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get arbitrage scanning statistics."""
    total_deals = db.query(ArbitrageDeal).filter(ArbitrageDeal.is_profitable == True).count()
    active_deals = db.query(ArbitrageDeal).filter(
        ArbitrageDeal.is_profitable == True,
        ArbitrageDeal.status == "active",
    ).count()

    # Count by tier
    tier_counts = {}
    for tier in ["glitch", "clearance", "arbitrage", "watch"]:
        count = db.query(ArbitrageDeal).filter(
            ArbitrageDeal.deal_tier == tier,
            ArbitrageDeal.is_profitable == True,
        ).count()
        if count > 0:
            tier_counts[tier] = count

    # Recent scans
    recent_scans = db.query(ScanRun).order_by(ScanRun.started_at.desc()).limit(10).all()

    return {
        "total_profitable_deals": total_deals,
        "active_deals": active_deals,
        "tier_counts": tier_counts,
        "recent_scans": [
            {
                "id": str(s.id),
                "scan_type": s.scan_type,
                "products_scanned": s.products_scanned,
                "deals_found": s.deals_found,
                "status": s.status,
                "started_at": s.started_at.isoformat() if s.started_at else None,
                "completed_at": s.completed_at.isoformat() if s.completed_at else None,
            }
            for s in recent_scans
        ],
    }


@router.delete("/deals/all", response_model=dict)
async def delete_all_deals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete all arbitrage deals. Useful for clearing stale data."""
    count = db.query(ArbitrageDeal).count()
    db.query(ArbitrageDeal).delete()
    db.commit()
    return {"deleted": count}


def _save_opportunity(db: Session, opp: ArbitrageOpportunity) -> ArbitrageDeal:
    """Save an ArbitrageOpportunity to the database."""
    # Check for existing deal with same ASIN (dedup within 24h)
    from datetime import timedelta
    cutoff = datetime.utcnow() - timedelta(hours=24)
    existing = db.query(ArbitrageDeal).filter(
        ArbitrageDeal.asin == opp.asin,
        ArbitrageDeal.detected_at >= cutoff,
    ).first()

    if existing:
        # Update existing deal
        existing.buy_price = opp.buy_price
        existing.sell_price = opp.sell_price
        existing.net_profit = opp.profit.net_profit if opp.profit else None
        existing.roi = opp.profit.roi if opp.profit else None
        existing.total_costs = opp.profit.total_costs if opp.profit else None
        existing.platform_fee = opp.profit.platform_fee if opp.profit else None
        existing.detected_at = datetime.utcnow()
        if opp.niche:
            existing.niche = opp.niche
        db.commit()
        db.refresh(existing)
        return existing

    deal = ArbitrageDeal(
        asin=opp.asin,
        title=opp.title,
        image_url=opp.image_url,
        buy_url=opp.buy_url,
        buy_platform="amazon",
        buy_price=opp.buy_price,
        sell_platform=opp.sell_platform,
        sell_price=opp.sell_price,
        historical_avg=opp.historical_avg,
        discrepancy=opp.discrepancy,
        deal_tier=opp.deal_tier,
        net_profit=opp.profit.net_profit if opp.profit else None,
        roi=opp.profit.roi if opp.profit else None,
        total_costs=opp.profit.total_costs if opp.profit else None,
        platform_fee=opp.profit.platform_fee if opp.profit else None,
        bsr=opp.bsr,
        category=opp.category,
        niche=opp.niche,
        is_profitable=opp.is_profitable,
        status="active",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def _deal_to_response(deal: ArbitrageDeal) -> DealResponse:
    """Convert an ArbitrageDeal model to a DealResponse."""
    # Filter out broken Amazon image URLs (ASIN-based URLs don't work)
    image_url = deal.image_url
    if image_url and "m.media-amazon.com/images/I/" in image_url:
        # Check if it's a valid Amazon image ID (starts with a number, not B0)
        img_part = image_url.split("/images/I/")[-1].split(".")[0]
        if img_part.startswith("B0") and len(img_part) == 10:
            # This is an ASIN, not an image ID — Amazon will return 400
            image_url = None

    return DealResponse(
        id=str(deal.id),
        asin=deal.asin,
        title=deal.title,
        image_url=image_url,
        buy_url=deal.buy_url,
        buy_price=float(deal.buy_price),
        sell_price=float(deal.sell_price),
        historical_avg=float(deal.historical_avg) if deal.historical_avg else None,
        discrepancy=float(deal.discrepancy) if deal.discrepancy else None,
        deal_tier=deal.deal_tier,
        retailer=getattr(deal, "retailer", None) or deal.buy_platform or "amazon",
        deal_source=getattr(deal, "deal_source", None) or "online",
        net_profit=float(deal.net_profit) if deal.net_profit else None,
        roi=float(deal.roi) if deal.roi else None,
        total_costs=float(deal.total_costs) if deal.total_costs else None,
        platform_fee=float(deal.platform_fee) if deal.platform_fee else None,
        bsr=deal.bsr,
        category=deal.category,
        niche=deal.niche,
        is_profitable=deal.is_profitable,
        status=deal.status,
        detected_at=deal.detected_at.isoformat() if deal.detected_at else "",
    )
