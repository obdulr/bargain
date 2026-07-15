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
    STRIPE_PRICE_HUNTER: str = ""
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

    # Coupon Scraping
    COUPON_AUTO_SCRAPE: bool = False
    COUPON_SCRAPE_INTERVAL_HOURS: int = 6

    # ─── Notification Channels ────────────────────────────────────────────

    # Discord
    DISCORD_WEBHOOK_URL: str = ""

    # Telegram
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHANNEL_ID: str = ""  # e.g. @bargainhuntrs_deals or -1001234567890

    # X.com (Twitter)
    TWITTER_API_KEY: str = ""
    TWITTER_API_SECRET: str = ""
    TWITTER_ACCESS_TOKEN: str = ""
    TWITTER_ACCESS_TOKEN_SECRET: str = ""

    # Facebook
    FACEBOOK_PAGE_ACCESS_TOKEN: str = ""
    FACEBOOK_PAGE_ID: str = ""

    # SMS (Telnyx)
    TELNYX_API_KEY: str = ""
    TELNYX_FROM_NUMBER: str = ""  # e.g. +1234567890
    TELNYX_MESSAGING_PROFILE_ID: str = ""  # Telnyx messaging profile ID

    # Notification settings
    NOTIFY_MIN_PROFIT: float = 5.0  # Only notify on deals with >= $5 net profit
    NOTIFY_GLITCH_IMMEDIATE: bool = True  # Send glitch alerts immediately to all channels

    # Price Monitoring
    USER_AGENT: str = "Mozilla/5.0 (compatible; BargainHuntrs/1.0; +https://bargainhuntrs.com)"

    # Scraper settings
    SCRAPER_RATE_LIMIT_SECONDS: float = 2.0  # Delay between requests to same domain
    SCRAPER_MAX_RETRIES: int = 3
    SCRAPER_PROXY_URL: str = ""  # Optional proxy for scraping (http://user:pass@host:port)

    # Keepa API (Amazon price history)
    KEEPA_API_KEY: str = ""

    # eBay API (Browse API for sold listings)
    EBAY_CLIENT_ID: str = ""
    EBAY_CLIENT_SECRET: str = ""

    # Affiliate IDs
    AMAZON_ASSOCIATES_TAG: str = ""  # e.g. "bargainhuntrs-20"
    EBAY_PARTNER_NETWORK_ID: str = ""  # eBay Partner Network campaign ID
    WALMART_AFFILIATE_ID: str = ""  # Walmart affiliate ID
    TARGET_AFFILIATE_ID: str = ""  # Target affiliate ID
    BESTBUY_AFFILIATE_ID: str = ""  # Best Buy affiliate ID
    RAKUTEN_AFFILIATE_ID: str = ""  # Rakuten/Legacy affiliate ID

    # Impact (affiliate network for real promo codes)
    IMPACT_ACCOUNT_SID: str = ""  # Impact Account SID (username for API auth)
    IMPACT_AUTH_TOKEN: str = ""  # Impact Auth Token (password for API auth)
    IMPACT_PROGRAM_IDS: str = ""  # Comma-separated Impact program IDs to fetch coupons from

    # X (Twitter) API credentials for auto-posting deals
    X_CONSUMER_KEY: str = ""
    X_CONSUMER_SECRET: str = ""
    X_ACCESS_TOKEN: str = ""
    X_ACCESS_TOKEN_SECRET: str = ""

    # Make.com webhook URL for X auto-posting via Buffer
    # Create a scenario: Webhook → Buffer → X
    # Set this to the webhook URL from Make.com
    MAKE_WEBHOOK_URL: str = ""

    # Buffer API for direct X posting (preferred over Make.com)
    BUFFER_API_KEY: str = ""
    BUFFER_CHANNEL_ID: str = ""        # X/Twitter
    BUFFER_IG_CHANNEL_ID: str = ""     # Instagram
    BUFFER_FB_CHANNEL_ID: str = ""     # Facebook
    BUFFER_ORG_ID: str = ""

    # Impact.com Affiliate API
    IMPACT_ACCOUNT_SID: str = ""
    IMPACT_AUTH_TOKEN: str = ""

    # Affiliate Network Credentials
    # Rakuten Advertising (https://pubhelp.rakutenadvertising.com)
    RAKUTEN_WEBSERVICES_TOKEN: str = ""
    RAKUTEN_SECURITY_TOKEN: str = ""

    # Awin (https://ui.awin.com/publisher-signup/en)
    AWIN_API_TOKEN: str = ""
    AWIN_PUBLISHER_ID: str = ""

    # CJ Affiliate (https://signup.cj.com)
    CJ_ACCESS_TOKEN: str = ""
    CJ_WEBSITE_ID: str = ""

    # Skimlinks (https://signup.skimlinks.com/en)
    SKIMLINKS_PRODUCT_KEY: str = ""
    SKIMLINKS_CLIENT_ID: str = ""
    SKIMLINKS_CLIENT_SECRET: str = ""

    # Niche categories for deal scanning
    NICHES: List[str] = [
        "electronics",
        "tools_home_improvement",
        "outdoor_garden",
        "toys_games",
        "kitchen_dining",
        "sports_fitness",
        "beauty_personal_care",
        "baby_nursery",
        "pet_supplies",
        "video_games",
    ]

    # Railway (set automatically)
    PORT: int = 4030
    RAILWAY_ENVIRONMENT: Optional[str] = None
    RAILWAY_PROJECT_NAME: Optional[str] = None
    RAILWAY_SERVICE_NAME: Optional[str] = None
    
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
