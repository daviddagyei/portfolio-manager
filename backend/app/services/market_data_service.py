import yfinance as yf
import pandas as pd
import asyncio
import redis.asyncio as redis
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from decimal import Decimal
import json
import structlog
from asyncio_throttle import Throttler
from contextlib import asynccontextmanager

from app.core.config import settings
from app.models import Asset, PriceData
from app.schemas import PriceDataCreate
from sqlalchemy.orm import Session

logger = structlog.get_logger()


class MarketDataProvider:
    """Base class for market data providers."""
    
    def __init__(self):
        self.throttler = Throttler(rate_limit=5, period=1)  # 5 requests per second
    
    async def get_price_data(self, symbol: str, period: str = "1d") -> Dict[str, Any]:
        """Get price data for a symbol."""
        raise NotImplementedError
    
    async def get_multiple_price_data(self, symbols: List[str], period: str = "1d") -> Dict[str, Dict[str, Any]]:
        """Get price data for multiple symbols."""
        raise NotImplementedError


class YahooFinanceProvider(MarketDataProvider):
    """Yahoo Finance data provider using yfinance."""
    
    def __init__(self):
        super().__init__()
        self.valid_periods = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y", "10y", "ytd", "max"]
        self.valid_intervals = ["1m", "2m", "5m", "15m", "30m", "60m", "90m", "1h", "1d", "5d", "1wk", "1mo", "3mo"]
    
    async def get_price_data(self, symbol: str, period: str = "1d", interval: str = "1d") -> Dict[str, Any]:
        """Get price data for a single symbol."""
        async with self.throttler:
            try:
                # Run yfinance in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    self._fetch_yahoo_data, 
                    symbol, 
                    period, 
                    interval
                )
                return result
            except Exception as e:
                logger.error("Error fetching Yahoo Finance data", symbol=symbol, error=str(e))
                raise
    
    def _fetch_yahoo_data(self, symbol: str, period: str, interval: str) -> Dict[str, Any]:
        """Fetch data from Yahoo Finance (blocking operation)."""
        try:
            ticker = yf.Ticker(symbol)
            
            # Get historical data
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                raise ValueError(f"No data found for symbol {symbol}")
            
            # Get latest info
            info = {}
            try:
                info = ticker.info
            except Exception as e:
                logger.warning("Could not fetch ticker info", symbol=symbol, error=str(e))
            
            # Convert to our format
            price_data = []
            for date, row in hist.iterrows():
                price_data.append({
                    "date": date.isoformat(),
                    "open": float(row["Open"]) if not pd.isna(row["Open"]) else None,
                    "high": float(row["High"]) if not pd.isna(row["High"]) else None,
                    "low": float(row["Low"]) if not pd.isna(row["Low"]) else None,
                    "close": float(row["Close"]) if not pd.isna(row["Close"]) else None,
                    "volume": int(row["Volume"]) if not pd.isna(row["Volume"]) else None,
                })
            
            return {
                "symbol": symbol,
                "period": period,
                "interval": interval,
                "data": price_data,
                "info": info,
                "fetched_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Yahoo Finance fetch error", symbol=symbol, error=str(e))
            raise
    
    async def get_multiple_price_data(self, symbols: List[str], period: str = "1d") -> Dict[str, Dict[str, Any]]:
        """Get price data for multiple symbols."""
        tasks = []
        for symbol in symbols:
            task = asyncio.create_task(self.get_price_data(symbol, period))
            tasks.append((symbol, task))
        
        results = {}
        for symbol, task in tasks:
            try:
                results[symbol] = await task
            except Exception as e:
                logger.error("Failed to fetch data for symbol", symbol=symbol, error=str(e))
                results[symbol] = {"error": str(e)}
        
        return results


class CacheManager:
    """Redis-based cache manager for market data."""
    
    def __init__(self, redis_url: Optional[str] = None):
        self.redis_url = redis_url or settings.REDIS_URL or "redis://localhost:6379"
        self.redis_client = None
        self.default_ttl = settings.CACHE_TTL  # Default TTL in seconds
    
    async def connect(self):
        """Connect to Redis."""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("Connected to Redis cache")
        except Exception as e:
            logger.warning("Could not connect to Redis", error=str(e))
            self.redis_client = None
    
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data."""
        if not self.redis_client:
            return None
        
        try:
            data = await self.redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception as e:
            logger.error("Cache get error", key=key, error=str(e))
        
        return None
    
    async def set(self, key: str, value: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set cached data."""
        if not self.redis_client:
            return False
        
        try:
            ttl = ttl or self.default_ttl
            await self.redis_client.setex(key, ttl, json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.error("Cache set error", key=key, error=str(e))
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete cached data."""
        if not self.redis_client:
            return False
        
        try:
            await self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.error("Cache delete error", key=key, error=str(e))
            return False
    
    def make_key(self, symbol: str, period: str, data_type: str = "price") -> str:
        """Generate cache key."""
        return f"market_data:{data_type}:{symbol}:{period}"


class MarketDataService:
    """Main market data service coordinating providers and caching."""
    
    def __init__(self, db: Session, cache_manager: Optional[CacheManager] = None):
        self.db = db
        self.cache_manager = cache_manager or CacheManager()
        self.providers = {
            "yahoo": YahooFinanceProvider(),
        }
        self.default_provider = "yahoo"
    
    async def initialize(self):
        """Initialize the service."""
        await self.cache_manager.connect()
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.cache_manager.disconnect()
    
    async def get_price_data(
        self, 
        symbol: str, 
        period: str = "1d", 
        force_refresh: bool = False,
        provider: str = None
    ) -> Dict[str, Any]:
        """Get price data with caching."""
        provider = provider or self.default_provider
        cache_key = self.cache_manager.make_key(symbol, period)
        
        # Check cache first
        if not force_refresh:
            cached_data = await self.cache_manager.get(cache_key)
            if cached_data:
                logger.info("Cache hit for market data", symbol=symbol, period=period)
                return cached_data
        
        # Fetch from provider
        logger.info("Fetching market data from provider", symbol=symbol, period=period, provider=provider)
        data_provider = self.providers.get(provider)
        if not data_provider:
            raise ValueError(f"Unknown provider: {provider}")
        
        try:
            data = await data_provider.get_price_data(symbol, period)
            
            # Cache the result
            await self.cache_manager.set(cache_key, data)
            
            return data
        except Exception as e:
            logger.error("Error fetching market data", symbol=symbol, error=str(e))
            raise
    
    async def get_multiple_price_data(
        self, 
        symbols: List[str], 
        period: str = "1d",
        force_refresh: bool = False,
        provider: str = None
    ) -> Dict[str, Dict[str, Any]]:
        """Get price data for multiple symbols."""
        provider = provider or self.default_provider
        data_provider = self.providers.get(provider)
        if not data_provider:
            raise ValueError(f"Unknown provider: {provider}")
        
        # Check cache for each symbol
        results = {}
        symbols_to_fetch = []
        
        if not force_refresh:
            for symbol in symbols:
                cache_key = self.cache_manager.make_key(symbol, period)
                cached_data = await self.cache_manager.get(cache_key)
                if cached_data:
                    results[symbol] = cached_data
                else:
                    symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch = symbols
        
        # Fetch uncached symbols
        if symbols_to_fetch:
            fetched_data = await data_provider.get_multiple_price_data(symbols_to_fetch, period)
            
            # Cache and merge results
            for symbol, data in fetched_data.items():
                if "error" not in data:
                    cache_key = self.cache_manager.make_key(symbol, period)
                    await self.cache_manager.set(cache_key, data)
                results[symbol] = data
        
        return results
    
    async def save_price_data_to_db(self, symbol: str, price_data: Dict[str, Any]) -> int:
        """Save price data to database."""
        try:
            # Get asset
            asset = self.db.query(Asset).filter(Asset.symbol == symbol).first()
            if not asset:
                raise ValueError(f"Asset not found: {symbol}")
            
            saved_count = 0
            for data_point in price_data.get("data", []):
                # Check if price data already exists
                existing = self.db.query(PriceData).filter(
                    PriceData.asset_id == asset.id,
                    PriceData.date == datetime.fromisoformat(data_point["date"])
                ).first()
                
                if existing:
                    # Update existing record
                    existing.open_price = Decimal(str(data_point["open"])) if data_point["open"] else None
                    existing.high_price = Decimal(str(data_point["high"])) if data_point["high"] else None
                    existing.low_price = Decimal(str(data_point["low"])) if data_point["low"] else None
                    existing.close_price = Decimal(str(data_point["close"])) if data_point["close"] else None
                    existing.volume = data_point["volume"]
                else:
                    # Create new record
                    price_record = PriceData(
                        asset_id=asset.id,
                        date=datetime.fromisoformat(data_point["date"]),
                        open_price=Decimal(str(data_point["open"])) if data_point["open"] else None,
                        high_price=Decimal(str(data_point["high"])) if data_point["high"] else None,
                        low_price=Decimal(str(data_point["low"])) if data_point["low"] else None,
                        close_price=Decimal(str(data_point["close"])) if data_point["close"] else None,
                        volume=data_point["volume"]
                    )
                    self.db.add(price_record)
                
                saved_count += 1
            
            self.db.commit()
            logger.info("Saved price data to database", symbol=symbol, count=saved_count)
            return saved_count
            
        except Exception as e:
            self.db.rollback()
            logger.error("Error saving price data to database", symbol=symbol, error=str(e))
            raise
