from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.schemas import (
    Asset, AssetCreate, AssetUpdate, AssetResponse, AssetListResponse
)
from app.models import Asset as AssetModel
from app.services.asset_service import AssetService

logger = structlog.get_logger()

router = APIRouter()


@router.get("/", response_model=AssetListResponse)
async def get_assets(
    skip: int = Query(0, ge=0, description="Number of assets to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of assets to return"),
    asset_type: Optional[str] = Query(None, description="Filter by asset type"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    search: Optional[str] = Query(None, description="Search in symbol or name"),
    db: Session = Depends(get_db)
):
    """Get all assets with optional filtering."""
    try:
        service = AssetService(db)
        assets, total = await service.get_assets(
            skip=skip,
            limit=limit,
            asset_type=asset_type,
            sector=sector,
            search=search
        )
        
        return AssetListResponse(
            data=assets,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        logger.error("Error fetching assets", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=AssetResponse)
async def create_asset(
    asset: AssetCreate,
    db: Session = Depends(get_db)
):
    """Create a new asset."""
    try:
        service = AssetService(db)
        created_asset = await service.create_asset(asset)
        
        return AssetResponse(
            data=created_asset,
            message="Asset created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
    except Exception as e:
        logger.error("Error creating asset", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{asset_id}", response_model=AssetResponse)
async def get_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific asset by ID."""
    try:
        service = AssetService(db)
        asset = await service.get_asset(asset_id)
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return AssetResponse(
            data=asset,
            message="Asset retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching asset", asset_id=asset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/symbol/{symbol}", response_model=AssetResponse)
async def get_asset_by_symbol(
    symbol: str,
    db: Session = Depends(get_db)
):
    """Get a specific asset by symbol."""
    try:
        service = AssetService(db)
        asset = await service.get_asset_by_symbol(symbol)
        
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {symbol}")
        
        return AssetResponse(
            data=asset,
            message="Asset retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching asset by symbol", symbol=symbol, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{asset_id}", response_model=AssetResponse)
async def update_asset(
    asset_id: int,
    asset_update: AssetUpdate,
    db: Session = Depends(get_db)
):
    """Update an asset."""
    try:
        service = AssetService(db)
        updated_asset = await service.update_asset(asset_id, asset_update)
        
        if not updated_asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return AssetResponse(
            data=updated_asset,
            message="Asset updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating asset", asset_id=asset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{asset_id}")
async def delete_asset(
    asset_id: int,
    db: Session = Depends(get_db)
):
    """Delete an asset (mark as inactive)."""
    try:
        service = AssetService(db)
        success = await service.delete_asset(asset_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        return {"success": True, "message": "Asset deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting asset", asset_id=asset_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
