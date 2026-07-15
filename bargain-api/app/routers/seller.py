"""Seller portal endpoints — verified sellers submit coupons and price drops."""
import logging
from decimal import Decimal
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models import User, SellerSubmission, CouponCode, ArbitrageDeal
from app.routers.auth import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/seller", tags=["seller"])


# ─── Request Models ────────────────────────────────────────────────────────────

class ApplySellerRequest(BaseModel):
    store_name: str
    website: str

    @field_validator("store_name", "website")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class SubmitCouponRequest(BaseModel):
    title: str
    url: str
    retailer: str
    coupon_code: str
    discount_type: str = "percentage"  # percentage, fixed, free_shipping
    discount_value: float
    expires_at: Optional[datetime] = None
    category: Optional[str] = None
    description: Optional[str] = None

    @field_validator("title", "url", "retailer", "coupon_code")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class SubmitPriceDropRequest(BaseModel):
    title: str
    url: str
    retailer: str
    original_price: float
    sale_price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    @field_validator("title", "url", "retailer")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()

    @field_validator("sale_price", "original_price")
    @classmethod
    def positive_price(cls, v):
        if v is None or v <= 0:
            raise ValueError("Price must be greater than 0")
        return v


class BulkDealItem(BaseModel):
    title: str
    url: str
    retailer: str
    original_price: float
    sale_price: float
    image_url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None


class BulkSubmitRequest(BaseModel):
    deals: List[BulkDealItem]


# ─── Helpers ───────────────────────────────────────────────────────────────────

def _require_verified_seller(user: User):
    """Raise 403 if the user is not a verified seller."""
    if not user.is_verified_seller:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Verified seller account required.",
        )


def _submission_to_response(sub: SellerSubmission) -> dict:
    return {
        "id": str(sub.id),
        "submission_type": sub.submission_type,
        "title": sub.title,
        "url": sub.url,
        "retailer": sub.retailer,
        "image_url": sub.image_url,
        "category": sub.category,
        "description": sub.description,
        "coupon_code": sub.coupon_code,
        "discount_type": sub.discount_type,
        "discount_value": float(sub.discount_value) if sub.discount_value is not None else None,
        "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
        "original_price": float(sub.original_price) if sub.original_price is not None else None,
        "sale_price": float(sub.sale_price) if sub.sale_price is not None else None,
        "status": sub.status,
        "promoted_deal_id": str(sub.promoted_deal_id) if sub.promoted_deal_id else None,
        "promoted_coupon_id": str(sub.promoted_coupon_id) if sub.promoted_coupon_id else None,
        "created_at": sub.created_at.isoformat() if sub.created_at else None,
    }


# ─── Apply to Become a Verified Seller ─────────────────────────────────────────

@router.post("/apply", status_code=status.HTTP_200_OK)
async def apply_as_seller(
    body: ApplySellerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Apply to become a verified seller. Auto-approves for now (admin can revoke later)."""
    current_user.is_verified_seller = True
    current_user.seller_store_name = body.store_name
    current_user.seller_website = body.website

    db.commit()
    db.refresh(current_user)

    logger.info(f"User {current_user.email} approved as seller: {body.store_name}")

    return {
        "success": True,
        "seller_profile": {
            "is_verified_seller": current_user.is_verified_seller,
            "seller_store_name": current_user.seller_store_name,
            "seller_website": current_user.seller_website,
        },
    }


# ─── Get Seller Profile ────────────────────────────────────────────────────────

@router.get("/profile")
async def get_seller_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's seller profile and submission counts."""
    _require_verified_seller(current_user)

    counts = db.query(
        SellerSubmission.submission_type,
        SellerSubmission.status,
        func.count(SellerSubmission.id),
    ).filter(
        SellerSubmission.seller_id == current_user.id,
    ).group_by(
        SellerSubmission.submission_type, SellerSubmission.status,
    ).all()

    submission_counts = {}
    for submission_type, sub_status, count in counts:
        key = f"{submission_type}_{sub_status}"
        submission_counts[key] = count

    total = db.query(func.count(SellerSubmission.id)).filter(
        SellerSubmission.seller_id == current_user.id,
    ).scalar() or 0

    return {
        "is_verified_seller": current_user.is_verified_seller,
        "seller_store_name": current_user.seller_store_name,
        "seller_website": current_user.seller_website,
        "total_submissions": total,
        "submission_counts": submission_counts,
    }


# ─── Submit a Coupon Code ──────────────────────────────────────────────────────

@router.post("/submit/coupon", status_code=status.HTTP_201_CREATED)
async def submit_coupon(
    body: SubmitCouponRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a coupon code. Verified sellers are auto-approved."""
    _require_verified_seller(current_user)

    # Create the SellerSubmission record
    submission = SellerSubmission(
        seller_id=current_user.id,
        submission_type="coupon_code",
        title=body.title,
        url=body.url,
        retailer=body.retailer.lower(),
        coupon_code=body.coupon_code,
        discount_type=body.discount_type,
        discount_value=Decimal(str(body.discount_value)),
        expires_at=body.expires_at,
        category=body.category,
        description=body.description,
        status="approved",
        reviewed_at=datetime.utcnow(),
    )
    db.add(submission)
    db.flush()  # get the submission id

    # Auto-approve: create the CouponCode record directly
    coupon = CouponCode(
        code=body.coupon_code,
        retailer=body.retailer.lower(),
        title=body.title,
        description=body.description,
        discount_type=body.discount_type,
        discount_value=Decimal(str(body.discount_value)),
        category=body.category,
        product_url=body.url,
        source="seller",
        source_url=body.url,
        expires_at=body.expires_at,
        verified=True,
        verified_at=datetime.utcnow(),
        status="active",
    )
    db.add(coupon)
    db.flush()

    # Link the submission to the promoted coupon
    submission.promoted_coupon_id = coupon.id

    db.commit()
    db.refresh(submission)
    db.refresh(coupon)

    logger.info(
        f"Seller {current_user.email} submitted coupon '{body.coupon_code}' for {body.retailer}"
    )

    return {
        "success": True,
        "submission": _submission_to_response(submission),
        "coupon": {
            "id": str(coupon.id),
            "code": coupon.code,
            "retailer": coupon.retailer,
            "discount_type": coupon.discount_type,
            "discount_value": float(coupon.discount_value) if coupon.discount_value is not None else None,
            "status": coupon.status,
            "verified": coupon.verified,
        },
    }


# ─── Submit a Price Drop ───────────────────────────────────────────────────────

@router.post("/submit/price-drop", status_code=status.HTTP_201_CREATED)
async def submit_price_drop(
    body: SubmitPriceDropRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a price drop. Verified sellers are auto-approved."""
    _require_verified_seller(current_user)

    if body.sale_price >= body.original_price:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale price must be lower than original price.",
        )

    # Compute discount percentage
    discount_percent = round(
        (1 - body.sale_price / body.original_price) * 100, 1
    )

    # Create the SellerSubmission record
    submission = SellerSubmission(
        seller_id=current_user.id,
        submission_type="price_drop",
        title=body.title,
        url=body.url,
        retailer=body.retailer.lower(),
        image_url=body.image_url,
        category=body.category,
        description=body.description,
        original_price=Decimal(str(body.original_price)),
        sale_price=Decimal(str(body.sale_price)),
        status="approved",
        reviewed_at=datetime.utcnow(),
    )
    db.add(submission)
    db.flush()

    # Auto-approve: create the ArbitrageDeal record directly
    deal = ArbitrageDeal(
        asin=f"SELLER-{submission.id}",  # synthetic identifier for seller-submitted deals
        title=body.title,
        image_url=body.image_url,
        buy_url=body.url,
        buy_platform="seller",
        retailer=body.retailer.lower(),
        deal_source="online",
        buy_price=Decimal(str(body.sale_price)),
        sell_platform="seller",
        sell_price=Decimal(str(body.original_price)),
        category=body.category,
        niche=body.category,
        is_profitable=True,
        status="active",
        deal_tier="clearance",
    )
    db.add(deal)
    db.flush()

    # Link the submission to the promoted deal
    submission.promoted_deal_id = deal.id

    db.commit()
    db.refresh(submission)
    db.refresh(deal)

    logger.info(
        f"Seller {current_user.email} submitted price drop '{body.title}' for {body.retailer}"
    )

    return {
        "success": True,
        "submission": _submission_to_response(submission),
        "deal": {
            "id": str(deal.id),
            "title": deal.title,
            "retailer": deal.retailer,
            "buy_price": float(deal.buy_price) if deal.buy_price is not None else None,
            "sell_price": float(deal.sell_price) if deal.sell_price is not None else None,
            "discount_percent": discount_percent,
            "status": deal.status,
        },
    }


# ─── Bulk Submit Deals ─────────────────────────────────────────────────────────

@router.post("/submit/bulk", status_code=status.HTTP_201_CREATED)
async def bulk_submit_deals(
    body: BulkSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Bulk submit price-drop deals. Verified sellers only."""
    _require_verified_seller(current_user)

    if not body.deals:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No deals provided.",
        )

    success_count = 0
    errors = []

    for idx, item in enumerate(body.deals):
        try:
            if item.sale_price >= item.original_price:
                errors.append({
                    "index": idx,
                    "title": item.title,
                    "error": "Sale price must be lower than original price.",
                })
                continue

            submission = SellerSubmission(
                seller_id=current_user.id,
                submission_type="price_drop",
                title=item.title,
                url=item.url,
                retailer=item.retailer.lower(),
                image_url=item.image_url,
                category=item.category,
                description=item.description,
                original_price=Decimal(str(item.original_price)),
                sale_price=Decimal(str(item.sale_price)),
                status="approved",
                reviewed_at=datetime.utcnow(),
            )
            db.add(submission)
            db.flush()

            deal = ArbitrageDeal(
                asin=f"SELLER-{submission.id}",
                title=item.title,
                image_url=item.image_url,
                buy_url=item.url,
                buy_platform="seller",
                retailer=item.retailer.lower(),
                deal_source="online",
                buy_price=Decimal(str(item.sale_price)),
                sell_platform="seller",
                sell_price=Decimal(str(item.original_price)),
                category=item.category,
                niche=item.category,
                is_profitable=True,
                status="active",
                deal_tier="clearance",
            )
            db.add(deal)
            db.flush()

            submission.promoted_deal_id = deal.id
            success_count += 1

        except Exception as e:
            logger.error(f"Bulk submit error at index {idx}: {e}")
            errors.append({
                "index": idx,
                "title": getattr(item, "title", None),
                "error": str(e),
            })

    db.commit()

    logger.info(
        f"Seller {current_user.email} bulk submitted {success_count}/{len(body.deals)} deals"
    )

    return {
        "success": True,
        "total_requested": len(body.deals),
        "successful": success_count,
        "errors": errors,
    }


# ─── List Seller's Own Submissions ─────────────────────────────────────────────

@router.get("/submissions")
async def list_seller_submissions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List all submissions for the current seller, newest first."""
    _require_verified_seller(current_user)

    submissions = db.query(SellerSubmission).filter(
        SellerSubmission.seller_id == current_user.id,
    ).order_by(desc(SellerSubmission.created_at)).all()

    return [_submission_to_response(s) for s in submissions]


# ─── Deactivate a Submission ───────────────────────────────────────────────────

@router.put("/submissions/{submission_id}/deactivate")
async def deactivate_submission(
    submission_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Deactivate (reject) a seller's own submission, removing it from the feed."""
    _require_verified_seller(current_user)

    submission = db.query(SellerSubmission).filter(
        SellerSubmission.id == submission_id,
        SellerSubmission.seller_id == current_user.id,
    ).first()

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found.",
        )

    submission.status = "rejected"
    submission.reviewed_at = datetime.utcnow()

    # Also deactivate the promoted coupon/deal if it exists
    if submission.promoted_coupon_id:
        coupon = db.query(CouponCode).filter(
            CouponCode.id == submission.promoted_coupon_id,
        ).first()
        if coupon:
            coupon.status = "expired"

    if submission.promoted_deal_id:
        deal = db.query(ArbitrageDeal).filter(
            ArbitrageDeal.id == submission.promoted_deal_id,
        ).first()
        if deal:
            deal.status = "rejected"

    db.commit()
    db.refresh(submission)

    logger.info(
        f"Seller {current_user.email} deactivated submission {submission_id}"
    )

    return {
        "success": True,
        "submission": _submission_to_response(submission),
    }
