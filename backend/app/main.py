from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import structlog
from pydantic import ValidationError

from app.core.config import settings
from app.core.database import init_db
from app.api.v1.api import api_router
from app.utils.exceptions import (
    APIException,
    api_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    general_exception_handler
)

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events."""
    logger.info("Portfolio Manager API starting up...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Failed to initialize database", error=str(e))
        raise
    
    yield
    
    # Shutdown logic here
    logger.info("Portfolio Manager API shutting down...")


def create_application() -> FastAPI:
    """Create FastAPI application with all configurations."""
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="A comprehensive portfolio and asset management dashboard API",
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Set up CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": settings.PROJECT_NAME,
            "version": settings.VERSION
        }

    return app


# Create the FastAPI application
app = create_application()


# Exception handlers
@app.exception_handler(APIException)
async def handle_api_exception(request, exc: APIException):
    return await api_exception_handler(request, exc)

@app.exception_handler(ValidationError)
async def handle_validation_error(request, exc: ValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(RequestValidationError)
async def handle_request_validation_error(request, exc: RequestValidationError):
    return await validation_exception_handler(request, exc)

@app.exception_handler(Exception)
async def handle_exception(request, exc: Exception):
    return await general_exception_handler(request, exc)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
