from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .base import BaseSchema, TimestampedSchema
from .portfolio import PortfolioSummary


class PortfolioHoldingBase(BaseSchema):
    """Base portfolio holding schema with common fields."""
    
    portfolio_id: int = Field(..., description="Portfolio ID")
    asset_id: int = Field(..., description="Asset ID")
    quantity: Decimal = Field(..., description="Quantity held")
    average_cost: Decimal = Field(..., ge=0, description="Average cost per unit")
    current_price: Optional[Decimal] = Field(None, ge=0, description="Current market price")
    
    @validator('quantity', 'average_cost', 'current_price', pre=True)
    def validate_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v


class PortfolioHoldingCreate(PortfolioHoldingBase):
    """Schema for creating a new portfolio holding."""
    pass


class PortfolioHoldingUpdate(BaseSchema):
    """Schema for updating a portfolio holding."""
    
    quantity: Optional[Decimal] = None
    average_cost: Optional[Decimal] = None
    current_price: Optional[Decimal] = None


class PortfolioHolding(PortfolioHoldingBase, TimestampedSchema):
    """Full portfolio holding schema with all fields."""
    
    id: int
    market_value: Decimal = Field(default=Decimal('0'), description="Current market value")
    unrealized_gain_loss: Decimal = Field(default=Decimal('0'), description="Unrealized gain/loss")
    unrealized_gain_loss_percentage: Decimal = Field(default=Decimal('0'), description="Unrealized gain/loss percentage")
    
    class Config:
        from_attributes = True


class PortfolioHoldingWithAsset(PortfolioHolding):
    """Portfolio holding with asset details."""
    
    asset_symbol: str
    asset_name: str
    asset_type: str
    sector: Optional[str] = None


class PortfolioHoldingResponse(BaseSchema):
    """Portfolio holding response schema."""
    
    success: bool = True
    data: PortfolioHolding
    message: Optional[str] = None


class PortfolioHoldingListResponse(BaseSchema):
    """Portfolio holding list response schema."""
    
    success: bool = True
    data: List[PortfolioHoldingWithAsset]
    total: int
    page: int = 1
    per_page: int = 50
    message: Optional[str] = None


class PortfolioAllocation(BaseSchema):
    """Portfolio allocation schema."""
    
    portfolio_id: int
    total_value: Decimal
    by_asset: List[Dict]
    by_sector: Dict
    by_asset_type: Dict
    
    
class PortfolioPerformanceMetrics(BaseSchema):
    """Portfolio performance metrics schema."""
    
    portfolio_id: int
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    total_return: Decimal
    annualized_return: Decimal
    volatility: Decimal
    sharpe_ratio: Decimal
    max_drawdown: Decimal
    data_points: int


class PortfolioCalculationResult(BaseSchema):
    """Portfolio calculation result schema."""
    
    portfolio_id: int
    current_value: Decimal
    initial_value: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    total_unrealized_gain_loss: Decimal
    total_cost_basis: Decimal
    holdings_count: int
    holdings: List[Dict]
    last_updated: datetime


class PortfolioImportResult(BaseSchema):
    """Portfolio import result schema."""
    
    success: bool
    total_parsed: int
    errors: List[Dict]
    error_count: int
    message: Optional[str] = None


class PortfolioHistoryEntry(BaseSchema):
    """Portfolio history entry schema."""
    
    date: str
    value: Decimal
    return_amount: Decimal
    return_percentage: Decimal
    cash_flows: Decimal
    holdings_count: int


class PortfolioHistoryResponse(BaseSchema):
    """Portfolio history response schema."""
    
    success: bool = True
    data: List[PortfolioHistoryEntry]
    total: int
    message: Optional[str] = None


class PortfolioComparisonResult(BaseSchema):
    """Portfolio comparison result schema."""
    
    start_date: str
    end_date: str
    portfolios: Dict


class PortfolioAggregation(BaseSchema):
    """Portfolio aggregation schema for multiple portfolios."""
    
    user_id: int
    total_portfolios: int
    total_value: Decimal
    total_initial_value: Decimal
    total_return: Decimal
    total_return_percentage: Decimal
    portfolios: List[PortfolioSummary]


class PortfolioTaskResult(BaseSchema):
    """Portfolio background task result schema."""
    
    success: bool
    timestamp: str
    message: Optional[str] = None
    data: Optional[Dict] = None
    error: Optional[str] = None
