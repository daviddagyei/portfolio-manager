from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .base import BaseSchema, TimestampedSchema


class AssetType(str, Enum):
    """Asset types supported by the system."""
    STOCK = "stock"
    BOND = "bond"
    ETF = "etf"
    MUTUAL_FUND = "mutual_fund"
    CRYPTOCURRENCY = "cryptocurrency"
    COMMODITY = "commodity"
    REAL_ESTATE = "real_estate"
    CASH = "cash"
    OTHER = "other"


class AssetBase(BaseSchema):
    """Base asset schema with common fields."""
    
    symbol: str = Field(..., description="Asset symbol (e.g., AAPL, BTC)")
    name: str = Field(..., description="Full asset name")
    asset_type: AssetType = Field(..., description="Type of asset")
    sector: Optional[str] = Field(None, description="Asset sector")
    industry: Optional[str] = Field(None, description="Asset industry")
    description: Optional[str] = Field(None, description="Asset description")
    
    @validator('symbol')
    def validate_symbol(cls, v):
        return v.upper().strip()


class AssetCreate(AssetBase):
    """Schema for creating a new asset."""
    pass


class AssetUpdate(BaseSchema):
    """Schema for updating an asset."""
    
    name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    description: Optional[str] = None


class Asset(AssetBase, TimestampedSchema):
    """Full asset schema with all fields."""
    
    id: int
    is_active: bool = True
    
    class Config:
        from_attributes = True


class AssetResponse(BaseSchema):
    """Asset response schema."""
    
    success: bool = True
    data: Asset
    message: Optional[str] = None


class AssetListResponse(BaseSchema):
    """Asset list response schema."""
    
    success: bool = True
    data: List[Asset]
    total: int
    page: int = 1
    per_page: int = 50
    message: Optional[str] = None
