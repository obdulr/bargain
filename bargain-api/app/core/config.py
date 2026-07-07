from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List, Optional


class Settings(BaseSettings):
    # Database (Railway provides DATABASE_URL automatically)
    DATABASE_URL: str = "sqlite:///./bargain.db"
    
    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def convert_to_psycopg2(cls, v: str) -> str:
        """Convert Railway's default postgresql:// URL to psycopg2 driver format.

        The codebase uses synchronous SQLAlchemy (create_engine/Session), so we
        normalize to the psycopg2 driver rather than asyncpg.
        """
        if v.startswith("postgresql+asyncpg://"):
            return v.replace("postgresql+asyncpg://", "postgresql+psycopg2://", 1)
        if v.startswith("postgresql://") and not v.startswith("postgresql+psycopg2://"):
            return v.replace("postgresql://", "postgresql+psycopg2://", 1)
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
    STRIPE_SECRET_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_FREE: str = ""
    STRIPE_PRICE_PRO: str = ""
    STRIPE_PRICE_ENTERPRISE: str = ""
    FRONTEND_URL: str = "http://localhost:3030"

    # WebAuthn (passkeys)
    WEB_AUTHN_RP_ID: str = "localhost"
    WEB_AUTHN_RP_NAME: str = "BargainHuntrs"
    WEB_AUTHN_ORIGIN: str = "http://localhost:3030"
    
    # Resend (Email)
    RESEND_API_KEY: str = ""
    ALERT_FROM_EMAIL: str = "alerts@bargainhuntrs.com"

    # Scheduled Scanning
    AUTO_SCAN: bool = False
    SCAN_INTERVAL_MINUTES: int = 60

    # Price Monitoring
    USER_AGENT: str = "Mozilla/5.0 (compatible; BargainHuntrs/1.0; +https://bargainhuntrs.com)"

    # Keepa API (Amazon price history)
    KEEPA_API_KEY: str = ""

    # eBay API (Browse API for sold listings)
    EBAY_CLIENT_ID: str = ""
    EBAY_CLIENT_SECRET: str = ""
    
    # Railway (set automatically)
    PORT: int = 4030
    RAILWAY_ENVIRONMENT: Optional[str] = None
    RAILWAY_PROJECT_NAME: Optional[str] = None
    RAILWAY_SERVICE_NAME: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
