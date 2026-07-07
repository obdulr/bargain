"""WebAuthn (passkey) authentication router.

Endpoints:
  POST /api/v1/auth/webauthn/register/start
  POST /api/v1/auth/webauthn/register/finish
  POST /api/v1/auth/webauthn/login/start
  POST /api/v1/auth/webauthn/login/finish
"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from uuid import UUID

from app.db.session import get_db
from app.db.models import User
from app.routers.auth import get_current_user
from app.services import webauthn_service

router = APIRouter(prefix="/api/v1/auth/webauthn", tags=["webauthn"])


class RegistrationStartResponse(BaseModel):
    options: str


class RegistrationFinishRequest(BaseModel):
    credential: str


class LoginStartRequest(BaseModel):
    email: EmailStr


class LoginStartResponse(BaseModel):
    options: str


class LoginFinishRequest(BaseModel):
    credential: str
    email: EmailStr


@router.post("/register/start")
async def webauthn_register_start(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Begin passkey registration for the authenticated user."""
    try:
        options_json = webauthn_service.generate_registration_options(
            current_user.id, db
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"success": True, "options": options_json}


@router.post("/register/finish")
async def webauthn_register_finish(
    body: RegistrationFinishRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Complete passkey registration by verifying the browser credential."""
    try:
        result = webauthn_service.verify_registration(
            current_user.id, body.credential, db
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

    return {"success": True, **result}


@router.post("/login/start")
async def webauthn_login_start(body: LoginStartRequest, db: Session = Depends(get_db)):
    """Begin passkey authentication for the given email."""
    options_json = webauthn_service.generate_authentication_options(body.email, db)
    return {"success": True, "options": options_json}


@router.post("/login/finish")
async def webauthn_login_finish(body: LoginFinishRequest, db: Session = Depends(get_db)):
    """Complete passkey authentication and return a JWT."""
    try:
        result = webauthn_service.verify_authentication(body.credential, body.email, db)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))

    return {"success": True, **result}
