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
        "http://localhost:8000",  # FastAPI docs
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    DATABASE_URL: Optional[str] = None
    POSTGRES_SERVER: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
    POSTGRES_DB: Optional[str] = None
    
    @validator("DATABASE_URL", pre=True)
    def assemble_db_connection(cls, v, values):
        if isinstance(v, str):
            return v
        return (
            f"postgresql://{values.get('POSTGRES_USER')}:"
            f"{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/"
            f"{values.get('POSTGRES_DB')}"
        )
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379"
    
    # Security settings
    SECRET_KEY: str = "your-secret-key-here-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ALGORITHM: str = "HS256"
    
    # External API settings
    YAHOO_FINANCE_TIMEOUT: int = 10
    PRICE_CACHE_TIMEOUT: int = 300  # 5 minutes
    
    # Background task settings
    PRICE_UPDATE_INTERVAL: int = 60  # seconds
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    
    # Development settings
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
