from typing import List, Dict, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, date, timedelta
from decimal import Decimal
import structlog

from app.models import (
    Portfolio as PortfolioModel,
    PortfolioHolding,
    Transaction as TransactionModel,
    Asset as AssetModel,
    PriceData as PriceDataModel
)
from app.schemas import Portfolio, PortfolioSummary

logger = structlog.get_logger()


class PortfolioCalculationEngine:
    """Engine for portfolio calculations and performance metrics."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def calculate_portfolio_values(self, portfolio_id: int) -> Dict:
        """Calculate current portfolio values and performance metrics."""
        try:
            # Get portfolio
            portfolio = self.db.query(PortfolioModel).filter(
                PortfolioModel.id == portfolio_id
            ).first()
            
            if not portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
            
            # Get all holdings
            holdings = self.db.query(PortfolioHolding).filter(
                PortfolioHolding.portfolio_id == portfolio_id
            ).all()
            
            # Calculate current values
            current_value = Decimal('0')
            total_cost = Decimal('0')
            total_unrealized_gain_loss = Decimal('0')
            
            holding_details = []
            
            for holding in holdings:
                # Get latest price for the asset
                latest_price = await self._get_latest_price(holding.asset_id)
                
                if latest_price:
                    holding.current_price = latest_price
                    holding.market_value = holding.quantity * latest_price
                else:
                    holding.market_value = holding.quantity * holding.average_cost
                
                # Calculate unrealized gain/loss
                cost_basis = holding.quantity * holding.average_cost
                holding.unrealized_gain_loss = holding.market_value - cost_basis
                
                if cost_basis > 0:
                    holding.unrealized_gain_loss_percentage = (
                        holding.unrealized_gain_loss / cost_basis
                    ) * 100
                else:
                    holding.unrealized_gain_loss_percentage = Decimal('0')
                
                # Update holding in database
                self.db.merge(holding)
                
                # Add to totals
                current_value += holding.market_value
                total_cost += cost_basis
                total_unrealized_gain_loss += holding.unrealized_gain_loss
                
                # Add to holding details
                asset = self.db.query(AssetModel).filter(
                    AssetModel.id == holding.asset_id
                ).first()
                
                holding_details.append({
                    'asset_id': holding.asset_id,
                    'asset_symbol': asset.symbol if asset else '',
                    'asset_name': asset.name if asset else '',
                    'quantity': holding.quantity,
                    'average_cost': holding.average_cost,
                    'current_price': holding.current_price,
                    'market_value': holding.market_value,
                    'unrealized_gain_loss': holding.unrealized_gain_loss,
                    'unrealized_gain_loss_percentage': holding.unrealized_gain_loss_percentage
                })
            
            # Calculate portfolio-level metrics
            total_return = current_value - portfolio.initial_value
            total_return_percentage = (
                (total_return / portfolio.initial_value) * 100 
                if portfolio.initial_value > 0 else Decimal('0')
            )
            
            # Update portfolio values
            portfolio.current_value = current_value
            portfolio.total_return = total_return
            portfolio.total_return_percentage = total_return_percentage
            
            self.db.commit()
            
            return {
                'portfolio_id': portfolio_id,
                'current_value': current_value,
                'initial_value': portfolio.initial_value,
                'total_return': total_return,
                'total_return_percentage': total_return_percentage,
                'total_unrealized_gain_loss': total_unrealized_gain_loss,
                'total_cost_basis': total_cost,
                'holdings_count': len(holdings),
                'holdings': holding_details,
                'last_updated': datetime.now()
            }
            
        except Exception as e:
            logger.error("Error calculating portfolio values", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def calculate_portfolio_performance(
        self, 
        portfolio_id: int, 
        start_date: Optional[date] = None, 
        end_date: Optional[date] = None
    ) -> Dict:
        """Calculate portfolio performance metrics over a time period."""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=365)  # Default to 1 year
            if not end_date:
                end_date = date.today()
            
            # Get portfolio
            portfolio = self.db.query(PortfolioModel).filter(
                PortfolioModel.id == portfolio_id
            ).first()
            
            if not portfolio:
                raise ValueError(f"Portfolio with ID {portfolio_id} not found")
            
            # Get transactions in the period
            transactions = self.db.query(TransactionModel).filter(
                and_(
                    TransactionModel.portfolio_id == portfolio_id,
                    TransactionModel.transaction_date >= start_date,
                    TransactionModel.transaction_date <= end_date
                )
            ).all()
            
            # Calculate cash flows
            cash_flows = []
            total_inflows = Decimal('0')
            total_outflows = Decimal('0')
            
            for transaction in transactions:
                if transaction.transaction_type in ['buy', 'transfer_in']:
                    total_inflows += transaction.total_amount
                    cash_flows.append({
                        'date': transaction.transaction_date,
                        'amount': transaction.total_amount,
                        'type': 'inflow'
                    })
                elif transaction.transaction_type in ['sell', 'transfer_out']:
                    total_outflows += transaction.total_amount
                    cash_flows.append({
                        'date': transaction.transaction_date,
                        'amount': -transaction.total_amount,
                        'type': 'outflow'
                    })
            
            # Calculate current values
            current_values = await self.calculate_portfolio_values(portfolio_id)
            
            # Calculate basic performance metrics
            net_cash_flow = total_inflows - total_outflows
            current_value = current_values['current_value']
            
            # Simple return calculation
            if total_inflows > 0:
                total_return = (current_value + total_outflows - total_inflows) / total_inflows
                annualized_return = ((1 + total_return) ** (365 / (end_date - start_date).days)) - 1
            else:
                total_return = Decimal('0')
                annualized_return = Decimal('0')
            
            return {
                'portfolio_id': portfolio_id,
                'start_date': start_date,
                'end_date': end_date,
                'current_value': current_value,
                'total_inflows': total_inflows,
                'total_outflows': total_outflows,
                'net_cash_flow': net_cash_flow,
                'total_return': total_return,
                'annualized_return': annualized_return,
                'cash_flows': cash_flows,
                'transaction_count': len(transactions)
            }
            
        except Exception as e:
            logger.error("Error calculating portfolio performance", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def get_portfolio_allocation(self, portfolio_id: int) -> Dict:
        """Get portfolio allocation by asset, sector, and asset type."""
        try:
            # Get all holdings with asset information
            holdings_query = self.db.query(
                PortfolioHolding,
                AssetModel.symbol,
                AssetModel.name,
                AssetModel.asset_type,
                AssetModel.sector
            ).join(
                AssetModel, PortfolioHolding.asset_id == AssetModel.id
            ).filter(
                PortfolioHolding.portfolio_id == portfolio_id,
                PortfolioHolding.quantity > 0
            )
            
            holdings = holdings_query.all()
            
            if not holdings:
                return {
                    'portfolio_id': portfolio_id,
                    'by_asset': [],
                    'by_sector': {},
                    'by_asset_type': {},
                    'total_value': Decimal('0')
                }
            
            # Calculate total portfolio value
            total_value = sum(holding.market_value for holding, _, _, _, _ in holdings)
            
            # Allocation by asset
            by_asset = []
            for holding, symbol, name, asset_type, sector in holdings:
                percentage = (holding.market_value / total_value) * 100 if total_value > 0 else 0
                by_asset.append({
                    'asset_id': holding.asset_id,
                    'symbol': symbol,
                    'name': name,
                    'asset_type': asset_type,
                    'sector': sector,
                    'quantity': holding.quantity,
                    'market_value': holding.market_value,
                    'percentage': percentage
                })
            
            # Allocation by sector
            by_sector = {}
            for holding, _, _, _, sector in holdings:
                if sector:
                    if sector not in by_sector:
                        by_sector[sector] = {'value': Decimal('0'), 'percentage': Decimal('0')}
                    by_sector[sector]['value'] += holding.market_value
            
            for sector in by_sector:
                by_sector[sector]['percentage'] = (
                    by_sector[sector]['value'] / total_value
                ) * 100 if total_value > 0 else 0
            
            # Allocation by asset type
            by_asset_type = {}
            for holding, _, _, asset_type, _ in holdings:
                if asset_type:
                    if asset_type not in by_asset_type:
                        by_asset_type[asset_type] = {'value': Decimal('0'), 'percentage': Decimal('0')}
                    by_asset_type[asset_type]['value'] += holding.market_value
            
            for asset_type in by_asset_type:
                by_asset_type[asset_type]['percentage'] = (
                    by_asset_type[asset_type]['value'] / total_value
                ) * 100 if total_value > 0 else 0
            
            return {
                'portfolio_id': portfolio_id,
                'by_asset': by_asset,
                'by_sector': by_sector,
                'by_asset_type': by_asset_type,
                'total_value': total_value
            }
            
        except Exception as e:
            logger.error("Error calculating portfolio allocation", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def calculate_all_portfolios(self) -> List[Dict]:
        """Calculate values for all active portfolios."""
        try:
            portfolios = self.db.query(PortfolioModel).filter(
                PortfolioModel.is_active == True
            ).all()
            
            results = []
            for portfolio in portfolios:
                try:
                    values = await self.calculate_portfolio_values(portfolio.id)
                    results.append(values)
                except Exception as e:
                    logger.error("Error calculating portfolio", portfolio_id=portfolio.id, error=str(e))
                    continue
            
            return results
            
        except Exception as e:
            logger.error("Error calculating all portfolios", error=str(e))
            raise
    
    async def _get_latest_price(self, asset_id: int) -> Optional[Decimal]:
        """Get the latest price for an asset."""
        try:
            latest_price = self.db.query(PriceDataModel.close_price).filter(
                PriceDataModel.asset_id == asset_id
            ).order_by(PriceDataModel.date.desc()).first()
            
            if latest_price:
                return latest_price[0]
            
            return None
            
        except Exception as e:
            logger.error("Error getting latest price", asset_id=asset_id, error=str(e))
            return None
    
    async def get_portfolio_history(
        self, 
        portfolio_id: int, 
        days: int = 30
    ) -> List[Dict]:
        """Get portfolio value history over the last N days."""
        try:
            # This is a simplified version - in a real implementation,
            # you would store daily portfolio values or calculate them
            # based on historical prices and holdings
            
            end_date = date.today()
            start_date = end_date - timedelta(days=days)
            
            # Get current values as baseline
            current_values = await self.calculate_portfolio_values(portfolio_id)
            
            # Generate sample history (in real implementation, use actual historical data)
            history = []
            for i in range(days):
                day = start_date + timedelta(days=i)
                # Simplified: use current value as baseline
                # In real implementation, calculate based on historical prices
                history.append({
                    'date': day,
                    'value': current_values['current_value'],
                    'return': current_values['total_return_percentage']
                })
            
            return history
            
        except Exception as e:
            logger.error("Error getting portfolio history", portfolio_id=portfolio_id, error=str(e))
            raise
