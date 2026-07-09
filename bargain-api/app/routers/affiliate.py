"""Affiliate click tracking router.

Tracks outbound clicks on affiliate links so we can measure conversion
rates and revenue per deal.
"""
import logging
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import AffiliateClick, ArbitrageDeal, User
from app.routers.auth import get_current_user
from app.services.affiliate_service import add_affiliate_tag, detect_retailer

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/affiliate", tags=["affiliate"])


class ClickRequest(BaseModel):
    url: str = ""
    retailer: str = ""
    asin: str = ""
    deal_id: Optional[str] = None
    user_id: Optional[str] = None


class ClickResponse(BaseModel):
    affiliate_url: str
    original_url: str
    retailer: str
    tracked: bool


@router.post("/click", response_model=ClickResponse)
async def track_click(
    body: ClickRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Track a click on a deal link and return the affiliate URL.

    Requires authentication. The authenticated user is recorded as the
    clicker unless an explicit ``user_id`` is supplied (admin override).
    """
    url = body.url or ""
    retailer = body.retailer or detect_retailer(url)
    asin = body.asin or ""

    affiliate_url = add_affiliate_tag(url, retailer, asin)

    # Resolve deal_id / user_id to UUIDs (best-effort)
    deal_id_uuid = None
    if body.deal_id:
        try:
            deal_id_uuid = UUID(str(body.deal_id))
        except (ValueError, TypeError):
            deal_id_uuid = None

    user_id_uuid = None
    if body.user_id:
        try:
            user_id_uuid = UUID(str(body.user_id))
        except (ValueError, TypeError):
            user_id_uuid = None
    if user_id_uuid is None:
        user_id_uuid = current_user.id

    tracked = False
    try:
        click = AffiliateClick(
            deal_id=deal_id_uuid,
            user_id=user_id_uuid,
            retailer=retailer or None,
            original_url=url,
            affiliate_url=affiliate_url,
            asin=asin or None,
            clicked_at=datetime.utcnow(),
        )
        db.add(click)
        db.commit()
        tracked = True
    except Exception as e:
        logger.warning(f"Failed to log affiliate click: {e}")
        db.rollback()

    return ClickResponse(
        affiliate_url=affiliate_url,
        original_url=url,
        retailer=retailer,
        tracked=tracked,
    )


@router.post("/click/public", response_model=ClickResponse)
async def track_click_public(
    body: ClickRequest,
    db: Session = Depends(get_db),
):
    """Public affiliate click — no authentication required.

    Appends the affiliate tag to the URL and logs the click anonymously.
    Used by the homepage deals feed so non-logged-in visitors can click
    affiliate links and generate revenue.
    """
    url = body.url or ""
    retailer = body.retailer or detect_retailer(url)
    asin = body.asin or ""

    affiliate_url = add_affiliate_tag(url, retailer, asin)

    deal_id_uuid = None
    if body.deal_id:
        try:
            deal_id_uuid = UUID(str(body.deal_id))
        except (ValueError, TypeError):
            deal_id_uuid = None

    tracked = False
    try:
        click = AffiliateClick(
            deal_id=deal_id_uuid,
            user_id=None,
            retailer=retailer or None,
            original_url=url,
            affiliate_url=affiliate_url,
            asin=asin or None,
            clicked_at=datetime.utcnow(),
        )
        db.add(click)
        db.commit()
        tracked = True
    except Exception as e:
        logger.warning(f"Failed to log public affiliate click: {e}")
        db.rollback()

    return ClickResponse(
        affiliate_url=affiliate_url,
        original_url=url,
        retailer=retailer,
        tracked=tracked,
    )


@router.get("/stats")
async def click_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Aggregate affiliate click statistics for the authenticated user."""
    try:
        total = db.query(AffiliateClick).filter(
            AffiliateClick.user_id == current_user.id
        ).count()
        converted = db.query(AffiliateClick).filter(
            AffiliateClick.user_id == current_user.id,
            AffiliateClick.converted == True,
        ).count()
    except Exception as e:
        logger.warning(f"Failed to query affiliate stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to load affiliate stats",
        )

    conversion_rate = (converted / total * 100) if total else 0
    return {
        "total_clicks": total,
        "converted": converted,
        "conversion_rate": round(conversion_rate, 2),
    }
