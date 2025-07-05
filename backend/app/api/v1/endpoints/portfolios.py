from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.schemas import (
    Portfolio, PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioListResponse, PortfolioSummary
)
from app.models import Portfolio as PortfolioModel
from app.services.portfolio_service import PortfolioService

logger = structlog.get_logger()

router = APIRouter()


@router.get("/", response_model=PortfolioListResponse)
async def get_portfolios(
    skip: int = Query(0, ge=0, description="Number of portfolios to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of portfolios to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    portfolio_type: Optional[str] = Query(None, description="Filter by portfolio type"),
    db: Session = Depends(get_db)
):
    """Get all portfolios with optional filtering."""
    try:
        service = PortfolioService(db)
        portfolios, total = await service.get_portfolios(
            skip=skip,
            limit=limit,
            user_id=user_id,
            portfolio_type=portfolio_type
        )
        
        return PortfolioListResponse(
            data=portfolios,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        logger.error("Error fetching portfolios", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=PortfolioResponse)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """Create a new portfolio."""
    try:
        service = PortfolioService(db)
        created_portfolio = await service.create_portfolio(portfolio)
        
        return PortfolioResponse(
            data=created_portfolio,
            message="Portfolio created successfully"
        )
    except Exception as e:
        logger.error("Error creating portfolio", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}", response_model=PortfolioResponse)
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific portfolio by ID."""
    try:
        service = PortfolioService(db)
        portfolio = await service.get_portfolio(portfolio_id)
        
        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return PortfolioResponse(
            data=portfolio,
            message="Portfolio retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching portfolio", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}", response_model=PortfolioResponse)
async def update_portfolio(
    portfolio_id: int,
    portfolio_update: PortfolioUpdate,
    db: Session = Depends(get_db)
):
    """Update a portfolio."""
    try:
        service = PortfolioService(db)
        updated_portfolio = await service.update_portfolio(portfolio_id, portfolio_update)
        
        if not updated_portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return PortfolioResponse(
            data=updated_portfolio,
            message="Portfolio updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating portfolio", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{portfolio_id}")
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Delete a portfolio."""
    try:
        service = PortfolioService(db)
        success = await service.delete_portfolio(portfolio_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return {"success": True, "message": "Portfolio deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting portfolio", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/summary", response_model=PortfolioSummary)
async def get_portfolio_summary(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get portfolio summary with key metrics."""
    try:
        service = PortfolioService(db)
        summary = await service.get_portfolio_summary(portfolio_id)
        
        if not summary:
            raise HTTPException(status_code=404, detail="Portfolio not found")
        
        return summary
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching portfolio summary", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
