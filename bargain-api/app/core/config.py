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
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Resend (Email)
    RESEND_API_KEY: str = ""
    
    # Price Monitoring
    USER_AGENT: str = "Mozilla/5.0 (compatible; BargainHuntrs/1.0; +https://bargainhuntrs.com)"
    
    # Railway (set automatically)
    PORT: int = 4030
    RAILWAY_ENVIRONMENT: Optional[str] = None
    RAILWAY_PROJECT_NAME: Optional[str] = None
    RAILWAY_SERVICE_NAME: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
