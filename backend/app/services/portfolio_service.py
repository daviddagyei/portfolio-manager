from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models import Portfolio as PortfolioModel, PortfolioHolding
from app.schemas import (
    PortfolioCreate, PortfolioUpdate, Portfolio, PortfolioSummary
)


class PortfolioService:
    """Service class for portfolio operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_portfolios(
        self,
        skip: int = 0,
        limit: int = 50,
        user_id: Optional[int] = None,
        portfolio_type: Optional[str] = None
    ) -> Tuple[List[Portfolio], int]:
        """Get portfolios with optional filtering."""
        query = self.db.query(PortfolioModel)
        
        # Apply filters
        if user_id:
            query = query.filter(PortfolioModel.user_id == user_id)
        if portfolio_type:
            query = query.filter(PortfolioModel.portfolio_type == portfolio_type)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        portfolios = query.offset(skip).limit(limit).all()
        
        return [Portfolio.from_orm(p) for p in portfolios], total
    
    async def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        """Get a specific portfolio by ID."""
        portfolio = self.db.query(PortfolioModel).filter(
            PortfolioModel.id == portfolio_id
        ).first()
        
        return Portfolio.from_orm(portfolio) if portfolio else None
    
    async def create_portfolio(self, portfolio_data: PortfolioCreate) -> Portfolio:
        """Create a new portfolio."""
        # For now, we'll use a default user_id (will be replaced with actual user in Phase 3)
        portfolio = PortfolioModel(
            **portfolio_data.dict(),
            user_id=1  # Placeholder user ID
        )
        
        self.db.add(portfolio)
        self.db.commit()
        self.db.refresh(portfolio)
        
        return Portfolio.from_orm(portfolio)
    
    async def update_portfolio(
        self, 
        portfolio_id: int, 
        portfolio_update: PortfolioUpdate
    ) -> Optional[Portfolio]:
        """Update a portfolio."""
        portfolio = self.db.query(PortfolioModel).filter(
            PortfolioModel.id == portfolio_id
        ).first()
        
        if not portfolio:
            return None
        
        update_data = portfolio_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(portfolio, field, value)
        
        self.db.commit()
        self.db.refresh(portfolio)
        
        return Portfolio.from_orm(portfolio)
    
    async def delete_portfolio(self, portfolio_id: int) -> bool:
        """Delete a portfolio."""
        portfolio = self.db.query(PortfolioModel).filter(
            PortfolioModel.id == portfolio_id
        ).first()
        
        if not portfolio:
            return False
        
        self.db.delete(portfolio)
        self.db.commit()
        
        return True
    
    async def get_portfolio_summary(self, portfolio_id: int) -> Optional[PortfolioSummary]:
        """Get portfolio summary with key metrics."""
        portfolio = self.db.query(PortfolioModel).filter(
            PortfolioModel.id == portfolio_id
        ).first()
        
        if not portfolio:
            return None
        
        # Count assets in portfolio
        asset_count = self.db.query(PortfolioHolding).filter(
            PortfolioHolding.portfolio_id == portfolio_id
        ).count()
        
        return PortfolioSummary(
            id=portfolio.id,
            name=portfolio.name,
            portfolio_type=portfolio.portfolio_type,
            current_value=portfolio.current_value,
            total_return=portfolio.total_return,
            total_return_percentage=portfolio.total_return_percentage,
            asset_count=asset_count,
            last_updated=portfolio.updated_at or portfolio.created_at
        )
