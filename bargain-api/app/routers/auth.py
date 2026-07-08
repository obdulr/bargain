from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.config import settings
from app.db.session import get_db
from app.db.models import User
from app.services.niche_service import get_all_niches, get_niche

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])
security = HTTPBearer(auto_error=False)

ACCESS_TOKEN_EXPIRE_SECONDS = 30 * 24 * 60 * 60  # 30 days like Prime


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    firstName: str | None = None
    lastName: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenRequest(BaseModel):
    token: str


class UpdateNichePreferences(BaseModel):
    subscribed_niches: list[str] = []


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(seconds=ACCESS_TOKEN_EXPIRE_SECONDS)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=60)
    to_encode = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")

    try:
        payload = jwt.decode(credentials.credentials, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None or payload.get("type") == "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.post("/register")
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == body.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        first_name=body.firstName,
        last_name=body.lastName,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    user.refresh_token = refresh_token
    db.commit()

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": ACCESS_TOKEN_EXPIRE_SECONDS,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "role": user.role,
        },
    }


@router.post("/login")
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if user is None or not user.is_active or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    access_token = create_access_token(str(user.id))
    refresh_token = create_refresh_token(str(user.id))
    user.refresh_token = refresh_token
    db.commit()

    return {
        "accessToken": access_token,
        "refreshToken": refresh_token,
        "expiresIn": ACCESS_TOKEN_EXPIRE_SECONDS,
        "user": {
            "id": str(user.id),
            "email": user.email,
            "firstName": user.first_name,
            "lastName": user.last_name,
            "role": user.role,
        },
    }


@router.get("/profile")
async def profile(current_user: User = Depends(get_current_user)):
    return {
        "success": True,
        "id": str(current_user.id),
        "email": current_user.email,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name,
        "role": current_user.role,
        "subscriptionTier": current_user.subscription_tier,
        "subscribedNiches": current_user.subscribed_niches or [],
    }


@router.get("/me")
async def me(current_user: User = Depends(get_current_user)):
    """Alias for /profile that the frontend calls as /api/v1/auth/me."""
    return {
        "success": True,
        "id": str(current_user.id),
        "email": current_user.email,
        "firstName": current_user.first_name,
        "lastName": current_user.last_name,
        "role": current_user.role,
        "subscriptionTier": current_user.subscription_tier,
        "subscribedNiches": current_user.subscribed_niches or [],
    }


@router.get("/me/niches")
async def get_my_niches(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the current user's niche subscriptions and all available niches."""
    available = [
        {
            "key": n.key,
            "name": n.display_name,
            "emoji": n.emoji,
            "description": n.description,
            "typical_margin": n.typical_margin,
        }
        for n in get_all_niches()
    ]
    return {
        "subscribed_niches": current_user.subscribed_niches or [],
        "available_niches": available,
    }


@router.put("/me/niches")
async def update_my_niches(
    body: UpdateNichePreferences,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the current user's niche subscriptions.

    Send an empty list to subscribe to all niches (no filter).
    Only valid niche keys are accepted; unknown keys are rejected.
    """
    valid_keys = {n.key for n in get_all_niches()}
    invalid = [k for k in body.subscribed_niches if k not in valid_keys]
    if invalid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown niche(s): {', '.join(invalid)}",
        )

    current_user.subscribed_niches = list(body.subscribed_niches)
    db.commit()
    db.refresh(current_user)

    return {
        "success": True,
        "subscribed_niches": current_user.subscribed_niches or [],
    }


@router.post("/refresh")
async def refresh(body: TokenRequest, db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(body.token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    user = db.query(User).filter(User.id == UUID(user_id)).first()
    if user is None or not user.is_active or user.refresh_token != body.token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    access_token = create_access_token(str(user.id))
    return {"accessToken": access_token, "expiresIn": ACCESS_TOKEN_EXPIRE_SECONDS}
