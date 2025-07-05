from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
from enum import Enum

from .base import BaseModel


class TransactionType(Enum):
    """Transaction types supported by the system."""
    BUY = "buy"
    SELL = "sell"
    DIVIDEND = "dividend"
    SPLIT = "split"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    FEE = "fee"
    INTEREST = "interest"


class Transaction(BaseModel):
    """Transaction model for storing transaction records."""
    
    __tablename__ = "transactions"
    
    user_id = Column(Integer, nullable=False, index=True)  # Will be linked to User model in Phase 3
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    transaction_type = Column(SQLEnum(TransactionType), nullable=False, index=True)
    quantity = Column(DECIMAL(15, 6), nullable=False)
    price = Column(DECIMAL(15, 4), nullable=False)
    total_amount = Column(DECIMAL(15, 2), nullable=False)
    fees = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    transaction_date = Column(DateTime, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="transactions")
    asset = relationship("Asset", back_populates="transactions")
    
    def __repr__(self):
        return f"<Transaction(type={self.transaction_type}, asset_id={self.asset_id}, quantity={self.quantity})>"
