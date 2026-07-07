"""
Arbitrage API Router — Phase 1

Endpoints for scanning, viewing, and managing arbitrage opportunities.
"""

from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, ArbitrageDeal, ScanRun
from app.routers.auth import get_current_user
from app.services.arbitrage import (
    find_arbitrage_for_asin,
    scan_amazon_for_arbitrage,
    ArbitrageOpportunity,
)
from app.services.profit_calculator import Platform

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
    net_profit: Optional[float] = None
    roi: Optional[float] = None
    total_costs: Optional[float] = None
    platform_fee: Optional[float] = None
    bsr: Optional[int] = None
    category: Optional[str] = None
    is_profitable: bool
    status: str
    detected_at: str


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
    min_profit: Optional[float] = Query(None, description="Minimum net profit"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List arbitrage deals, optionally filtered by tier and minimum profit."""
    query = db.query(ArbitrageDeal).filter(ArbitrageDeal.is_profitable == True)

    if tier:
        query = query.filter(ArbitrageDeal.deal_tier == tier)

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
        is_profitable=opp.is_profitable,
        status="active",
    )
    db.add(deal)
    db.commit()
    db.refresh(deal)
    return deal


def _deal_to_response(deal: ArbitrageDeal) -> DealResponse:
    """Convert an ArbitrageDeal model to a DealResponse."""
    return DealResponse(
        id=str(deal.id),
        asin=deal.asin,
        title=deal.title,
        image_url=deal.image_url,
        buy_url=deal.buy_url,
        buy_price=float(deal.buy_price),
        sell_price=float(deal.sell_price),
        historical_avg=float(deal.historical_avg) if deal.historical_avg else None,
        discrepancy=float(deal.discrepancy) if deal.discrepancy else None,
        deal_tier=deal.deal_tier,
        net_profit=float(deal.net_profit) if deal.net_profit else None,
        roi=float(deal.roi) if deal.roi else None,
        total_costs=float(deal.total_costs) if deal.total_costs else None,
        platform_fee=float(deal.platform_fee) if deal.platform_fee else None,
        bsr=deal.bsr,
        category=deal.category,
        is_profitable=deal.is_profitable,
        status=deal.status,
        detected_at=deal.detected_at.isoformat() if deal.detected_at else "",
    )
