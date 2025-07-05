from typing import List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime

from app.models import Asset as AssetModel
from app.schemas import (
    AssetCreate, AssetUpdate, Asset
)


class AssetService:
    """Service class for asset operations."""
    
    def __init__(self, db: Session):
        self.db = db
    
    async def get_assets(
        self,
        skip: int = 0,
        limit: int = 50,
        asset_type: Optional[str] = None,
        sector: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Asset], int]:
        """Get assets with optional filtering."""
        query = self.db.query(AssetModel)
        
        # Apply filters
        if asset_type:
            query = query.filter(AssetModel.asset_type == asset_type)
        if sector:
            query = query.filter(AssetModel.sector == sector)
        if search:
            query = query.filter(
                or_(
                    AssetModel.symbol.ilike(f"%{search}%"),
                    AssetModel.name.ilike(f"%{search}%")
                )
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        assets = query.offset(skip).limit(limit).all()
        
        return [Asset.from_orm(a) for a in assets], total
    
    async def get_asset(self, asset_id: int) -> Optional[Asset]:
        """Get a specific asset by ID."""
        asset = self.db.query(AssetModel).filter(
            AssetModel.id == asset_id
        ).first()
        
        return Asset.from_orm(asset) if asset else None
    
    async def get_asset_by_symbol(self, symbol: str) -> Optional[Asset]:
        """Get a specific asset by symbol."""
        asset = self.db.query(AssetModel).filter(
            AssetModel.symbol == symbol.upper()
        ).first()
        
        return Asset.from_orm(asset) if asset else None
    
    async def create_asset(self, asset_data: AssetCreate) -> Asset:
        """Create a new asset."""
        # Check if asset with same symbol already exists
        existing_asset = await self.get_asset_by_symbol(asset_data.symbol)
        if existing_asset:
            raise ValueError(f"Asset with symbol {asset_data.symbol} already exists")
        
        asset = AssetModel(**asset_data.dict())
        
        self.db.add(asset)
        self.db.commit()
        self.db.refresh(asset)
        
        return Asset.from_orm(asset)
    
    async def update_asset(
        self, 
        asset_id: int, 
        asset_update: AssetUpdate
    ) -> Optional[Asset]:
        """Update an asset."""
        asset = self.db.query(AssetModel).filter(
            AssetModel.id == asset_id
        ).first()
        
        if not asset:
            return None
        
        update_data = asset_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(asset, field, value)
        
        self.db.commit()
        self.db.refresh(asset)
        
        return Asset.from_orm(asset)
    
    async def delete_asset(self, asset_id: int) -> bool:
        """Delete an asset."""
        asset = self.db.query(AssetModel).filter(
            AssetModel.id == asset_id
        ).first()
        
        if not asset:
            return False
        
        # Set as inactive instead of deleting to preserve historical data
        asset.is_active = False
        self.db.commit()
        
        return True
