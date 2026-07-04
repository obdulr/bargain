from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional, Dict, Any
import json


class Settings(BaseSettings):
    # Database (Railway provides DATABASE_URL automatically)
    DATABASE_URL: str = "sqlite:///./bargain.db"
    
    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def convert_to_asyncpg(cls, v: str) -> str:
        """Convert Railway's default postgresql:// URL to asyncpg driver format."""
        if v.startswith("postgresql://") and not v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql://", "postgresql+asyncpg://", 1)
        return v
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS (Railway frontend URL will be added dynamically)
    ALLOWED_ORIGINS: List[str] = ["*"]
    
    # Stripe
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = ""
    FIREBASE_CREDENTIALS_JSON: Optional[Dict[str, Any]] = None
    
    @field_validator("FIREBASE_CREDENTIALS_JSON", mode="before")
    @classmethod
    def parse_firebase_credentials_json(cls, v):
        """Parse Firebase service account JSON if provided as a string."""
        if isinstance(v, str) and v:
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                return None
        return v
    
    # Resend (Email)
    RESEND_API_KEY: str = ""
    
    # Price Monitoring
    USER_AGENT: str = "Mozilla/5.0 (compatible; BargainHuntrs/1.0; +https://bargainhuntrs.com)"
    
    # Railway (set automatically)
    PORT: int = 4030
    RAILWAY_ENVIRONMENT: Optional[str] = None
    RAILWAY_PROJECT_NAME: Optional[str] = None
    RAILWAY_SERVICE_NAME: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
