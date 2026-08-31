"""Newsletter API Router — subscribe, unsubscribe, admin listing, digest trigger."""
import os
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status, Header
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import List, Optional

from app.db.session import get_db
from app.db.models import NewsletterSubscriber, User
from app.routers.auth import get_current_user
from app.services.newsletter_service import (
    send_daily_digest,
    send_weekly_digest,
    send_welcome_newsletter,
)

router = APIRouter(prefix="/api/v1/newsletter", tags=["newsletter"])


# --- Schemas ---

class SubscribeRequest(BaseModel):
    email: EmailStr
    name: Optional[str] = None
    source: Optional[str] = None


class UnsubscribeRequest(BaseModel):
    email: EmailStr


class SubscriberResponse(BaseModel):
    id: str
    email: str
    name: Optional[str] = None
    subscribed_at: Optional[str] = None
    is_active: bool
    source: Optional[str] = None


class DigestResponse(BaseModel):
    sent: int
    digest_type: str


# --- Cron secret helper ---

def _verify_cron_secret(x_cron_secret: Optional[str] = Header(None)):
    expected = os.getenv("SCRAPE_CRON_SECRET")
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Newsletter digest endpoints are not configured. Set SCRAPE_CRON_SECRET.",
        )
    if x_cron_secret != expected:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or missing cron secret.",
        )


def _require_admin(current_user: User):
    if (current_user.role or "").lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )


# --- Endpoints ---

@router.post("/subscribe", response_model=dict, status_code=status.HTTP_201_CREATED)
async def subscribe(body: SubscribeRequest, db: Session = Depends(get_db)):
    """Add an email to the newsletter list and send a welcome email."""
    existing = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == body.email.lower()
    ).first()

    if existing and existing.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This email is already subscribed.",
        )

    if existing and not existing.is_active:
        # Reactivate previously unsubscribed user
        existing.is_active = True
        existing.unsubscribed_at = None
        existing.subscribed_at = datetime.utcnow()
        existing.name = body.name or existing.name
        existing.source = body.source or existing.source
        db.commit()
        db.refresh(existing)
    else:
        sub = NewsletterSubscriber(
            email=body.email.lower(),
            name=body.name,
            source=body.source or "website",
            is_active=True,
            subscribed_at=datetime.utcnow(),
        )
        db.add(sub)
        db.commit()
        db.refresh(sub)

    # Send welcome email (non-blocking, fails silently)
    try:
        send_welcome_newsletter(body.email.lower(), body.name)
    except Exception:
        pass

    return {"status": "subscribed", "email": body.email.lower()}


@router.post("/unsubscribe", response_model=dict)
async def unsubscribe(body: UnsubscribeRequest, db: Session = Depends(get_db)):
    """Remove an email from the newsletter list."""
    sub = db.query(NewsletterSubscriber).filter(
        NewsletterSubscriber.email == body.email.lower()
    ).first()

    if not sub or not sub.is_active:
        return {"status": "not_subscribed", "email": body.email.lower()}

    sub.is_active = False
    sub.unsubscribed_at = datetime.utcnow()
    db.commit()

    return {"status": "unsubscribed", "email": body.email.lower()}


@router.get("/subscribers", response_model=List[SubscriberResponse])
async def list_subscribers(
    active_only: bool = Query(True, description="Filter to active subscribers only"),
    limit: int = Query(100, le=500),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Admin only — list all newsletter subscribers."""
    _require_admin(current_user)
    query = db.query(NewsletterSubscriber)
    if active_only:
        query = query.filter(NewsletterSubscriber.is_active == True)
    query = query.order_by(NewsletterSubscriber.subscribed_at.desc())
    subs = query.offset(offset).limit(limit).all()
    return [
        SubscriberResponse(
            id=str(s.id),
            email=s.email,
            name=s.name,
            subscribed_at=s.subscribed_at.isoformat() if s.subscribed_at else None,
            is_active=s.is_active,
            source=s.source,
        )
        for s in subs
    ]


@router.post("/send-digest", response_model=DigestResponse)
async def trigger_digest(
    digest_type: str = Query("daily", description="daily or weekly"),
    x_cron_secret: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    """Trigger sending the deal digest to all subscribers. Protected by cron secret."""
    _verify_cron_secret(x_cron_secret)

    if digest_type == "weekly":
        sent = send_weekly_digest()
    else:
        sent = send_daily_digest()

    return DigestResponse(sent=sent, digest_type=digest_type)
