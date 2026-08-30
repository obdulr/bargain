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
from app.services.affiliate_networks import fetch_awin_programmes
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
    # Security: reject non-http(s) URLs to prevent open redirect and XSS
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must start with http:// or https://",
        )
    if not parsed.hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must have a valid hostname",
        )

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
    # Security: reject non-http(s) URLs to prevent open redirect and XSS
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must start with http:// or https://",
        )
    if not parsed.hostname:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="URL must have a valid hostname",
        )

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


@router.get("/awin/discover")
async def awin_discover(
    country: str = "US",
    limit: int = 100,
    current_user: User = Depends(get_current_user),
):
    """List Awin programmes the publisher has not yet joined.

    Defaults to US notjoined programmes. Use `country` to filter by ISO
    Alpha-2 country code (e.g. GB, DE, FR).
    """
    programmes = await fetch_awin_programmes(
        relationship="notjoined",
        country_code=country,
    )
    results = []
    for prog in programmes[:limit]:
        results.append({
            "id": prog.get("id"),
            "name": prog.get("name"),
            "description": prog.get("description", "")[:300],
            "display_url": prog.get("displayUrl"),
            "logo_url": prog.get("logoUrl"),
            "primary_region": prog.get("primaryRegion"),
            "primary_sector": prog.get("primarySector"),
            "valid_domains": [
                d.get("domain") for d in prog.get("validDomains", [])
                if isinstance(d, dict)
            ],
            "link_status": prog.get("linkStatus"),
            "status": prog.get("status"),
        })
    return {"country": country, "count": len(results), "programmes": results}


@router.get("/awin/recommend")
async def awin_recommend(
    country: str = "US",
    sectors: str = "Retail & Shopping,Electronics,Home & Garden,Sports & Outdoors,Health & Beauty,Toys & Games,Pet Supplies,Food & Drink",
    link_status: str = "online",
    limit: int = 50,
    current_user: User = Depends(get_current_user),
):
    """Recommend Awin programmes worth joining for a deals/coupons site."""
    target_sectors = {s.strip().lower() for s in sectors.split(",") if s.strip()}
    want_link = link_status.lower() if link_status else ""

    programmes = await fetch_awin_programmes(
        relationship="notjoined",
        country_code=country,
    )

    scored = []
    for prog in programmes:
        prog_sector = (prog.get("primarySector") or "").lower()
        prog_link = (prog.get("linkStatus") or "").lower()
        prog_status = (prog.get("status") or "").lower()
        has_domains = bool(prog.get("validDomains"))

        if target_sectors and prog_sector not in target_sectors:
            continue
        if want_link and prog_link != want_link:
            continue
        if prog_status != "active":
            continue

        score = 0
        if prog_link == "online":
            score += 3
        if has_domains:
            score += 2
        if prog_sector in {"retail & shopping", "electronics"}:
            score += 1

        scored.append({
            "id": prog.get("id"),
            "name": prog.get("name"),
            "description": (prog.get("description", "") or "")[:300],
            "display_url": prog.get("displayUrl"),
            "logo_url": prog.get("logoUrl"),
            "primary_region": prog.get("primaryRegion"),
            "primary_sector": prog.get("primarySector"),
            "valid_domains": [
                d.get("domain") for d in prog.get("validDomains", [])
                if isinstance(d, dict)
            ],
            "link_status": prog.get("linkStatus"),
            "status": prog.get("status"),
            "score": score,
        })

    scored.sort(key=lambda x: x["score"], reverse=True)
    results = scored[:limit]
    return {"country": country, "count": len(results), "programmes": results}
