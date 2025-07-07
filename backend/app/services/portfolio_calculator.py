"""
Portfolio calculation engine for computing portfolio metrics and analytics.
"""

from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import structlog

from app.models import Portfolio, PortfolioHolding, Asset, PriceData
from app.schemas import PortfolioCalculationResult

logger = structlog.get_logger()


class PortfolioCalculationEngine:
    """
    Handles portfolio-level calculations including:
    - Current portfolio value
    - Total return calculations
    - Risk metrics
    - Asset allocation percentages
    - Performance analytics
    """

    def __init__(self):
        self.logger = logger

    def calculate_portfolio_value(self, holdings: List[PortfolioHolding]) -> Decimal:
        """Calculate the total current value of a portfolio."""
        try:
            total_value = Decimal('0')
            for holding in holdings:
                if holding.current_price and holding.quantity:
                    market_value = holding.current_price * holding.quantity
                    total_value += market_value
            return total_value
        except Exception as e:
            self.logger.error("Error calculating portfolio value", error=str(e))
            return Decimal('0')

    def calculate_total_return(self, holdings: List[PortfolioHolding]) -> Tuple[Decimal, Decimal]:
        """
        Calculate total return and return percentage.
        Returns: (total_return, return_percentage)
        """
        try:
            total_cost_basis = Decimal('0')
            total_market_value = Decimal('0')
            
            for holding in holdings:
                if holding.average_cost and holding.quantity:
                    cost_basis = holding.average_cost * holding.quantity
                    total_cost_basis += cost_basis
                    
                if holding.current_price and holding.quantity:
                    market_value = holding.current_price * holding.quantity
                    total_market_value += market_value
            
            total_return = total_market_value - total_cost_basis
            return_percentage = (
                (total_return / total_cost_basis) * 100 
                if total_cost_basis > 0 else Decimal('0')
            )
            
            return total_return, return_percentage
            
        except Exception as e:
            self.logger.error("Error calculating total return", error=str(e))
            return Decimal('0'), Decimal('0')

    def calculate_asset_allocation(self, holdings: List[PortfolioHolding]) -> Dict[str, Dict[str, Decimal]]:
        """
        Calculate asset allocation by type and sector.
        Returns: {
            'by_type': {'stock': value, 'bond': value, ...},
            'by_sector': {'technology': value, 'healthcare': value, ...}
        }
        """
        try:
            allocation_by_type = {}
            allocation_by_sector = {}
            total_value = Decimal('0')
            
            for holding in holdings:
                if holding.current_price and holding.quantity:
                    market_value = holding.current_price * holding.quantity
                    total_value += market_value
                    
                    # Group by asset type
                    if hasattr(holding, 'asset') and holding.asset:
                        asset_type = holding.asset.asset_type or 'other'
                        allocation_by_type[asset_type] = allocation_by_type.get(asset_type, Decimal('0')) + market_value
                        
                        # Group by sector
                        sector = holding.asset.sector or 'other'
                        allocation_by_sector[sector] = allocation_by_sector.get(sector, Decimal('0')) + market_value
            
            # Convert to percentages
            if total_value > 0:
                for asset_type in allocation_by_type:
                    allocation_by_type[asset_type] = (allocation_by_type[asset_type] / total_value) * 100
                    
                for sector in allocation_by_sector:
                    allocation_by_sector[sector] = (allocation_by_sector[sector] / total_value) * 100
            
            return {
                'by_type': allocation_by_type,
                'by_sector': allocation_by_sector
            }
            
        except Exception as e:
            self.logger.error("Error calculating asset allocation", error=str(e))
            return {'by_type': {}, 'by_sector': {}}

    def calculate_holding_metrics(self, holding: PortfolioHolding) -> Dict[str, Decimal]:
        """Calculate metrics for a single holding."""
        try:
            metrics = {
                'market_value': Decimal('0'),
                'cost_basis': Decimal('0'),
                'unrealized_gain_loss': Decimal('0'),
                'unrealized_gain_loss_percentage': Decimal('0'),
                'weight': Decimal('0')
            }
            
            if holding.current_price and holding.quantity:
                metrics['market_value'] = holding.current_price * holding.quantity
                
            if holding.average_cost and holding.quantity:
                metrics['cost_basis'] = holding.average_cost * holding.quantity
                
            metrics['unrealized_gain_loss'] = metrics['market_value'] - metrics['cost_basis']
            
            if metrics['cost_basis'] > 0:
                metrics['unrealized_gain_loss_percentage'] = (
                    metrics['unrealized_gain_loss'] / metrics['cost_basis']
                ) * 100
            
            return metrics
            
        except Exception as e:
            self.logger.error("Error calculating holding metrics", holding_id=holding.id, error=str(e))
            return {
                'market_value': Decimal('0'),
                'cost_basis': Decimal('0'),
                'unrealized_gain_loss': Decimal('0'),
                'unrealized_gain_loss_percentage': Decimal('0'),
                'weight': Decimal('0')
            }

    def calculate_portfolio_metrics(self, portfolio: Portfolio, holdings: List[PortfolioHolding]) -> Dict:
        """Calculate comprehensive portfolio metrics."""
        try:
            current_value = self.calculate_portfolio_value(holdings)
            total_return, return_percentage = self.calculate_total_return(holdings)
            allocation = self.calculate_asset_allocation(holdings)
            
            metrics = {
                'current_value': current_value,
                'total_return': total_return,
                'return_percentage': return_percentage,
                'asset_count': len(holdings),
                'allocation': allocation,
                'last_updated': datetime.utcnow()
            }
            
            return metrics
            
        except Exception as e:
            self.logger.error("Error calculating portfolio metrics", portfolio_id=portfolio.id, error=str(e))
            return {
                'current_value': Decimal('0'),
                'total_return': Decimal('0'),
                'return_percentage': Decimal('0'),
                'asset_count': 0,
                'allocation': {'by_type': {}, 'by_sector': {}},
                'last_updated': datetime.utcnow()
            }

    def update_holding_calculations(self, holding: PortfolioHolding) -> PortfolioHolding:
        """Update calculated fields for a holding."""
        try:
            metrics = self.calculate_holding_metrics(holding)
            
            holding.market_value = metrics['market_value']
            holding.unrealized_gain_loss = metrics['unrealized_gain_loss']
            holding.unrealized_gain_loss_percentage = metrics['unrealized_gain_loss_percentage']
            
            return holding
            
        except Exception as e:
            self.logger.error("Error updating holding calculations", holding_id=holding.id, error=str(e))
            return holding

    def calculate_diversification_score(self, holdings: List[PortfolioHolding]) -> Decimal:
        """
        Calculate a diversification score based on asset allocation.
        Returns a score between 0 and 100.
        """
        try:
            allocation = self.calculate_asset_allocation(holdings)
            
            # Calculate Herfindahl-Hirschman Index for concentration
            hhi_type = sum(
                (percentage / 100) ** 2 
                for percentage in allocation['by_type'].values()
            )
            
            hhi_sector = sum(
                (percentage / 100) ** 2 
                for percentage in allocation['by_sector'].values()
            )
            
            # Convert to diversification score (inverse of concentration)
            diversification_score = (1 - (hhi_type + hhi_sector) / 2) * 100
            
            return Decimal(str(max(0, min(100, diversification_score))))
            
        except Exception as e:
            self.logger.error("Error calculating diversification score", error=str(e))
            return Decimal('0')


# Global instance
portfolio_calculator = PortfolioCalculationEngine()
