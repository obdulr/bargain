from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from typing import Optional

from app.db.session import get_db
from app.db.models import WaitlistEntry

router = APIRouter(prefix="/api/v1/waitlist", tags=["waitlist"])


class WaitlistRequest(BaseModel):
    email: EmailStr
    name: str
    plan: Optional[str] = None
    source: Optional[str] = None
    message: Optional[str] = None


class WaitlistResponse(BaseModel):
    success: bool
    message: str


@router.post("", response_model=WaitlistResponse, status_code=status.HTTP_201_CREATED)
async def join_waitlist(body: WaitlistRequest, db: Session = Depends(get_db)):
    existing = db.query(WaitlistEntry).filter(WaitlistEntry.email == body.email).first()
    if existing:
        return WaitlistResponse(success=True, message="You are already on the waitlist.")

    entry = WaitlistEntry(
        email=body.email,
        name=body.name,
        plan=body.plan or "",
        source=body.source or "",
        message=body.message or "",
    )
    db.add(entry)
    db.commit()
    return WaitlistResponse(success=True, message="You have joined the waitlist.")
