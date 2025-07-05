from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

from .base import BaseSchema, TimestampedSchema


class PriceDataBase(BaseSchema):
    """Base price data schema with common fields."""
    
    asset_id: int = Field(..., description="Asset ID")
    date: datetime = Field(..., description="Price date")
    open_price: Decimal = Field(..., ge=0, description="Opening price")
    high_price: Decimal = Field(..., ge=0, description="High price")
    low_price: Decimal = Field(..., ge=0, description="Low price")
    close_price: Decimal = Field(..., ge=0, description="Closing price")
    volume: Optional[int] = Field(None, ge=0, description="Trading volume")
    adjusted_close: Optional[Decimal] = Field(None, ge=0, description="Adjusted closing price")
    
    @validator('open_price', 'high_price', 'low_price', 'close_price', 'adjusted_close', pre=True)
    def validate_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v
    
    @validator('high_price')
    def validate_high_price(cls, v, values):
        if 'low_price' in values and v < values['low_price']:
            raise ValueError('High price cannot be less than low price')
        return v
    
    @validator('close_price')
    def validate_close_price(cls, v, values):
        if 'high_price' in values and 'low_price' in values:
            if v > values['high_price'] or v < values['low_price']:
                raise ValueError('Close price must be between high and low prices')
        return v


class PriceDataCreate(PriceDataBase):
    """Schema for creating new price data."""
    pass


class PriceDataUpdate(BaseSchema):
    """Schema for updating price data."""
    
    open_price: Optional[Decimal] = None
    high_price: Optional[Decimal] = None
    low_price: Optional[Decimal] = None
    close_price: Optional[Decimal] = None
    volume: Optional[int] = None
    adjusted_close: Optional[Decimal] = None


class PriceData(PriceDataBase, TimestampedSchema):
    """Full price data schema with all fields."""
    
    id: int
    
    class Config:
        from_attributes = True


class PriceDataWithAsset(PriceData):
    """Price data with asset details."""
    
    asset_symbol: str
    asset_name: str


class PriceDataResponse(BaseSchema):
    """Price data response schema."""
    
    success: bool = True
    data: PriceData
    message: Optional[str] = None


class PriceDataListResponse(BaseSchema):
    """Price data list response schema."""
    
    success: bool = True
    data: List[PriceDataWithAsset]
    total: int
    page: int = 1
    per_page: int = 50
    message: Optional[str] = None


class PriceHistoryRequest(BaseSchema):
    """Request schema for price history."""
    
    asset_id: int
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    period: Optional[str] = Field(default="1y", description="Period: 1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max")


class PriceHistoryResponse(BaseSchema):
    """Price history response schema."""
    
    success: bool = True
    data: List[PriceData]
    asset_symbol: str
    asset_name: str
    period: str
    total_records: int
    message: Optional[str] = None
