"""Subscription (Stripe) router.

Endpoints:
  POST /api/v1/subscriptions/create-checkout-session  (JWT protected)
  POST /api/v1/subscriptions/webhook                  (raw body, no auth)
  GET  /api/v1/subscriptions/current                  (JWT protected)
  POST /api/v1/subscriptions/cancel                   (JWT protected)
"""
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models import User, Subscription
from app.routers.auth import get_current_user
from app.services import stripe_service

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


class CreateCheckoutRequest(BaseModel):
    plan_id: str  # "free" | "pro" | "enterprise"


class CancelRequest(BaseModel):
    subscription_id: str | None = None


@router.post("/create-checkout-session")
async def create_checkout_session(
    body: CreateCheckoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a Stripe Checkout session for the given plan."""
    try:
        result = stripe_service.create_checkout_session(
            current_user.id, body.plan_id, db
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    if result.get("free"):
        # Free plan — no checkout needed, update tier directly.
        current_user.subscription_tier = "free"
        db.commit()
        return {
            "success": True,
            "plan": body.plan_id,
            "url": None,
            "message": "Activated free plan",
        }

    return {"success": True, "url": result["url"], "session_id": result["session_id"]}


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """Stripe webhook receiver. Uses the raw request body for signature verification."""
    payload = await request.body()
    signature = request.headers.get("Stripe-Signature", "")

    result = stripe_service.handle_webhook(payload, signature, db)
    if not result.get("received"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Webhook verification failed"),
        )

    return {"received": True, "type": result.get("type")}


@router.get("/current")
async def current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Return the current user's subscription details."""
    sub = (
        db.query(Subscription)
        .filter(Subscription.user_id == current_user.id)
        .order_by(Subscription.created_at.desc())
        .first()
    )
    return {
        "success": True,
        "tier": current_user.subscription_tier,
        "stripe_customer_id": current_user.stripe_customer_id,
        "stripe_subscription_id": current_user.stripe_subscription_id,
        "status": sub.status if sub else None,
        "current_period_end": sub.current_period_end.isoformat() if sub and sub.current_period_end else None,
        "cancel_at_period_end": sub.cancel_at_period_end if sub else False,
    }


@router.post("/cancel")
async def cancel_subscription(
    body: CancelRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Cancel the current user's Stripe subscription at period end."""
    subscription_id = body.subscription_id or current_user.stripe_subscription_id
    if not subscription_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription to cancel",
        )

    try:
        result = stripe_service.cancel_subscription(subscription_id)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel subscription: {exc}",
        )

    # Reflect the cancellation locally.
    sub = (
        db.query(Subscription)
        .filter(Subscription.stripe_subscription_id == subscription_id)
        .first()
    )
    if sub:
        sub.cancel_at_period_end = True
        db.commit()

    return {"success": True, **result}
