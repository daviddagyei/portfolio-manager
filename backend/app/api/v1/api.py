from fastapi import APIRouter

from app.api.v1.endpoints import portfolios, market_data, analytics, optimization, assets

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    assets.router,
    prefix="/assets",
    tags=["assets"]
)

api_router.include_router(
    portfolios.router,
    prefix="/portfolios",
    tags=["portfolios"]
)

api_router.include_router(
    market_data.router,
    prefix="/market-data",
    tags=["market-data"]
)

api_router.include_router(
    analytics.router,
    prefix="/analytics",
    tags=["analytics"]
)

api_router.include_router(
    optimization.router,
    prefix="/optimization",
    tags=["optimization"]
)


@api_router.get("/")
async def root():
    """API root endpoint."""
    return {
        "message": "Portfolio Manager API v1",
        "docs": "/docs",
        "redoc": "/redoc"
    }
