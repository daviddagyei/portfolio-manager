from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.schemas import (
    PriceData, PriceDataCreate, PriceDataResponse, PriceDataListResponse,
    PriceHistoryRequest, PriceHistoryResponse
)
from app.models import Asset, PriceData as PriceDataModel
from app.services.market_data_service import MarketDataService, CacheManager
from app.tasks.market_data_tasks import update_asset_price_data, refresh_asset_data

logger = structlog.get_logger()

router = APIRouter()


@router.get("/prices", response_model=PriceDataListResponse)
async def get_price_data(
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    symbol: Optional[str] = Query(None, description="Filter by asset symbol"),
    start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    db: Session = Depends(get_db)
):
    """Get historical price data with filtering."""
    try:
        # Join PriceData with Asset to get asset details
        query = db.query(PriceDataModel, Asset).join(Asset, PriceDataModel.asset_id == Asset.id)
        
        # Apply filters
        if asset_id:
            query = query.filter(PriceDataModel.asset_id == asset_id)
        
        if symbol:
            asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
            if asset:
                query = query.filter(PriceDataModel.asset_id == asset.id)
            else:
                raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        if start_date:
            query = query.filter(PriceDataModel.date >= start_date)
        
        if end_date:
            query = query.filter(PriceDataModel.date <= end_date)
        
        # Get total count
        total = query.count()
        
        # Apply pagination and ordering
        results = query.order_by(PriceDataModel.date.desc()).offset(skip).limit(limit).all()
        
        # Convert to PriceDataWithAsset objects
        price_data_with_assets = []
        for price_data, asset in results:
            price_dict = {
                **price_data.__dict__,
                'asset_symbol': asset.symbol,
                'asset_name': asset.name
            }
            price_data_with_assets.append(price_dict)
        
        return PriceDataListResponse(
            data=price_data_with_assets,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching price data", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch", response_model=Dict[str, Any])
async def fetch_market_data(
    symbol: str = Query(..., description="Asset symbol"),
    period: str = Query("1d", description="Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)"),
    force_refresh: bool = Query(False, description="Force refresh from provider"),
    save_to_db: bool = Query(True, description="Save fetched data to database"),
    db: Session = Depends(get_db)
):
    """Fetch market data from external provider."""
    try:
        # Validate asset exists
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        # Initialize market data service
        cache_manager = CacheManager()
        service = MarketDataService(db, cache_manager)
        
        await service.initialize()
        
        try:
            # Fetch data
            price_data = await service.get_price_data(
                symbol.upper(), 
                period, 
                force_refresh=force_refresh
            )
            
            # Save to database if requested
            saved_count = 0
            if save_to_db:
                saved_count = await service.save_price_data_to_db(symbol.upper(), price_data)
            
            return {
                "success": True,
                "symbol": symbol.upper(),
                "period": period,
                "data_points": len(price_data.get("data", [])),
                "saved_to_db": saved_count if save_to_db else 0,
                "fetched_at": price_data.get("fetched_at"),
                "cached": not force_refresh
            }
            
        finally:
            await service.cleanup()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching market data", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch/multiple", response_model=Dict[str, Any])
async def fetch_multiple_market_data(
    symbols: List[str] = Query(..., description="Asset symbols"),
    period: str = Query("1d", description="Data period"),
    force_refresh: bool = Query(False, description="Force refresh from provider"),
    save_to_db: bool = Query(True, description="Save fetched data to database"),
    db: Session = Depends(get_db)
):
    """Fetch market data for multiple symbols."""
    try:
        # Validate symbols
        symbols_upper = [s.upper() for s in symbols]
        assets = db.query(Asset).filter(Asset.symbol.in_(symbols_upper)).all()
        found_symbols = {asset.symbol for asset in assets}
        missing_symbols = set(symbols_upper) - found_symbols
        
        if missing_symbols:
            raise HTTPException(
                status_code=404, 
                detail=f"Assets not found: {', '.join(missing_symbols)}"
            )
        
        # Initialize market data service
        cache_manager = CacheManager()
        service = MarketDataService(db, cache_manager)
        
        await service.initialize()
        
        try:
            # Fetch data for all symbols
            all_data = await service.get_multiple_price_data(
                symbols_upper, 
                period, 
                force_refresh=force_refresh
            )
            
            # Save to database if requested
            results = {}
            for symbol, data in all_data.items():
                saved_count = 0
                if save_to_db and "error" not in data:
                    saved_count = await service.save_price_data_to_db(symbol, data)
                
                results[symbol] = {
                    "success": "error" not in data,
                    "data_points": len(data.get("data", [])) if "error" not in data else 0,
                    "saved_to_db": saved_count if save_to_db else 0,
                    "error": data.get("error")
                }
            
            return {
                "success": True,
                "period": period,
                "symbols": symbols_upper,
                "results": results
            }
            
        finally:
            await service.cleanup()
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching multiple market data", symbols=symbols, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/refresh/{asset_id}", response_model=Dict[str, Any])
async def refresh_asset_data_endpoint(
    asset_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Refresh market data for a specific asset using background task."""
    try:
        # Validate asset exists
        asset = db.query(Asset).filter(Asset.id == asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")
        
        # Start background task
        task = refresh_asset_data.apply_async(args=[asset_id])
        
        return {
            "success": True,
            "message": f"Refresh task started for asset {asset.symbol}",
            "task_id": task.id,
            "asset_id": asset_id,
            "symbol": asset.symbol
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting refresh task", asset_id=asset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/refresh/status/{task_id}", response_model=Dict[str, Any])
async def get_refresh_status(task_id: str):
    """Get status of a refresh task."""
    try:
        from app.tasks.market_data_tasks import celery_app
        
        result = celery_app.AsyncResult(task_id)
        
        return {
            "task_id": task_id,
            "status": result.status,
            "result": result.result if result.ready() else None,
            "traceback": result.traceback if result.failed() else None
        }
        
    except Exception as e:
        logger.error("Error getting task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latest/{symbol}", response_model=PriceDataResponse)
async def get_latest_price(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Get the latest price data for a symbol."""
    try:
        # Find asset
        asset = db.query(Asset).filter(Asset.symbol == symbol.upper()).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        # Get latest price data
        latest_price = db.query(PriceDataModel).filter(
            PriceDataModel.asset_id == asset.id
        ).order_by(PriceDataModel.date.desc()).first()
        
        if not latest_price:
            raise HTTPException(status_code=404, detail=f"No price data found for {symbol}")
        
        return PriceDataResponse(
            data=PriceData.from_orm(latest_price),
            message=f"Latest price for {symbol}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting latest price", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/history", response_model=PriceHistoryResponse)
async def get_price_history(
    request: PriceHistoryRequest,
    db: Session = Depends(get_db)
):
    """Get price history for an asset."""
    try:
        # Find asset
        asset = db.query(Asset).filter(Asset.id == request.asset_id).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {request.asset_id}")
        
        # Build query
        query = db.query(PriceDataModel).filter(PriceDataModel.asset_id == request.asset_id)
        
        if request.start_date:
            query = query.filter(PriceDataModel.date >= request.start_date)
        
        if request.end_date:
            query = query.filter(PriceDataModel.date <= request.end_date)
        
        # Get price data
        price_data = query.order_by(PriceDataModel.date.desc()).all()
        
        return PriceHistoryResponse(
            data=[PriceData.from_orm(pd) for pd in price_data],
            asset_symbol=asset.symbol,
            asset_name=asset.name,
            period=request.period or "custom",
            total_records=len(price_data)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error getting price history", asset_id=request.asset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
