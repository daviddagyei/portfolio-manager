from sqlalchemy import Column, Integer, String, Text, Boolean, Enum as SQLEnum, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from enum import Enum

from .base import BaseModel


class PortfolioType(Enum):
    """Portfolio types supported by the system."""
    PERSONAL = "personal"
    RETIREMENT = "retirement"
    EDUCATION = "education"
    INVESTMENT = "investment"
    TRADING = "trading"
    OTHER = "other"


class Portfolio(BaseModel):
    """Portfolio model for storing portfolio information."""
    
    __tablename__ = "portfolios"
    
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    portfolio_type = Column(SQLEnum(PortfolioType), nullable=False)
    user_id = Column(Integer, nullable=False, index=True)  # Will be linked to User model in Phase 3
    initial_value = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    current_value = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    total_return = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    total_return_percentage = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    target_return = Column(DECIMAL(5, 2), nullable=True)
    risk_tolerance = Column(String(20), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="portfolio", cascade="all, delete-orphan")
    holdings = relationship("PortfolioHolding", back_populates="portfolio", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Portfolio(name={self.name}, user_id={self.user_id})>"


class PortfolioHolding(BaseModel):
    """Portfolio holding model for tracking asset positions."""
    
    __tablename__ = "portfolio_holdings"
    
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    quantity = Column(DECIMAL(15, 6), nullable=False, default=0.0)
    average_cost = Column(DECIMAL(15, 4), nullable=False, default=0.0)
    current_price = Column(DECIMAL(15, 4), nullable=True)
    market_value = Column(DECIMAL(15, 2), nullable=False, default=0.0)
    unrealized_gain_loss = Column(DECIMAL(15, 2), nullable=False, default=0.0)
    unrealized_gain_loss_percentage = Column(DECIMAL(5, 2), nullable=False, default=0.0)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="holdings")
    asset = relationship("Asset")
    
    def __repr__(self):
        return f"<PortfolioHolding(portfolio_id={self.portfolio_id}, asset_id={self.asset_id}, quantity={self.quantity})>"
