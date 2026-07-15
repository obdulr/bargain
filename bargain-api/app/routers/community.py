"""Community deal submission, voting, and leaderboard endpoints."""
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID
from datetime import datetime

from app.db.session import get_db
from app.db.models import User, UserSubmittedDeal, DealVote, ArbitrageDeal
from app.routers.auth import get_current_user
from app.services.email_service import send_deal_approved_email

router = APIRouter(prefix="/api/v1/community", tags=["community"])

# Aura points configuration
AURA_SUBMIT_DEAL = 10       # Points for submitting a deal
AURA_DEAL_APPROVED = 50     # Bonus when deal is approved
AURA_UPVOTE_RECEIVED = 2    # Points per upvote on your deal
AURA_DOWNVOTE_PENALTY = 1   # Points lost per downvote
AURA_VOTE_BONUS = 1         # Points for voting on others' deals

# Aura tier thresholds
AURA_TIERS = [
    (10000, "goat"),
    (1000, "elite"),
    (0, "hunter"),
]


def _compute_aura_tier(points: int) -> str:
    for threshold, tier in AURA_TIERS:
        if points >= threshold:
            return tier
    return "hunter"


class SubmitDealRequest(BaseModel):
    title: str
    url: str
    retailer: str
    original_price: Optional[float] = None
    sale_price: Optional[float] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None

    @field_validator("title", "url", "retailer")
    @classmethod
    def not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty")
        return v.strip()


class VoteRequest(BaseModel):
    vote: int  # 1 = upvote, -1 = downvote

    @field_validator("vote")
    @classmethod
    def valid_vote(cls, v):
        if v not in (1, -1):
            raise ValueError("Vote must be 1 (upvote) or -1 (downvote)")
        return v


class ModerateDealRequest(BaseModel):
    status: str  # approved or rejected
    rejection_reason: Optional[str] = None


class DealResponse(BaseModel):
    id: str
    title: str
    url: str
    image_url: Optional[str] = None
    retailer: str
    original_price: Optional[float] = None
    sale_price: Optional[float] = None
    discount_percent: Optional[float] = None
    category: Optional[str] = None
    description: Optional[str] = None
    status: str
    upvotes: int
    downvotes: int
    score: int
    user_aura: int
    user_tier: str
    created_at: str
    user_vote: Optional[int] = None  # 1, -1, or None if not voted


def _deal_to_response(deal: UserSubmittedDeal, user_vote: Optional[int] = None) -> dict:
    discount = None
    if deal.original_price and deal.sale_price and deal.original_price > 0:
        discount = round(
            (1 - float(deal.sale_price) / float(deal.original_price)) * 100, 1
        )
    elif deal.discount_percent:
        discount = float(deal.discount_percent)

    return {
        "id": str(deal.id),
        "title": deal.title,
        "url": deal.url,
        "image_url": deal.image_url,
        "retailer": deal.retailer,
        "original_price": float(deal.original_price) if deal.original_price else None,
        "sale_price": float(deal.sale_price) if deal.sale_price else None,
        "discount_percent": discount,
        "category": deal.category,
        "description": deal.description,
        "status": deal.status,
        "upvotes": deal.upvotes or 0,
        "downvotes": deal.downvotes or 0,
        "score": deal.score or 0,
        "user_aura": deal.user.aura_points if deal.user else 0,
        "user_tier": deal.user.aura_tier if deal.user else "hunter",
        "created_at": deal.created_at.isoformat() if deal.created_at else None,
        "user_vote": user_vote,
    }


# ─── Submit a Deal ────────────────────────────────────────────────────────────

@router.post("/deals/submit", status_code=status.HTTP_201_CREATED)
async def submit_deal(
    body: SubmitDealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Submit a community deal. Awards 10 Aura points."""
    # Check for duplicate URL
    existing = db.query(UserSubmittedDeal).filter(
        UserSubmittedDeal.url == body.url,
        UserSubmittedDeal.status != "rejected",
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This deal URL has already been submitted.",
        )

    discount = None
    if body.original_price and body.sale_price and body.original_price > 0:
        discount = round((1 - body.sale_price / body.original_price) * 100, 1)

    deal = UserSubmittedDeal(
        user_id=current_user.id,
        title=body.title,
        url=body.url,
        image_url=body.image_url,
        retailer=body.retailer.lower(),
        original_price=Decimal(str(body.original_price)) if body.original_price else None,
        sale_price=Decimal(str(body.sale_price)) if body.sale_price else None,
        discount_percent=discount,
        category=body.category,
        description=body.description,
    )
    db.add(deal)

    # Award Aura points for submitting
    current_user.aura_points = (current_user.aura_points or 0) + AURA_SUBMIT_DEAL
    current_user.aura_tier = _compute_aura_tier(current_user.aura_points)

    db.commit()
    db.refresh(deal)

    return {
        "success": True,
        "deal": _deal_to_response(deal),
        "aura_points": current_user.aura_points,
        "aura_tier": current_user.aura_tier,
    }


# ─── List Community Deals ─────────────────────────────────────────────────────

@router.get("/deals")
async def list_community_deals(
    status_filter: str = Query("approved", alias="status"),
    sort: str = Query("hot", description="hot, new, top"),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List community-submitted deals. Default: approved, sorted by hot (score)."""
    query = db.query(UserSubmittedDeal)

    # Non-admin users can only see approved deals (plus their own pending)
    if current_user.role == "admin":
        if status_filter != "all":
            query = query.filter(UserSubmittedDeal.status == status_filter)
    else:
        query = query.filter(
            (UserSubmittedDeal.status == "approved") |
            (UserSubmittedDeal.user_id == current_user.id)
        )

    # Sorting
    if sort == "new":
        query = query.order_by(desc(UserSubmittedDeal.created_at))
    elif sort == "top":
        query = query.order_by(desc(UserSubmittedDeal.score))
    else:  # hot
        query = query.order_by(desc(UserSubmittedDeal.score), desc(UserSubmittedDeal.created_at))

    deals = query.offset(offset).limit(limit).all()

    # Get user's votes for these deals
    deal_ids = [d.id for d in deals]
    votes = {}
    if deal_ids:
        vote_rows = db.query(DealVote).filter(
            DealVote.deal_id.in_(deal_ids),
            DealVote.user_id == current_user.id,
        ).all()
        votes = {v.deal_id: v.vote for v in vote_rows}

    return [_deal_to_response(d, votes.get(d.id)) for d in deals]


# ─── Get Single Deal ──────────────────────────────────────────────────────────

@router.get("/deals/{deal_id}")
async def get_community_deal(
    deal_id: UUID,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single community deal by ID."""
    deal = db.query(UserSubmittedDeal).filter(UserSubmittedDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    # Non-admin users can only see approved deals or their own
    if deal.status != "approved" and deal.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=404, detail="Deal not found")

    vote = db.query(DealVote).filter(
        DealVote.deal_id == deal.id,
        DealVote.user_id == current_user.id,
    ).first()

    return _deal_to_response(deal, vote.vote if vote else None)


# ─── Vote on a Deal ───────────────────────────────────────────────────────────

@router.post("/deals/{deal_id}/vote")
async def vote_deal(
    deal_id: UUID,
    body: VoteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Vote on a community deal. Awards 1 Aura point to voter, adjusts submitter's Aura."""
    deal = db.query(UserSubmittedDeal).filter(UserSubmittedDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if deal.status != "approved":
        raise HTTPException(status_code=400, detail="Can only vote on approved deals")

    if deal.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot vote on your own deal")

    # Check existing vote
    existing = db.query(DealVote).filter(
        DealVote.deal_id == deal_id,
        DealVote.user_id == current_user.id,
    ).first()

    if existing:
        if existing.vote == body.vote:
            # Same vote — remove it (toggle off)
            db.delete(existing)
            if body.vote == 1:
                deal.upvotes = max(0, (deal.upvotes or 0) - 1)
            else:
                deal.downvotes = max(0, (deal.downvotes or 0) - 1)
            deal.score = (deal.upvotes or 0) - (deal.downvotes or 0)
            db.commit()
            db.refresh(deal)
            return {
                "success": True,
                "action": "removed",
                "upvotes": deal.upvotes,
                "downvotes": deal.downvotes,
                "score": deal.score,
            }
        else:
            # Change vote
            old_vote = existing.vote
            existing.vote = body.vote
            if body.vote == 1:
                deal.upvotes = (deal.upvotes or 0) + 1
                deal.downvotes = max(0, (deal.downvotes or 0) - 1)
            else:
                deal.downvotes = (deal.downvotes or 0) + 1
                deal.upvotes = max(0, (deal.upvotes or 0) - 1)
            deal.score = (deal.upvotes or 0) - (deal.downvotes or 0)
    else:
        # New vote
        vote = DealVote(deal_id=deal_id, user_id=current_user.id, vote=body.vote)
        db.add(vote)
        if body.vote == 1:
            deal.upvotes = (deal.upvotes or 0) + 1
        else:
            deal.downvotes = (deal.downvotes or 0) + 1
        deal.score = (deal.upvotes or 0) - (deal.downvotes or 0)

        # Award Aura to voter for participating
        current_user.aura_points = (current_user.aura_points or 0) + AURA_VOTE_BONUS
        current_user.aura_tier = _compute_aura_tier(current_user.aura_points)

    # Adjust submitter's Aura based on vote
    submitter = db.query(User).filter(User.id == deal.user_id).first()
    if submitter:
        if body.vote == 1:
            submitter.aura_points = (submitter.aura_points or 0) + AURA_UPVOTE_RECEIVED
        else:
            submitter.aura_points = max(0, (submitter.aura_points or 0) - AURA_DOWNVOTE_PENALTY)
        submitter.aura_tier = _compute_aura_tier(submitter.aura_points)

    db.commit()
    db.refresh(deal)

    return {
        "success": True,
        "action": "voted",
        "upvotes": deal.upvotes,
        "downvotes": deal.downvotes,
        "score": deal.score,
        "aura_points": current_user.aura_points,
        "aura_tier": current_user.aura_tier,
    }


# ─── Admin Moderation ─────────────────────────────────────────────────────────

@router.put("/deals/{deal_id}/moderate")
async def moderate_deal(
    deal_id: UUID,
    body: ModerateDealRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Approve or reject a submitted deal. Admin only."""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")

    deal = db.query(UserSubmittedDeal).filter(UserSubmittedDeal.id == deal_id).first()
    if not deal:
        raise HTTPException(status_code=404, detail="Deal not found")

    if body.status not in ("approved", "rejected"):
        raise HTTPException(status_code=400, detail="Status must be 'approved' or 'rejected'")

    deal.status = body.status
    deal.reviewed_by = current_user.id
    deal.reviewed_at = datetime.utcnow()

    if body.status == "rejected":
        deal.rejection_reason = body.rejection_reason
    else:
        # Award bonus Aura to submitter for approved deal
        submitter = db.query(User).filter(User.id == deal.user_id).first()
        if submitter:
            submitter.aura_points = (submitter.aura_points or 0) + AURA_DEAL_APPROVED
            submitter.aura_tier = _compute_aura_tier(submitter.aura_points)
            # Send approval email
            send_deal_approved_email(submitter.email, deal.title, submitter.first_name)

    db.commit()
    db.refresh(deal)

    return {
        "success": True,
        "deal_id": str(deal.id),
        "status": deal.status,
    }


# ─── Leaderboard ──────────────────────────────────────────────────────────────

@router.get("/leaderboard")
async def leaderboard(
    limit: int = Query(50, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the Aura leaderboard — top deal hunters ranked by Aura points."""
    users = (
        db.query(User)
        .filter(User.aura_points > 0)
        .order_by(desc(User.aura_points))
        .limit(limit)
        .all()
    )

    # Count approved deals per user
    deal_counts = (
        db.query(UserSubmittedDeal.user_id, func.count(UserSubmittedDeal.id))
        .filter(UserSubmittedDeal.status == "approved")
        .group_by(UserSubmittedDeal.user_id)
        .all()
    )
    deal_count_map = {uid: count for uid, count in deal_counts}

    return [
        {
            "rank": idx + 1,
            "user_id": str(u.id),
            "name": u.full_name if hasattr(u, "full_name") else u.email,
            "email": u.email,
            "aura_points": u.aura_points or 0,
            "aura_tier": u.aura_tier or "hunter",
            "deals_submitted": deal_count_map.get(u.id, 0),
            "is_you": u.id == current_user.id,
        }
        for idx, u in enumerate(users)
    ]


# ─── User's Own Submitted Deals ───────────────────────────────────────────────

@router.get("/my-deals")
async def my_deals(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's submitted deals (all statuses)."""
    deals = (
        db.query(UserSubmittedDeal)
        .filter(UserSubmittedDeal.user_id == current_user.id)
        .order_by(desc(UserSubmittedDeal.created_at))
        .all()
    )
    return [_deal_to_response(d) for d in deals]


# ─── User's Aura Stats ────────────────────────────────────────────────────────

@router.get("/aura")
async def my_aura(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's Aura stats."""
    total_deals = db.query(UserSubmittedDeal).filter(
        UserSubmittedDeal.user_id == current_user.id,
    ).count()
    approved_deals = db.query(UserSubmittedDeal).filter(
        UserSubmittedDeal.user_id == current_user.id,
        UserSubmittedDeal.status == "approved",
    ).count()
    total_upvotes = db.query(func.sum(UserSubmittedDeal.upvotes)).filter(
        UserSubmittedDeal.user_id == current_user.id,
    ).scalar() or 0

    points = current_user.aura_points or 0
    tier = current_user.aura_tier or "hunter"

    # Next tier info
    next_tier = None
    points_to_next = 0
    for threshold, t in AURA_TIERS:
        if points < threshold:
            next_tier = t
            points_to_next = threshold - points
            break

    return {
        "aura_points": points,
        "aura_tier": tier,
        "next_tier": next_tier,
        "points_to_next": points_to_next,
        "deals_submitted": total_deals,
        "deals_approved": approved_deals,
        "total_upvotes_received": int(total_upvotes),
    }
