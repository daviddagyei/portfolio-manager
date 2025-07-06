#!/usr/bin/env python3
"""
Portfolio Manager CLI for market data management.
"""

import asyncio
import sys
import argparse
from typing import List, Optional
from datetime import datetime, timedelta
import structlog

# Add the app directory to the Python path
sys.path.insert(0, '/home/iamdankwa/portfolio-manager/backend')

from app.core.database import SessionLocal, init_db
from app.models import Asset
from app.services.market_data_service import MarketDataService, CacheManager
from app.tasks.market_data_tasks import (
    update_asset_price_data, 
    update_all_stock_prices, 
    update_etf_prices,
    update_crypto_prices
)

logger = structlog.get_logger()


async def fetch_asset_data(symbol: str, period: str = "1d", save_to_db: bool = True):
    """Fetch data for a specific asset."""
    print(f"Fetching data for {symbol} with period {period}...")
    
    with SessionLocal() as db:
        # Check if asset exists
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        if not asset:
            print(f"Error: Asset {symbol} not found in database")
            return False
        
        try:
            cache_manager = CacheManager()
            service = MarketDataService(db, cache_manager)
            
            await service.initialize()
            
            # Fetch data
            data = await service.get_price_data(symbol.upper(), period, force_refresh=True)
            
            if save_to_db:
                saved_count = await service.save_price_data_to_db(symbol.upper(), data)
                print(f"Successfully saved {saved_count} price records for {symbol}")
            else:
                print(f"Fetched {len(data.get('data', []))} price records for {symbol}")
            
            await service.cleanup()
            return True
            
        except Exception as e:
            print(f"Error fetching data for {symbol}: {e}")
            return False


async def fetch_multiple_assets(symbols: List[str], period: str = "1d"):
    """Fetch data for multiple assets."""
    print(f"Fetching data for {len(symbols)} assets...")
    
    results = []
    for symbol in symbols:
        result = await fetch_asset_data(symbol, period)
        results.append((symbol, result))
    
    # Print summary
    successful = sum(1 for _, success in results if success)
    print(f"\nCompleted: {successful}/{len(symbols)} assets updated successfully")
    
    failed = [symbol for symbol, success in results if not success]
    if failed:
        print(f"Failed: {', '.join(failed)}")


def run_background_task(task_name: str):
    """Run a background task."""
    print(f"Running background task: {task_name}")
    
    try:
        if task_name == "stocks":
            result = update_all_stock_prices.apply_async()
        elif task_name == "etfs":
            result = update_etf_prices.apply_async()
        elif task_name == "crypto":
            result = update_crypto_prices.apply_async()
        else:
            print(f"Unknown task: {task_name}")
            return False
        
        print(f"Task submitted with ID: {result.id}")
        print("Use 'celery -A app.tasks.market_data_tasks.celery_app flower' to monitor tasks")
        return True
        
    except Exception as e:
        print(f"Error running task: {e}")
        return False


def list_assets(asset_type: Optional[str] = None):
    """List assets in the database."""
    with SessionLocal() as db:
        query = db.query(Asset).filter(Asset.is_active == True)
        
        if asset_type:
            query = query.filter(Asset.asset_type == asset_type)
        
        assets = query.all()
        
        print(f"\nFound {len(assets)} assets:")
        print("-" * 80)
        print(f"{'Symbol':<10} {'Name':<30} {'Type':<15} {'Sector':<20}")
        print("-" * 80)
        
        for asset in assets:
            print(f"{asset.symbol:<10} {asset.name[:30]:<30} {asset.asset_type:<15} {asset.sector or 'N/A':<20}")


async def test_market_data_service():
    """Test the market data service."""
    print("Testing market data service...")
    
    with SessionLocal() as db:
        try:
            cache_manager = CacheManager()
            service = MarketDataService(db, cache_manager)
            
            await service.initialize()
            
            # Test with AAPL
            print("Testing with AAPL...")
            data = await service.get_price_data("AAPL", "5d")
            
            if data and "data" in data:
                print(f"Successfully fetched {len(data['data'])} price points")
                latest = data['data'][-1] if data['data'] else None
                if latest:
                    print(f"Latest close price: ${latest.get('close', 'N/A')}")
            else:
                print("No data received")
            
            await service.cleanup()
            print("Market data service test completed successfully")
            
        except Exception as e:
            print(f"Market data service test failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="Portfolio Manager Market Data CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Fetch command
    fetch_parser = subparsers.add_parser("fetch", help="Fetch market data")
    fetch_parser.add_argument("symbol", help="Asset symbol")
    fetch_parser.add_argument("--period", default="1d", help="Data period (default: 1d)")
    fetch_parser.add_argument("--no-save", action="store_true", help="Don't save to database")
    
    # Fetch multiple command
    fetch_multi_parser = subparsers.add_parser("fetch-multi", help="Fetch data for multiple assets")
    fetch_multi_parser.add_argument("symbols", nargs="+", help="Asset symbols")
    fetch_multi_parser.add_argument("--period", default="1d", help="Data period (default: 1d)")
    
    # Background task command
    task_parser = subparsers.add_parser("task", help="Run background task")
    task_parser.add_argument("task_name", choices=["stocks", "etfs", "crypto"], help="Task to run")
    
    # List assets command
    list_parser = subparsers.add_parser("list", help="List assets")
    list_parser.add_argument("--type", help="Filter by asset type")
    
    # Test command
    subparsers.add_parser("test", help="Test market data service")
    
    # Initialize database command
    subparsers.add_parser("init-db", help="Initialize database")
    
    args = parser.parse_args()
    
    if args.command == "fetch":
        asyncio.run(fetch_asset_data(args.symbol, args.period, not args.no_save))
    
    elif args.command == "fetch-multi":
        asyncio.run(fetch_multiple_assets(args.symbols, args.period))
    
    elif args.command == "task":
        run_background_task(args.task_name)
    
    elif args.command == "list":
        list_assets(args.type)
    
    elif args.command == "test":
        asyncio.run(test_market_data_service())
    
    elif args.command == "init-db":
        print("Initializing database...")
        init_db()
        print("Database initialized successfully")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
