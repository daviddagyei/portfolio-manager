from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from datetime import datetime, date, timedelta
from decimal import Decimal
import structlog

from app.models import Portfolio as PortfolioModel, PortfolioHistory


logger = structlog.get_logger()


class PortfolioHistoryService:
    """Service for tracking portfolio history."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def record_daily_snapshot(self, portfolio_id: int, snapshot_date: date = None) -> Dict:
        """Record a daily portfolio snapshot."""
        try:
            if not snapshot_date:
                snapshot_date = date.today()
            
            # Check if snapshot already exists for this date
            existing_snapshot = self.db.query(PortfolioHistory).filter(
                PortfolioHistory.portfolio_id == portfolio_id,
                PortfolioHistory.date == snapshot_date
            ).first()
            
            if existing_snapshot:
                logger.info(f"Snapshot already exists for portfolio {portfolio_id} on {snapshot_date}")
                return {
                    'portfolio_id': portfolio_id,
                    'date': snapshot_date,
                    'value': existing_snapshot.value,
                    'status': 'already_exists'
                }
            
            # Get current portfolio values
            from app.services.portfolio_calculation_engine import PortfolioCalculationEngine
            engine = PortfolioCalculationEngine(self.db)
            portfolio_values = await engine.calculate_portfolio_values(portfolio_id)
            
            # Create history record
            history_record = PortfolioHistory(
                portfolio_id=portfolio_id,
                date=snapshot_date,
                value=portfolio_values['current_value'],
                return_amount=portfolio_values['total_return'],
                return_percentage=portfolio_values['total_return_percentage'],
                cash_flows=Decimal('0'),  # TODO: Calculate actual cash flows
                holdings_count=portfolio_values['holdings_count']
            )
            
            self.db.add(history_record)
            self.db.commit()
            self.db.refresh(history_record)
            
            logger.info(f"Recorded portfolio snapshot for {portfolio_id} on {snapshot_date}")
            
            return {
                'portfolio_id': portfolio_id,
                'date': snapshot_date,
                'value': history_record.value,
                'return_amount': history_record.return_amount,
                'return_percentage': history_record.return_percentage,
                'status': 'created'
            }
            
        except Exception as e:
            logger.error("Error recording portfolio snapshot", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def get_portfolio_history(
        self, 
        portfolio_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get portfolio history for a date range."""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=365)
            if not end_date:
                end_date = date.today()
            
            query = self.db.query(PortfolioHistory).filter(
                PortfolioHistory.portfolio_id == portfolio_id,
                PortfolioHistory.date >= start_date,
                PortfolioHistory.date <= end_date
            ).order_by(PortfolioHistory.date.desc()).limit(limit)
            
            history_records = query.all()
            
            return [
                {
                    'date': record.date.isoformat(),
                    'value': record.value,
                    'return_amount': record.return_amount,
                    'return_percentage': record.return_percentage,
                    'cash_flows': record.cash_flows,
                    'holdings_count': record.holdings_count
                }
                for record in history_records
            ]
            
        except Exception as e:
            logger.error("Error getting portfolio history", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def calculate_performance_metrics(
        self, 
        portfolio_id: int, 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Calculate performance metrics from historical data."""
        try:
            history = await self.get_portfolio_history(
                portfolio_id, start_date, end_date
            )
            
            if len(history) < 2:
                return {
                    'portfolio_id': portfolio_id,
                    'total_return': Decimal('0'),
                    'volatility': Decimal('0'),
                    'sharpe_ratio': Decimal('0'),
                    'max_drawdown': Decimal('0'),
                    'data_points': len(history)
                }
            
            # Calculate daily returns
            daily_returns = []
            values = [Decimal(str(h['value'])) for h in reversed(history)]
            
            for i in range(1, len(values)):
                if values[i-1] > 0:
                    daily_return = (values[i] - values[i-1]) / values[i-1]
                    daily_returns.append(daily_return)
            
            if not daily_returns:
                return {
                    'portfolio_id': portfolio_id,
                    'total_return': Decimal('0'),
                    'volatility': Decimal('0'),
                    'sharpe_ratio': Decimal('0'),
                    'max_drawdown': Decimal('0'),
                    'data_points': len(history)
                }
            
            # Calculate metrics
            total_return = (values[-1] - values[0]) / values[0] if values[0] > 0 else Decimal('0')
            
            # Volatility (standard deviation of daily returns)
            mean_return = sum(daily_returns) / len(daily_returns)
            variance = sum((r - mean_return) ** 2 for r in daily_returns) / len(daily_returns)
            volatility = variance ** Decimal('0.5')
            
            # Sharpe ratio (assuming risk-free rate of 0 for simplicity)
            sharpe_ratio = mean_return / volatility if volatility > 0 else Decimal('0')
            
            # Maximum drawdown
            max_drawdown = Decimal('0')
            peak = values[0]
            for value in values:
                if value > peak:
                    peak = value
                drawdown = (peak - value) / peak if peak > 0 else Decimal('0')
                if drawdown > max_drawdown:
                    max_drawdown = drawdown
            
            return {
                'portfolio_id': portfolio_id,
                'start_date': start_date.isoformat() if start_date else None,
                'end_date': end_date.isoformat() if end_date else None,
                'total_return': total_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe_ratio,
                'max_drawdown': max_drawdown,
                'data_points': len(history),
                'daily_returns_count': len(daily_returns)
            }
            
        except Exception as e:
            logger.error("Error calculating performance metrics", portfolio_id=portfolio_id, error=str(e))
            raise
    
    async def record_all_portfolios_snapshot(self, snapshot_date: date = None) -> Dict:
        """Record daily snapshots for all active portfolios."""
        try:
            if not snapshot_date:
                snapshot_date = date.today()
            
            # Get all active portfolios
            portfolios = self.db.query(PortfolioModel).filter(
                PortfolioModel.is_active == True
            ).all()
            
            results = []
            errors = []
            
            for portfolio in portfolios:
                try:
                    result = await self.record_daily_snapshot(portfolio.id, snapshot_date)
                    results.append(result)
                except Exception as e:
                    errors.append({
                        'portfolio_id': portfolio.id,
                        'error': str(e)
                    })
            
            return {
                'date': snapshot_date.isoformat(),
                'total_portfolios': len(portfolios),
                'successful_snapshots': len(results),
                'errors': len(errors),
                'results': results,
                'error_details': errors
            }
            
        except Exception as e:
            logger.error("Error recording all portfolios snapshot", error=str(e))
            raise
    
    async def get_portfolio_comparison(
        self, 
        portfolio_ids: List[int], 
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> Dict:
        """Compare performance of multiple portfolios."""
        try:
            if not start_date:
                start_date = date.today() - timedelta(days=365)
            if not end_date:
                end_date = date.today()
            
            comparison_data = {}
            
            for portfolio_id in portfolio_ids:
                history = await self.get_portfolio_history(
                    portfolio_id, start_date, end_date
                )
                
                performance = await self.calculate_performance_metrics(
                    portfolio_id, start_date, end_date
                )
                
                comparison_data[portfolio_id] = {
                    'history': history,
                    'performance': performance
                }
            
            return {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'portfolios': comparison_data
            }
            
        except Exception as e:
            logger.error("Error getting portfolio comparison", portfolio_ids=portfolio_ids, error=str(e))
            raise
    
    async def cleanup_old_history(self, days_to_keep: int = 1095) -> Dict:
        """Clean up old history records (default: keep 3 years)."""
        try:
            cutoff_date = date.today() - timedelta(days=days_to_keep)
            
            # Delete old records
            deleted_count = self.db.query(PortfolioHistory).filter(
                PortfolioHistory.date < cutoff_date
            ).delete()
            
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count} old portfolio history records")
            
            return {
                'cutoff_date': cutoff_date.isoformat(),
                'deleted_count': deleted_count
            }
            
        except Exception as e:
            logger.error("Error cleaning up old history", error=str(e))
            raise
