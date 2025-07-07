from sqlalchemy import Column, Integer, DECIMAL, Date, ForeignKey
from sqlalchemy.orm import relationship

from .base import BaseModel


class PortfolioHistory(BaseModel):
    """Model for tracking portfolio value history."""
    
    __tablename__ = "portfolio_history"
    
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    value = Column(DECIMAL(15, 2), nullable=False)
    return_amount = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    return_percentage = Column(DECIMAL(5, 2), nullable=False, default=0.00)
    cash_flows = Column(DECIMAL(15, 2), nullable=False, default=0.00)
    holdings_count = Column(Integer, nullable=False, default=0)
    
    # Relationships
    portfolio = relationship("Portfolio")
    
    def __repr__(self):
        return f"<PortfolioHistory(portfolio_id={self.portfolio_id}, date={self.date}, value={self.value})>"
