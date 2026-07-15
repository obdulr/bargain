from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, watchlist, waitlist, arbitrage, subscriptions, coupons, notifications, affiliate, community
from app.routers.alerts import router as alerts_router, scheduler_router

# WebAuthn (passkeys) is optional — requires python-webauthn package
try:
    from app.routers import webauthn
    _HAS_WEBAUTHN = True
except ImportError:
    _HAS_WEBAUTHN = False
from app.services.scheduler import scheduler
from app.core.config import settings

app = FastAPI(
    title="BargainHuntrs API",
    description="Arbitrage intelligence platform API",
    version="0.1.0",
)

# Add CORS middleware with fallback
try:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
except Exception:
    # Fallback if settings fail to load
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(auth.router)
if _HAS_WEBAUTHN:
    app.include_router(webauthn.router)
app.include_router(watchlist.router)
app.include_router(waitlist.router)
app.include_router(arbitrage.router)
app.include_router(subscriptions.router)
app.include_router(coupons.router)
app.include_router(notifications.router)
app.include_router(affiliate.router)
app.include_router(alerts_router)
app.include_router(scheduler_router)
app.include_router(community.router)


@app.on_event("startup")
async def startup_event():
    """Start the background scanner on app startup if AUTO_SCAN is enabled."""
    if settings.AUTO_SCAN:
        scheduler.start()
        print(f"[Startup] Auto-scan enabled — scheduler started (interval: {settings.SCAN_INTERVAL_MINUTES}min)")
    else:
        print("[Startup] Auto-scan disabled — scheduler not started")


@app.on_event("shutdown")
async def shutdown_event():
    """Stop the background scanner on app shutdown."""
    if scheduler.is_running:
        scheduler.stop()
        print("[Shutdown] Scheduler stopped")


@app.get("/")
async def root():
    return {
        "message": "BargainHuntrs API",
        "version": "0.2.0",
        "status": "operational",
        "deploy_id": "bcrypt-fix-2026-07-08"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
