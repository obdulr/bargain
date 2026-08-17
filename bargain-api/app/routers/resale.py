"""Resale Pricing Assistant API — repricing suggestions for arbitrage flips."""

from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models import User, ResaleListing
from app.routers.auth import get_current_user
from app.services.resale_pricing import refresh_resale_listing_price

router = APIRouter(prefix="/api/v1/resale", tags=["resale"])


class ResaleListingCreate(BaseModel):
    title: str
    our_price: float
    buy_price: Optional[float] = None
    min_price: Optional[float] = None
    sell_platform: str = "ebay"
    search_query: Optional[str] = None
    source_deal_id: Optional[str] = None


class ResaleListingUpdate(BaseModel):
    our_price: Optional[float] = None
    min_price: Optional[float] = None
    status: Optional[str] = None


def _to_response(item: ResaleListing) -> dict:
    return {
        "id": str(item.id),
        "title": item.title,
        "sell_platform": item.sell_platform,
        "buy_price": float(item.buy_price) if item.buy_price is not None else None,
        "our_price": float(item.our_price),
        "min_price": float(item.min_price) if item.min_price is not None else None,
        "competitor_price": float(item.competitor_price) if item.competitor_price is not None else None,
        "suggested_price": float(item.suggested_price) if item.suggested_price is not None else None,
        "suggestion_reason": item.suggestion_reason,
        "status": item.status,
        "last_checked_at": item.last_checked_at.isoformat() if item.last_checked_at else None,
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }


@router.get("", response_model=List[dict])
async def list_resale_listings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = (
        db.query(ResaleListing)
        .filter(ResaleListing.user_id == current_user.id)
        .order_by(ResaleListing.created_at.desc())
        .all()
    )
    return [_to_response(i) for i in items]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_resale_listing(
    body: ResaleListingCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    tier = (current_user.subscription_tier or "free").lower()
    if tier == "free":
        count = db.query(ResaleListing).filter(ResaleListing.user_id == current_user.id).count()
        if count >= 10:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Free plan limited to 10 resale listings. Upgrade to Hunter for unlimited.",
            )

    source_deal_uuid = None
    if body.source_deal_id:
        try:
            source_deal_uuid = UUID(body.source_deal_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid source_deal_id")

    item = ResaleListing(
        user_id=current_user.id,
        source_deal_id=source_deal_uuid,
        title=body.title,
        search_query=body.search_query or body.title,
        sell_platform=body.sell_platform,
        buy_price=Decimal(str(body.buy_price)) if body.buy_price is not None else None,
        our_price=Decimal(str(body.our_price)),
        min_price=Decimal(str(body.min_price)) if body.min_price is not None else None,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.post("/{item_id}/refresh")
async def refresh_resale_listing(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(ResaleListing).filter(
        ResaleListing.id == item_id,
        ResaleListing.user_id == current_user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    result = await refresh_resale_listing_price(item)
    item.competitor_price = result.competitor_price
    item.suggested_price = result.suggested_price
    item.suggestion_reason = result.reason
    item.last_checked_at = result.checked_at
    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.patch("/{item_id}")
async def update_resale_listing(
    item_id: UUID,
    body: ResaleListingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(ResaleListing).filter(
        ResaleListing.id == item_id,
        ResaleListing.user_id == current_user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")

    if body.our_price is not None:
        item.our_price = Decimal(str(body.our_price))
        # Applying a new price invalidates the last suggestion.
        item.suggested_price = None
        item.suggestion_reason = None
    if body.min_price is not None:
        item.min_price = Decimal(str(body.min_price))
    if body.status is not None:
        if body.status not in ("active", "sold", "archived"):
            raise HTTPException(status_code=400, detail="Invalid status")
        item.status = body.status

    db.commit()
    db.refresh(item)
    return _to_response(item)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resale_listing(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(ResaleListing).filter(
        ResaleListing.id == item_id,
        ResaleListing.user_id == current_user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Listing not found")
    db.delete(item)
    db.commit()
    return None
