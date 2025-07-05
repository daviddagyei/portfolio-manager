from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .base import BaseSchema, TimestampedSchema


class PortfolioType(str, Enum):
    """Portfolio types supported by the system."""
    PERSONAL = "personal"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    INVESTMENT = "investment"
    TRADING = "trading"
    OTHER = "other"


class PortfolioBase(BaseSchema):
    """Base portfolio schema with common fields."""
    
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    portfolio_type: PortfolioType = Field(..., description="Type of portfolio")
    initial_value: Decimal = Field(..., ge=0, description="Initial portfolio value")
    target_return: Optional[Decimal] = Field(None, ge=0, le=100, description="Target return percentage")
    risk_tolerance: Optional[str] = Field(None, description="Risk tolerance level")
    
    @validator('initial_value', 'target_return', pre=True)
    def validate_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class PortfolioCreate(PortfolioBase):
    """Schema for creating a new portfolio."""
    pass


class PortfolioUpdate(BaseSchema):
    """Schema for updating a portfolio."""
    
    name: Optional[str] = None
    description: Optional[str] = None
    portfolio_type: Optional[PortfolioType] = None
    target_return: Optional[Decimal] = None
    risk_tolerance: Optional[str] = None


class Portfolio(PortfolioBase, TimestampedSchema):
    """Full portfolio schema with all fields."""
    
    id: int
    user_id: int
    current_value: Decimal = Field(default=Decimal('0'), description="Current portfolio value")
    total_return: Decimal = Field(default=Decimal('0'), description="Total return")
    total_return_percentage: Decimal = Field(default=Decimal('0'), description="Total return percentage")
    is_active: bool = True
    
    class Config:
        from_attributes = True


class PortfolioSummary(BaseSchema):
    """Portfolio summary with key metrics."""
    
    id: int
    name: str
    portfolio_type: PortfolioType
    current_value: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    asset_count: int
    last_updated: datetime


class PortfolioResponse(BaseSchema):
    """Portfolio response schema."""
    
    success: bool = True
    data: Portfolio
    message: Optional[str] = None


class PortfolioListResponse(BaseSchema):
    """Portfolio list response schema."""
    
    success: bool = True
    data: List[Portfolio]
    total: int
    page: int = 1
    per_page: int = 50
    message: Optional[str] = None
