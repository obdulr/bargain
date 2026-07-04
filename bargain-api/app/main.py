from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="BargainHuntrs API",
    description="Arbitrage intelligence platform API",
    version="0.1.0",
)

# Add CORS middleware with fallback
try:
    from app.core.config import settings
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


@app.get("/")
async def root():
    return {
        "message": "BargainHuntrs API",
        "version": "0.1.0",
        "status": "operational"
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
