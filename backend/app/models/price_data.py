from sqlalchemy import Column, Integer, DateTime, DECIMAL, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from .base import BaseModel


class PriceData(BaseModel):
    """Price data model for storing historical and real-time price information."""
    
    __tablename__ = "price_data"
    
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    open_price = Column(DECIMAL(15, 4), nullable=False)
    high_price = Column(DECIMAL(15, 4), nullable=False)
    low_price = Column(DECIMAL(15, 4), nullable=False)
    close_price = Column(DECIMAL(15, 4), nullable=False)
    volume = Column(Integer, nullable=True)
    adjusted_close = Column(DECIMAL(15, 4), nullable=True)
    
    # Relationships
    asset = relationship("Asset", back_populates="price_data")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('asset_id', 'date', name='uix_asset_date'),
    )
    
    def __repr__(self):
        return f"<PriceData(asset_id={self.asset_id}, date={self.date}, close={self.close_price})>"
