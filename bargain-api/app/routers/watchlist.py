from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List
from uuid import UUID

from app.db.session import get_db
from app.db.models import User, WatchlistItem, PriceSnapshot
from app.routers.auth import get_current_user
from app.services.scraper import fetch_price

router = APIRouter(prefix="/api/v1/watchlist", tags=["watchlist"])


class WatchlistCreate(BaseModel):
    item_name: str
    retailer_url: str
    target_price: float | None = None


@router.get("", response_model=List[dict])
async def list_watchlist(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    items = db.query(WatchlistItem).filter(WatchlistItem.user_id == current_user.id).all()
    return [
        {
            "id": str(item.id),
            "item_name": item.item_name,
            "target_price": float(item.target_price) if item.target_price else None,
            "current_price": float(item.current_price) if item.current_price else None,
            "retailers": item.retailers or [],
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in items
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_watchlist_item(
    body: WatchlistCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    price, _ = await fetch_price(body.retailer_url)

    item = WatchlistItem(
        user_id=current_user.id,
        item_name=body.item_name,
        target_price=Decimal(str(body.target_price)) if body.target_price else None,
        current_price=price,
        retailers=[{"url": body.retailer_url, "price": float(price) if price else None}],
    )
    db.add(item)
    db.commit()
    db.refresh(item)

    if price:
        snapshot = PriceSnapshot(
            item_id=str(item.id),
            retailer=body.retailer_url,
            price=price,
        )
        db.add(snapshot)
        db.commit()

    return {
        "id": str(item.id),
        "item_name": item.item_name,
        "target_price": float(item.target_price) if item.target_price else None,
        "current_price": float(item.current_price) if item.current_price else None,
    }


@router.post("/{item_id}/refresh")
async def refresh_watchlist_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == current_user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    retailers = item.retailers or []
    if not retailers:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No retailer URL")

    url = retailers[0].get("url")
    price, _ = await fetch_price(url)
    if price is not None:
        item.current_price = price
        retailers[0]["price"] = float(price)
        item.retailers = retailers

        snapshot = PriceSnapshot(
            item_id=str(item.id),
            retailer=url,
            price=price,
        )
        db.add(snapshot)
        db.commit()
        db.refresh(item)

    return {
        "id": str(item.id),
        "item_name": item.item_name,
        "current_price": float(item.current_price) if item.current_price else None,
        "target_price": float(item.target_price) if item.target_price else None,
    }


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_watchlist_item(
    item_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    item = db.query(WatchlistItem).filter(
        WatchlistItem.id == item_id,
        WatchlistItem.user_id == current_user.id,
    ).first()
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    db.delete(item)
    db.commit()
    return None
