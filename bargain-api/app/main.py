from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.routers import auth, watchlist, waitlist, arbitrage, subscriptions, coupons, notifications, affiliate, community, gamification, seller, referrals
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

# Add CORS middleware — fail fast if ALLOWED_ORIGINS is misconfigured (no wildcard fallback)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security headers on all responses
@app.middleware("HTTP")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    return response

# Request body size limit (1MB) for non-file-upload endpoints
@app.middleware("HTTP")
async def limit_request_size(request: Request, call_next):
    if request.method in ("POST", "PUT", "PATCH"):
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > 1_000_000:  # 1MB
            return JSONResponse(status_code=413, content={"detail": "Request too large"})
    return await call_next(request)

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
app.include_router(gamification.router)
app.include_router(seller.router)
app.include_router(referrals.router)


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
