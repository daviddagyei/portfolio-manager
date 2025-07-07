from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
from decimal import Decimal
import structlog

from app.models import Portfolio as PortfolioModel, PortfolioHolding
from app.schemas import (
    PortfolioCreate, PortfolioUpdate, Portfolio, PortfolioSummary
)

logger = structlog.get_logger()


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
    
    async def get_portfolio_holdings(self, portfolio_id: int) -> List[Dict]:
        """Get all holdings for a portfolio with detailed information."""
        try:
            from app.models import PortfolioHolding, Asset as AssetModel
            
            holdings_query = self.db.query(
                PortfolioHolding,
                AssetModel.symbol,
                AssetModel.name,
                AssetModel.asset_type,
                AssetModel.sector
            ).join(
                AssetModel, PortfolioHolding.asset_id == AssetModel.id
            ).filter(
                PortfolioHolding.portfolio_id == portfolio_id
            )
            
            holdings = holdings_query.all()
            
            result = []
            for holding, symbol, name, asset_type, sector in holdings:
                result.append({
                    'holding_id': holding.id,
                    'asset_id': holding.asset_id,
                    'asset_symbol': symbol,
                    'asset_name': name,
                    'asset_type': asset_type,
                    'sector': sector,
                    'quantity': holding.quantity,
                    'average_cost': holding.average_cost,
                    'current_price': holding.current_price,
                    'market_value': holding.market_value,
                    'unrealized_gain_loss': holding.unrealized_gain_loss,
                    'unrealized_gain_loss_percentage': holding.unrealized_gain_loss_percentage,
                    'last_updated': holding.updated_at or holding.created_at
                })
            
            return result
            
        except Exception as e:
            logger.error("Error getting portfolio holdings", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def update_portfolio_holding(
        self, 
        portfolio_id: int, 
        asset_id: int, 
        quantity: Decimal, 
        current_price: Optional[Decimal] = None
    ) -> Dict:
        """Update a specific portfolio holding."""
        try:
            from app.models import PortfolioHolding
            
            holding = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.asset_id == asset_id
            ).first()
            
            if not holding:
                raise ValueError(f"Holding not found for portfolio {portfolio_id} and asset {asset_id}")
            
            # Update holding
            holding.quantity = quantity
            if current_price:
                holding.current_price = current_price
                holding.market_value = quantity * current_price
                
                # Recalculate unrealized gain/loss
                cost_basis = quantity * holding.average_cost
                holding.unrealized_gain_loss = holding.market_value - cost_basis
                
                if cost_basis > 0:
                    holding.unrealized_gain_loss_percentage = (
                        holding.unrealized_gain_loss / cost_basis
                    ) * 100
                else:
                    holding.unrealized_gain_loss_percentage = Decimal('0')
            
            self.db.commit()
            self.db.refresh(holding)
            
            return {
                'holding_id': holding.id,
                'portfolio_id': portfolio_id,
                'asset_id': asset_id,
                'quantity': holding.quantity,
                'current_price': holding.current_price,
                'market_value': holding.market_value,
                'unrealized_gain_loss': holding.unrealized_gain_loss,
                'unrealized_gain_loss_percentage': holding.unrealized_gain_loss_percentage
            }
            
        except Exception as e:
            logger.error("Error updating portfolio holding", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def get_portfolio_aggregation(self, user_id: int) -> Dict:
        """Get aggregated portfolio data across all portfolios for a user."""
        try:
            # Get all portfolios for the user
            portfolios = self.db.query(PortfolioModel).filter(
                PortfolioModel.user_id == user_id,
                PortfolioModel.is_active == True
            ).all()
            
            if not portfolios:
                return {
                    'user_id': user_id,
                    'total_portfolios': 0,
                    'total_value': Decimal('0'),
                    'total_return': Decimal('0'),
                    'total_return_percentage': Decimal('0'),
                    'portfolios': []
                }
            
            # Calculate aggregated metrics
            total_value = sum(p.current_value for p in portfolios)
            total_initial_value = sum(p.initial_value for p in portfolios)
            total_return = sum(p.total_return for p in portfolios)
            
            total_return_percentage = (
                (total_return / total_initial_value) * 100 
                if total_initial_value > 0 else Decimal('0')
            )
            
            # Get portfolio summaries
            portfolio_summaries = []
            for portfolio in portfolios:
                summary = await self.get_portfolio_summary(portfolio.id)
                if summary:
                    portfolio_summaries.append(summary)
            
            return {
                'user_id': user_id,
                'total_portfolios': len(portfolios),
                'total_value': total_value,
                'total_initial_value': total_initial_value,
                'total_return': total_return,
                'total_return_percentage': total_return_percentage,
                'portfolios': portfolio_summaries
            }
            
        except Exception as e:
            logger.error("Error getting portfolio aggregation", user_id=user_id, error=str(e))
            raise
