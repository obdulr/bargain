from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    # Database (Railway provides DATABASE_URL automatically)
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/bargainhuntrs"
    
    # API
    API_V1_PREFIX: str = "/api/v1"
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS (Railway frontend URL will be added dynamically)
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "https://bargainhuntrs.com"]
    
    # Stripe
    STRIPE_API_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    
    # Firebase
    FIREBASE_CREDENTIALS_PATH: str = ""
    
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
