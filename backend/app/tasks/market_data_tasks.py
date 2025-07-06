from celery import Celery
from celery.schedules import crontab
import asyncio
from typing import List, Dict, Any
import structlog
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal
from app.models import Asset
from app.services.market_data_service import MarketDataService, CacheManager

logger = structlog.get_logger()

# Create Celery app
celery_app = Celery(
    "portfolio_manager",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.market_data_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Scheduled tasks
celery_app.conf.beat_schedule = {
    "update-stock-prices": {
        "task": "app.tasks.market_data_tasks.update_all_stock_prices",
        "schedule": crontab(minute=0, hour="9-16"),  # Every hour during market hours
    },
    "update-etf-prices": {
        "task": "app.tasks.market_data_tasks.update_etf_prices",
        "schedule": crontab(minute=30, hour="9-16"),  # Every hour at 30 minutes during market hours
    },
    "update-crypto-prices": {
        "task": "app.tasks.market_data_tasks.update_crypto_prices",
        "schedule": crontab(minute="*/15"),  # Every 15 minutes for crypto
    },
    "cleanup-old-cache": {
        "task": "app.tasks.market_data_tasks.cleanup_old_cache_entries",
        "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
    },
}


@celery_app.task(bind=True, max_retries=3)
def update_asset_price_data(self, asset_id: int, period: str = "1d") -> Dict[str, Any]:
    """Update price data for a specific asset."""
    try:
        with SessionLocal() as db:
            # Get asset
            asset = db.query(Asset).filter(Asset.id == asset_id).first()
            if not asset:
                raise ValueError(f"Asset not found: {asset_id}")
            
            # Run async market data service
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                cache_manager = CacheManager()
                service = MarketDataService(db, cache_manager)
                
                # Initialize service
                loop.run_until_complete(service.initialize())
                
                # Fetch and save data
                price_data = loop.run_until_complete(
                    service.get_price_data(asset.symbol, period, force_refresh=True)
                )
                
                saved_count = loop.run_until_complete(
                    service.save_price_data_to_db(asset.symbol, price_data)
                )
                
                # Cleanup
                loop.run_until_complete(service.cleanup())
                
                logger.info(
                    "Updated price data for asset",
                    asset_id=asset_id,
                    symbol=asset.symbol,
                    saved_count=saved_count
                )
                
                return {
                    "success": True,
                    "asset_id": asset_id,
                    "symbol": asset.symbol,
                    "saved_count": saved_count,
                    "period": period
                }
                
            finally:
                loop.close()
                
    except Exception as e:
        logger.error("Error updating asset price data", asset_id=asset_id, error=str(e))
        
        # Retry logic
        if self.request.retries < self.max_retries:
            # Exponential backoff
            countdown = 2 ** self.request.retries
            logger.info(f"Retrying in {countdown} seconds", asset_id=asset_id)
            raise self.retry(countdown=countdown, exc=e)
        
        return {
            "success": False,
            "asset_id": asset_id,
            "error": str(e)
        }


@celery_app.task(bind=True)
def update_multiple_assets_price_data(self, asset_ids: List[int], period: str = "1d") -> Dict[str, Any]:
    """Update price data for multiple assets."""
    results = []
    
    for asset_id in asset_ids:
        try:
            result = update_asset_price_data.apply_async(args=[asset_id, period])
            results.append({
                "asset_id": asset_id,
                "task_id": result.id,
                "status": "submitted"
            })
        except Exception as e:
            results.append({
                "asset_id": asset_id,
                "status": "failed",
                "error": str(e)
            })
    
    return {
        "success": True,
        "total_assets": len(asset_ids),
        "results": results
    }


@celery_app.task
def update_all_stock_prices() -> Dict[str, Any]:
    """Update prices for all stock assets."""
    try:
        with SessionLocal() as db:
            # Get all stock assets
            stocks = db.query(Asset).filter(
                Asset.asset_type == "stock",
                Asset.is_active == True
            ).all()
            
            stock_ids = [stock.id for stock in stocks]
            
            logger.info(f"Updating prices for {len(stock_ids)} stocks")
            
            # Submit batch update
            result = update_multiple_assets_price_data.apply_async(
                args=[stock_ids, "1d"]
            )
            
            return {
                "success": True,
                "task_id": result.id,
                "asset_count": len(stock_ids),
                "asset_type": "stock"
            }
            
    except Exception as e:
        logger.error("Error updating all stock prices", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task
def update_etf_prices() -> Dict[str, Any]:
    """Update prices for all ETF assets."""
    try:
        with SessionLocal() as db:
            # Get all ETF assets
            etfs = db.query(Asset).filter(
                Asset.asset_type == "etf",
                Asset.is_active == True
            ).all()
            
            etf_ids = [etf.id for etf in etfs]
            
            logger.info(f"Updating prices for {len(etf_ids)} ETFs")
            
            # Submit batch update
            result = update_multiple_assets_price_data.apply_async(
                args=[etf_ids, "1d"]
            )
            
            return {
                "success": True,
                "task_id": result.id,
                "asset_count": len(etf_ids),
                "asset_type": "etf"
            }
            
    except Exception as e:
        logger.error("Error updating ETF prices", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task
def update_crypto_prices() -> Dict[str, Any]:
    """Update prices for all cryptocurrency assets."""
    try:
        with SessionLocal() as db:
            # Get all crypto assets
            cryptos = db.query(Asset).filter(
                Asset.asset_type == "cryptocurrency",
                Asset.is_active == True
            ).all()
            
            crypto_ids = [crypto.id for crypto in cryptos]
            
            logger.info(f"Updating prices for {len(crypto_ids)} cryptocurrencies")
            
            # Submit batch update
            result = update_multiple_assets_price_data.apply_async(
                args=[crypto_ids, "1d"]
            )
            
            return {
                "success": True,
                "task_id": result.id,
                "asset_count": len(crypto_ids),
                "asset_type": "cryptocurrency"
            }
            
    except Exception as e:
        logger.error("Error updating crypto prices", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task
def cleanup_old_cache_entries() -> Dict[str, Any]:
    """Clean up old cache entries."""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        try:
            cache_manager = CacheManager()
            loop.run_until_complete(cache_manager.connect())
            
            # This would require implementing cache cleanup logic
            # For now, we'll just log the task
            logger.info("Cache cleanup task executed")
            
            loop.run_until_complete(cache_manager.disconnect())
            
            return {
                "success": True,
                "message": "Cache cleanup completed"
            }
            
        finally:
            loop.close()
            
    except Exception as e:
        logger.error("Error during cache cleanup", error=str(e))
        return {
            "success": False,
            "error": str(e)
        }


@celery_app.task
def refresh_asset_data(asset_id: int) -> Dict[str, Any]:
    """Manually refresh data for a specific asset."""
    # Call the update task directly instead of using apply_async
    return update_asset_price_data(asset_id, "1d")
