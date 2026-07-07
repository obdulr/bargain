"""
Alerts API Router — Phase 1

Endpoints for managing user alerts and the background scan scheduler.
"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.db.session import get_db
from app.db.models import Alert, User
from app.routers.auth import get_current_user
from app.services.alert_service import send_test_alert
from app.services.scheduler import scheduler

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


class AlertResponse(BaseModel):
    id: str
    type: str
    title: str
    description: Optional[str] = None
    source_url: Optional[str] = None
    potential_profit: Optional[float] = None
    status: str
    is_read: bool
    read_at: Optional[str] = None
    sent_at: Optional[str] = None
    created_at: str


def _alert_to_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        id=str(alert.id),
        type=alert.type,
        title=alert.title,
        description=alert.description,
        source_url=alert.source_url,
        potential_profit=float(alert.potential_profit) if alert.potential_profit else None,
        status=alert.status,
        is_read=alert.is_read if alert.is_read is not None else False,
        read_at=alert.read_at.isoformat() if alert.read_at else None,
        sent_at=alert.sent_at.isoformat() if alert.sent_at else None,
        created_at=alert.created_at.isoformat() if alert.created_at else None,
    )


# --- Alert CRUD Endpoints ---

@router.get("", response_model=List[AlertResponse])
async def list_alerts(
    unread_only: bool = Query(False, description="Filter to unread alerts only"),
    alert_type: Optional[str] = Query(None, description="Filter by alert type"),
    limit: int = Query(50, le=200),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List the current user's alerts with pagination."""
    query = db.query(Alert).filter(Alert.user_id == current_user.id)

    if unread_only:
        query = query.filter(Alert.is_read == False)

    if alert_type:
        query = query.filter(Alert.type == alert_type)

    query = query.order_by(Alert.created_at.desc())
    alerts = query.offset(offset).limit(limit).all()

    return [_alert_to_response(a) for a in alerts]


@router.get("/unread/count", response_model=dict)
async def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the count of unread alerts for the current user."""
    count = db.query(Alert).filter(
        Alert.user_id == current_user.id,
        Alert.is_read == False,
    ).count()
    return {"unread_count": count}


@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a specific alert by ID."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return _alert_to_response(alert)


@router.patch("/{alert_id}/read", response_model=AlertResponse)
async def mark_alert_read(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Mark an alert as read."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    alert.is_read = True
    alert.read_at = datetime.utcnow()
    db.commit()
    db.refresh(alert)
    return _alert_to_response(alert)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete an alert."""
    alert = db.query(Alert).filter(
        Alert.id == alert_id,
        Alert.user_id == current_user.id,
    ).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    db.delete(alert)
    db.commit()
    return None


@router.post("/test", response_model=AlertResponse)
async def send_test_alert_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a test alert to the current user to verify email setup."""
    alert = send_test_alert(db, current_user)
    return _alert_to_response(alert)


# --- Scheduler Control Endpoints ---

scheduler_router = APIRouter(prefix="/api/v1/scheduler", tags=["scheduler"])


def _require_admin(user: User) -> None:
    """Check that the user has admin role."""
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )


@scheduler_router.post("/start", response_model=dict)
async def start_scheduler(
    current_user: User = Depends(get_current_user),
):
    """Start the background scan scheduler (admin only)."""
    _require_admin(current_user)
    started = scheduler.start()
    return {
        "started": started,
        "status": scheduler.get_status(),
        "message": "Scheduler started" if started else "Scheduler already running",
    }


@scheduler_router.post("/stop", response_model=dict)
async def stop_scheduler(
    current_user: User = Depends(get_current_user),
):
    """Stop the background scan scheduler (admin only)."""
    _require_admin(current_user)
    stopped = scheduler.stop()
    return {
        "stopped": stopped,
        "status": scheduler.get_status(),
        "message": "Scheduler stopped" if stopped else "Scheduler was not running",
    }


@scheduler_router.get("/status", response_model=dict)
async def scheduler_status(
    current_user: User = Depends(get_current_user),
):
    """Get the current scheduler status."""
    return scheduler.get_status()
