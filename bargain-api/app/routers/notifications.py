"""
Notification API Router

Endpoints for viewing notification history and testing channels.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, NotificationLog, ArbitrageDeal
from app.routers.auth import get_current_user
from app.services.notification_service import distribute_deal, DealInfo
from app.core.config import settings

router = APIRouter(prefix="/api/v1/notifications", tags=["notifications"])


class NotificationResponse(BaseModel):
    id: str
    asin: Optional[str] = None
    channel: str
    recipient: Optional[str] = None
    status: str
    error: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str


class ChannelStatus(BaseModel):
    channel: str
    configured: bool


class TestNotificationResponse(BaseModel):
    results: dict


@router.get("/channels", response_model=List[ChannelStatus])
async def list_channels(
    current_user: User = Depends(get_current_user),
):
    """List all notification channels and their configuration status."""
    channels = [
        ("discord", bool(settings.DISCORD_WEBHOOK_URL)),
        ("telegram", bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHANNEL_ID)),
        ("twitter", bool(settings.TWITTER_API_KEY and settings.TWITTER_ACCESS_TOKEN)),
        ("facebook", bool(settings.FACEBOOK_PAGE_ACCESS_TOKEN and settings.FACEBOOK_PAGE_ID)),
        ("sms", bool(settings.TELNYX_API_KEY and settings.TELNYX_FROM_NUMBER)),
        ("email", bool(settings.RESEND_API_KEY)),
    ]
    return [ChannelStatus(channel=name, configured=configured) for name, configured in channels]


@router.get("/history", response_model=List[NotificationResponse])
async def notification_history(
    channel: Optional[str] = Query(None, description="Filter by channel"),
    status: Optional[str] = Query(None, description="Filter by status (sent, failed)"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """View notification send history."""
    query = db.query(NotificationLog)

    if channel:
        query = query.filter(NotificationLog.channel == channel)
    if status:
        query = query.filter(NotificationLog.status == status)

    query = query.order_by(NotificationLog.created_at.desc())
    logs = query.offset(offset).limit(limit).all()

    return [
        NotificationResponse(
            id=str(log.id),
            asin=log.asin,
            channel=log.channel,
            recipient=log.recipient,
            status=log.status,
            error=log.error,
            sent_at=log.sent_at.isoformat() if log.sent_at else None,
            created_at=log.created_at.isoformat() if log.created_at else "",
        )
        for log in logs
    ]


@router.post("/test", response_model=TestNotificationResponse)
async def test_notification(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a test notification to all configured channels."""
    test_deal = DealInfo(
        asin="TEST001",
        title="Test Deal — Notification System Check",
        buy_price=__import__("decimal").Decimal("19.99"),
        sell_price=__import__("decimal").Decimal("39.99"),
        net_profit=__import__("decimal").Decimal("12.50"),
        roi=__import__("decimal").Decimal("0.63"),
        deal_tier="arbitrage",
        buy_url="https://www.amazon.com/dp/B08N5WRWNW",
        image_url=None,
    )

    results = await distribute_deal(test_deal, db)
    return TestNotificationResponse(results=results)


@router.post("/deal/{deal_id}/distribute", response_model=TestNotificationResponse)
async def distribute_existing_deal(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Manually distribute an existing arbitrage deal to all notification channels."""
    deal = db.query(ArbitrageDeal).filter(ArbitrageDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    deal_info = DealInfo.from_deal(deal)
    results = await distribute_deal(deal_info, db)
    return TestNotificationResponse(results=results)
