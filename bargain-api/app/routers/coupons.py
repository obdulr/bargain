"""
Coupon API Router

Endpoints for browsing, searching, scraping, and applying coupon codes.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.session import get_db
from app.db.models import User, CouponCode, ArbitrageDeal
from app.routers.auth import get_current_user
from app.services.coupon_scraper import (
    scrape_all_coupons,
    ScrapedCoupon,
    calculate_discounted_price,
    is_coupon_source_configured,
)
from app.services.arbitrage import apply_coupon_to_opportunity, ArbitrageOpportunity
from app.services.profit_calculator import calculate_profit, Platform, ProductCategory

router = APIRouter(prefix="/api/v1/coupons", tags=["coupons"])


class CouponResponse(BaseModel):
    id: str
    code: str
    retailer: str
    title: str
    description: Optional[str] = None
    discount_type: str
    discount_value: float
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    category: Optional[str] = None
    product_url: Optional[str] = None
    source: str
    source_url: Optional[str] = None
    expires_at: Optional[str] = None
    verified: bool
    times_used: int
    success_count: int
    status: str
    scraped_at: str


class ScrapeRequest(BaseModel):
    retailers: Optional[List[str]] = None  # None = all known retailers


class ScrapeResponse(BaseModel):
    scraped: int
    saved: int
    errors: int


class ApplyCouponRequest(BaseModel):
    deal_id: UUID
    coupon_id: UUID


class AppliedCouponResponse(BaseModel):
    deal_id: str
    original_buy_price: float
    effective_buy_price: float
    coupon_code: str
    coupon_discount: float
    original_net_profit: Optional[float] = None
    new_net_profit: Optional[float] = None
    original_roi: Optional[float] = None
    new_roi: Optional[float] = None


# ─── Endpoints ──────────────────────────────────────────────────────────────

@router.get("/status", response_model=dict)
async def coupon_source_status(
    current_user: User = Depends(get_current_user),
):
    """Check if a real coupon data source is configured.
    
    Returns whether the Impact affiliate network API is configured.
    When not configured, the coupons page should show a "coming soon"
    message instead of fake/generated codes.
    """
    return {
        "configured": is_coupon_source_configured(),
        "source": "impact" if is_coupon_source_configured() else None,
        "message": "Real coupons from Impact affiliate network" if is_coupon_source_configured()
                   else "Coupon integration not yet configured. Sign up at app.impact.com to enable real promo codes.",
    }


@router.get("/public", response_model=List[CouponResponse])
async def list_public_coupons(
    retailer: Optional[str] = Query(None, description="Filter by retailer"),
    category: Optional[str] = Query(None, description="Filter by category"),
    verified_only: bool = Query(False, description="Only verified coupons"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    db: Session = Depends(get_db),
):
    """Public coupon feed — no authentication required."""
    query = db.query(CouponCode).filter(CouponCode.status == "active")
    query = query.filter(
        (CouponCode.expires_at.is_(None)) | (CouponCode.expires_at > datetime.utcnow())
    )

    if retailer:
        query = query.filter(CouponCode.retailer == retailer.lower())
    if category:
        query = query.filter(CouponCode.category == category.lower())
    if verified_only:
        query = query.filter(CouponCode.verified == True)

    query = query.order_by(CouponCode.scraped_at.desc())
    coupons = query.offset(offset).limit(limit).all()
    return [_coupon_to_response(c) for c in coupons]


@router.get("/public/retailers", response_model=List[str])
async def get_public_coupon_retailers(
    db: Session = Depends(get_db),
):
    """Get list of retailers that have active coupons — public, no auth."""
    retailers = (
        db.query(CouponCode.retailer)
        .filter(CouponCode.status == "active")
        .distinct()
        .all()
    )
    return [r[0] for r in retailers if r[0]]


@router.get("", response_model=List[CouponResponse])
async def list_coupons(
    retailer: Optional[str] = Query(None, description="Filter by retailer"),
    category: Optional[str] = Query(None, description="Filter by category"),
    discount_type: Optional[str] = Query(None, description="percentage, fixed, free_shipping"),
    verified_only: bool = Query(False, description="Only verified coupons"),
    active_only: bool = Query(True, description="Only active (non-expired) coupons"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List coupon codes with optional filters."""
    query = db.query(CouponCode)

    if retailer:
        query = query.filter(CouponCode.retailer == retailer.lower())
    if category:
        query = query.filter(CouponCode.category == category.lower())
    if discount_type:
        query = query.filter(CouponCode.discount_type == discount_type)
    if verified_only:
        query = query.filter(CouponCode.verified == True)
    if active_only:
        query = query.filter(CouponCode.status == "active")
        # Filter out expired
        query = query.filter(
            (CouponCode.expires_at.is_(None)) | (CouponCode.expires_at > datetime.utcnow())
        )

    query = query.order_by(CouponCode.scraped_at.desc())
    coupons = query.offset(offset).limit(limit).all()

    return [_coupon_to_response(c) for c in coupons]


@router.get("/search", response_model=List[CouponResponse])
async def search_coupons(
    q: str = Query(..., min_length=2, description="Search query"),
    retailer: Optional[str] = Query(None),
    limit: int = Query(20, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Search coupons by title, description, or code."""
    query = db.query(CouponCode).filter(
        (CouponCode.title.ilike(f"%{q}%")) |
        (CouponCode.description.ilike(f"%{q}%")) |
        (CouponCode.code.ilike(f"%{q}%"))
    )

    if retailer:
        query = query.filter(CouponCode.retailer == retailer.lower())

    query = query.filter(CouponCode.status == "active")
    query = query.order_by(CouponCode.scraped_at.desc())
    coupons = query.limit(limit).all()

    return [_coupon_to_response(c) for c in coupons]


@router.get("/retailers", response_model=List[str])
async def list_retailers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all retailers that have coupons available."""
    retailers = db.query(CouponCode.retailer).distinct().all()
    return [r[0] for r in retailers if r[0]]


@router.get("/{coupon_id}", response_model=CouponResponse)
async def get_coupon(
    coupon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific coupon by ID."""
    coupon = db.query(CouponCode).filter(CouponCode.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")
    return _coupon_to_response(coupon)


@router.post("/scrape", response_model=ScrapeResponse)
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    body: ScrapeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Trigger a coupon scrape across all sources.

    Fetches real promo codes from the Impact affiliate network API.
    Returns 400 if Impact is not configured.
    """
    if not is_coupon_source_configured():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Coupon scraping is not configured. Set IMPACT_ACCOUNT_SID and IMPACT_AUTH_TOKEN env vars to fetch real promo codes from the Impact affiliate network.",
        )

    try:
        scraped_coupons = await scrape_all_coupons(retailers=body.retailers)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Scrape failed: {str(e)}",
        )

    saved = 0
    errors = 0

    for sc in scraped_coupons:
        try:
            _upsert_coupon(db, sc)
            saved += 1
        except Exception:
            errors += 1

    db.commit()

    # Mark expired coupons
    db.query(CouponCode).filter(
        CouponCode.expires_at < datetime.utcnow(),
        CouponCode.status == "active",
    ).update({"status": "expired"})
    db.commit()

    return ScrapeResponse(scraped=len(scraped_coupons), saved=saved, errors=errors)


@router.post("/apply", response_model=AppliedCouponResponse)
async def apply_coupon_to_deal(
    body: ApplyCouponRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply a coupon to an existing arbitrage deal and see the improved profit.

    This recalculates the deal's profit with the coupon-discounted buy price.
    """
    deal = db.query(ArbitrageDeal).filter(ArbitrageDeal.id == body.deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    coupon = db.query(CouponCode).filter(CouponCode.id == body.coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    if coupon.status != "active":
        raise HTTPException(status_code=400, detail="Coupon is not active")

    if coupon.expires_at and coupon.expires_at < datetime.utcnow():
        raise HTTPException(status_code=400, detail="Coupon has expired")

    # Check retailer match
    if coupon.retailer.lower() not in (deal.buy_platform or "amazon").lower():
        raise HTTPException(
            status_code=400,
            detail=f"Coupon is for {coupon.retailer}, deal is from {deal.buy_platform}",
        )

    original_price = deal.buy_price
    scraped = ScrapedCoupon(
        code=coupon.code,
        retailer=coupon.retailer,
        title=coupon.title,
        discount_type=coupon.discount_type,
        discount_value=coupon.discount_value or Decimal("0"),
        min_purchase=coupon.min_purchase,
        max_discount=coupon.max_discount,
    )

    effective_price, discount = calculate_discounted_price(original_price, scraped)

    if discount <= 0:
        raise HTTPException(status_code=400, detail="Coupon does not provide a discount for this deal")

    # Recalculate profit
    from app.services.arbitrage import _map_category
    category = _map_category(deal.category or "")

    new_profit = calculate_profit(
        buy_price=effective_price,
        sell_price=deal.sell_price,
        sell_platform=Platform.EBAY,
        category=category,
    )

    # Update coupon usage stats
    coupon.times_used = (coupon.times_used or 0) + 1
    db.commit()

    return AppliedCouponResponse(
        deal_id=str(deal.id),
        original_buy_price=float(original_price),
        effective_buy_price=float(effective_price),
        coupon_code=coupon.code,
        coupon_discount=float(discount),
        original_net_profit=float(deal.net_profit) if deal.net_profit else None,
        new_net_profit=float(new_profit.net_profit),
        original_roi=float(deal.roi) if deal.roi else None,
        new_roi=float(new_profit.roi),
    )


@router.get("/deal/{deal_id}/best", response_model=List[CouponResponse])
async def find_best_coupons_for_deal(
    deal_id: UUID,
    limit: int = Query(5, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Find the best coupons applicable to a specific arbitrage deal."""
    deal = db.query(ArbitrageDeal).filter(ArbitrageDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Find coupons for the deal's buy platform
    retailer = (deal.buy_platform or "amazon").lower()

    query = db.query(CouponCode).filter(
        CouponCode.retailer == retailer,
        CouponCode.status == "active",
        (CouponCode.expires_at.is_(None)) | (CouponCode.expires_at > datetime.utcnow()),
    )

    # Filter by category if deal has one
    if deal.category:
        query = query.filter(
            (CouponCode.category.is_(None)) | (CouponCode.category == deal.category.lower())
        )

    coupons = query.order_by(CouponCode.discount_value.desc()).limit(limit).all()

    return [_coupon_to_response(c) for c in coupons]


@router.delete("/all", response_model=dict)
async def delete_all_coupons(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete all coupons. Useful for clearing stale/fake data."""
    count = db.query(CouponCode).count()
    db.query(CouponCode).delete()
    db.commit()
    return {"deleted": count}


@router.delete("/{coupon_id}", response_model=dict)
async def delete_coupon(
    coupon_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a coupon (mark as expired)."""
    coupon = db.query(CouponCode).filter(CouponCode.id == coupon_id).first()
    if not coupon:
        raise HTTPException(status_code=404, detail="Coupon not found")

    coupon.status = "expired"
    db.commit()

    return {"status": "deleted", "id": str(coupon_id)}


# ─── Helpers ────────────────────────────────────────────────────────────────

def _upsert_coupon(db: Session, sc: ScrapedCoupon) -> CouponCode:
    """Insert or update a scraped coupon in the database."""
    existing = db.query(CouponCode).filter(
        CouponCode.code == sc.code,
        CouponCode.retailer == sc.retailer,
    ).first()

    if existing:
        # Update existing
        existing.title = sc.title
        existing.description = sc.description
        existing.discount_type = sc.discount_type
        existing.discount_value = sc.discount_value
        existing.min_purchase = sc.min_purchase
        existing.max_discount = sc.max_discount
        existing.category = sc.category
        existing.product_url = sc.product_url
        existing.source = sc.source
        existing.source_url = sc.source_url
        existing.expires_at = sc.expires_at
        existing.scraped_at = datetime.utcnow()
        existing.status = "active"
        return existing

    coupon = CouponCode(
        code=sc.code,
        retailer=sc.retailer,
        title=sc.title,
        description=sc.description,
        discount_type=sc.discount_type,
        discount_value=sc.discount_value,
        min_purchase=sc.min_purchase,
        max_discount=sc.max_discount,
        category=sc.category,
        product_url=sc.product_url,
        source=sc.source,
        source_url=sc.source_url,
        expires_at=sc.expires_at,
        status="active",
        scraped_at=datetime.utcnow(),
    )
    db.add(coupon)
    return coupon


def _coupon_to_response(c: CouponCode) -> CouponResponse:
    return CouponResponse(
        id=str(c.id),
        code=c.code,
        retailer=c.retailer,
        title=c.title,
        description=c.description,
        discount_type=c.discount_type,
        discount_value=float(c.discount_value) if c.discount_value else 0,
        min_purchase=float(c.min_purchase) if c.min_purchase else None,
        max_discount=float(c.max_discount) if c.max_discount else None,
        category=c.category,
        product_url=c.product_url,
        source=c.source,
        source_url=c.source_url,
        expires_at=c.expires_at.isoformat() if c.expires_at else None,
        verified=c.verified or False,
        times_used=c.times_used or 0,
        success_count=c.success_count or 0,
        status=c.status,
        scraped_at=c.scraped_at.isoformat() if c.scraped_at else "",
    )
