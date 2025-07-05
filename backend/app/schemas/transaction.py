from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum

from .base import BaseSchema, TimestampedSchema


class TransactionType(str, Enum):
    """Transaction types supported by the system."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    INTEREST = "interest"


class TransactionBase(BaseSchema):
    """Base transaction schema with common fields."""
    
    portfolio_id: int = Field(..., description="Portfolio ID")
    asset_id: int = Field(..., description="Asset ID")
    transaction_type: TransactionType = Field(..., description="Type of transaction")
    quantity: Decimal = Field(..., description="Quantity of assets")
    price: Decimal = Field(..., ge=0, description="Price per unit")
    total_amount: Decimal = Field(..., description="Total transaction amount")
    fees: Decimal = Field(default=Decimal('0'), ge=0, description="Transaction fees")
    transaction_date: datetime = Field(..., description="Date of transaction")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    @validator('quantity', 'price', 'total_amount', 'fees', pre=True)
    def validate_decimal(cls, v):
        if v is not None:
            return Decimal(str(v))
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        if 'quantity' in values and 'price' in values:
            calculated_total = values['quantity'] * values['price']
            if 'fees' in values:
                calculated_total += values['fees']
            if abs(v - calculated_total) > Decimal('0.01'):
                raise ValueError('Total amount does not match quantity * price + fees')
        return v


class TransactionCreate(TransactionBase):
    """Schema for creating a new transaction."""
    pass


class TransactionUpdate(BaseSchema):
    """Schema for updating a transaction."""
    
    quantity: Optional[Decimal] = None
    price: Optional[Decimal] = None
    total_amount: Optional[Decimal] = None
    fees: Optional[Decimal] = None
    transaction_date: Optional[datetime] = None
    notes: Optional[str] = None


class Transaction(TransactionBase, TimestampedSchema):
    """Full transaction schema with all fields."""
    
    id: int
    user_id: int
    
    class Config:
        from_attributes = True


class TransactionWithDetails(Transaction):
    """Transaction with asset and portfolio details."""
    
    asset_symbol: str
    asset_name: str
    portfolio_name: str


class TransactionResponse(BaseSchema):
    """Transaction response schema."""
    
    success: bool = True
    data: Transaction
    message: Optional[str] = None


class TransactionListResponse(BaseSchema):
    """Transaction list response schema."""
    
    success: bool = True
    data: List[TransactionWithDetails]
    total: int
    page: int = 1
    per_page: int = 50
    message: Optional[str] = None
