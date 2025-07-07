from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Settings(BaseSettings):
    """Application settings."""
    
    # Project information
    PROJECT_NAME: str = "Portfolio Manager API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A comprehensive portfolio and asset management dashboard API"
    
    # API settings
    API_V1_STR: str = "/api/v1"
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",  # React dev server
        "http://localhost:3030",  # React dev server (new port)
        "http://localhost:8000",  # FastAPI docs
        "http://localhost:8001",  # FastAPI backend
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3030",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    DATABASE_URL: str = Field(
        default="sqlite:///./portfolio_manager.db",
        description="Database connection URL"
    )
    
    # Security settings
    SECRET_KEY: str = Field(
        default="your-secret-key-here-change-in-production",
        description="Secret key for JWT tokens"
    )
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # External API settings
    ALPHA_VANTAGE_API_KEY: Optional[str] = Field(
        default=None,
        description="Alpha Vantage API key for market data"
    )
    YAHOO_FINANCE_ENABLED: bool = Field(
        default=True,
        description="Enable Yahoo Finance for market data"
    )
    
    # Application settings
    DEBUG: bool = Field(default=False, description="Debug mode")
    TESTING: bool = Field(default=False, description="Testing mode")
    
    # Pagination settings
    DEFAULT_PAGE_SIZE: int = 50
    MAX_PAGE_SIZE: int = 1000
    
    # Cache settings
    REDIS_URL: Optional[str] = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL for caching and tasks"
    )
    CACHE_TTL: int = Field(
        default=3600,
        description="Cache TTL in seconds"
    )
    
    # Market Data Settings
    MARKET_DATA_PROVIDER: str = Field(
        default="yahoo",
        description="Default market data provider"
    )
    MARKET_DATA_RATE_LIMIT: int = Field(
        default=5,
        description="Market data API rate limit (requests per second)"
    )
    MARKET_DATA_TIMEOUT: int = Field(
        default=30,
        description="Market data API timeout in seconds"
    )
    
    # Background Task Settings
    CELERY_BROKER_URL: Optional[str] = Field(
        default=None,
        description="Celery broker URL (defaults to REDIS_URL)"
    )
    CELERY_RESULT_BACKEND: Optional[str] = Field(
        default=None,
        description="Celery result backend URL (defaults to REDIS_URL)"
    )
    
    @property
    def celery_broker_url(self) -> str:
        return self.CELERY_BROKER_URL or self.REDIS_URL or "redis://localhost:6379/0"
    
    @property
    def celery_result_backend(self) -> str:
        return self.CELERY_RESULT_BACKEND or self.REDIS_URL or "redis://localhost:6379/0"
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
