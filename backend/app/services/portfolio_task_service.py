from typing import List, Dict, Optional
from datetime import datetime, date
import structlog
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.services.portfolio_calculation_engine import PortfolioCalculationEngine
from app.services.portfolio_history_service import PortfolioHistoryService
from app.models import Portfolio as PortfolioModel


logger = structlog.get_logger()


class PortfolioTaskService:
    """Service for portfolio background tasks."""
    
    @staticmethod
    async def calculate_all_portfolios_task() -> Dict:
        """Background task to calculate all portfolio values."""
        try:
            db = SessionLocal()
            engine = PortfolioCalculationEngine(db)
            
            results = await engine.calculate_all_portfolios()
            
            logger.info(f"Portfolio calculation task completed. Updated {len(results)} portfolios")
            
            return {
                'success': True,
                'updated_portfolios': len(results),
                'timestamp': datetime.now().isoformat(),
                'results': results
            }
            
        except Exception as e:
            logger.error("Error in portfolio calculation task", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            db.close()
    
    @staticmethod
    async def record_daily_snapshots_task(snapshot_date: Optional[date] = None) -> Dict:
        """Background task to record daily portfolio snapshots."""
        try:
            db = SessionLocal()
            history_service = PortfolioHistoryService(db)
            
            if not snapshot_date:
                snapshot_date = date.today()
            
            results = await history_service.record_all_portfolios_snapshot(snapshot_date)
            
            logger.info(f"Daily snapshots task completed. Recorded {results['successful_snapshots']} snapshots")
            
            return {
                'success': True,
                'snapshot_date': snapshot_date.isoformat(),
                'successful_snapshots': results['successful_snapshots'],
                'total_portfolios': results['total_portfolios'],
                'errors': results['errors'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in daily snapshots task", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            db.close()
    
    @staticmethod
    async def update_portfolio_prices_task() -> Dict:
        """Background task to update portfolio holdings with latest prices."""
        try:
            db = SessionLocal()
            
            # Get all active portfolios
            portfolios = db.query(PortfolioModel).filter(
                PortfolioModel.is_active == True
            ).all()
            
            engine = PortfolioCalculationEngine(db)
            
            updated_portfolios = []
            errors = []
            
            for portfolio in portfolios:
                try:
                    # Update portfolio values (this will fetch latest prices)
                    result = await engine.calculate_portfolio_values(portfolio.id)
                    updated_portfolios.append(result)
                    
                except Exception as e:
                    errors.append({
                        'portfolio_id': portfolio.id,
                        'error': str(e)
                    })
                    logger.error(f"Error updating portfolio {portfolio.id}", error=str(e))
            
            logger.info(f"Portfolio prices update task completed. Updated {len(updated_portfolios)} portfolios")
            
            return {
                'success': True,
                'updated_portfolios': len(updated_portfolios),
                'total_portfolios': len(portfolios),
                'errors': len(errors),
                'error_details': errors,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in portfolio prices update task", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            db.close()
    
    @staticmethod
    async def cleanup_old_data_task(days_to_keep: int = 1095) -> Dict:
        """Background task to cleanup old portfolio history data."""
        try:
            db = SessionLocal()
            history_service = PortfolioHistoryService(db)
            
            results = await history_service.cleanup_old_history(days_to_keep)
            
            logger.info(f"Data cleanup task completed. Deleted {results['deleted_count']} old records")
            
            return {
                'success': True,
                'deleted_count': results['deleted_count'],
                'cutoff_date': results['cutoff_date'],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in data cleanup task", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            db.close()
    
    @staticmethod
    async def generate_portfolio_reports_task(portfolio_ids: Optional[List[int]] = None) -> Dict:
        """Background task to generate portfolio reports."""
        try:
            db = SessionLocal()
            
            # Get portfolios to process
            if portfolio_ids:
                portfolios = db.query(PortfolioModel).filter(
                    PortfolioModel.id.in_(portfolio_ids),
                    PortfolioModel.is_active == True
                ).all()
            else:
                portfolios = db.query(PortfolioModel).filter(
                    PortfolioModel.is_active == True
                ).all()
            
            engine = PortfolioCalculationEngine(db)
            history_service = PortfolioHistoryService(db)
            
            reports = []
            errors = []
            
            for portfolio in portfolios:
                try:
                    # Generate comprehensive report
                    portfolio_values = await engine.calculate_portfolio_values(portfolio.id)
                    portfolio_allocation = await engine.get_portfolio_allocation(portfolio.id)
                    portfolio_performance = await engine.calculate_portfolio_performance(portfolio.id)
                    performance_metrics = await history_service.calculate_performance_metrics(portfolio.id)
                    
                    report = {
                        'portfolio_id': portfolio.id,
                        'portfolio_name': portfolio.name,
                        'values': portfolio_values,
                        'allocation': portfolio_allocation,
                        'performance': portfolio_performance,
                        'metrics': performance_metrics,
                        'generated_at': datetime.now().isoformat()
                    }
                    
                    reports.append(report)
                    
                except Exception as e:
                    errors.append({
                        'portfolio_id': portfolio.id,
                        'error': str(e)
                    })
                    logger.error(f"Error generating report for portfolio {portfolio.id}", error=str(e))
            
            logger.info(f"Portfolio reports generation task completed. Generated {len(reports)} reports")
            
            return {
                'success': True,
                'generated_reports': len(reports),
                'total_portfolios': len(portfolios),
                'errors': len(errors),
                'error_details': errors,
                'reports': reports,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error("Error in portfolio reports generation task", error=str(e))
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
        finally:
            db.close()


# Schedule configuration for background tasks
PORTFOLIO_TASKS_SCHEDULE = {
    'calculate_all_portfolios': {
        'task': 'calculate_all_portfolios_task',
        'schedule': '*/30 * * * *',  # Every 30 minutes
        'description': 'Calculate all portfolio values'
    },
    'record_daily_snapshots': {
        'task': 'record_daily_snapshots_task',
        'schedule': '0 0 * * *',  # Daily at midnight
        'description': 'Record daily portfolio snapshots'
    },
    'update_portfolio_prices': {
        'task': 'update_portfolio_prices_task',
        'schedule': '*/15 * * * *',  # Every 15 minutes during market hours
        'description': 'Update portfolio holdings with latest prices'
    },
    'cleanup_old_data': {
        'task': 'cleanup_old_data_task',
        'schedule': '0 2 * * 0',  # Weekly on Sunday at 2 AM
        'description': 'Cleanup old portfolio history data'
    },
    'generate_portfolio_reports': {
        'task': 'generate_portfolio_reports_task',
        'schedule': '0 6 * * *',  # Daily at 6 AM
        'description': 'Generate comprehensive portfolio reports'
    }
}
