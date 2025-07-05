from sqlalchemy import Column, Integer, String, Text, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from .base import BaseModel


class AssetType(Enum):
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


class Asset(BaseModel):
    """Asset model for storing asset information."""
    
    __tablename__ = "assets"
    
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(SQLEnum(AssetType), nullable=False, index=True)
    sector = Column(String(100), nullable=True)
    industry = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    price_data = relationship("PriceData", back_populates="asset", cascade="all, delete-orphan")
    transactions = relationship("Transaction", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(symbol={self.symbol}, name={self.name})>"
