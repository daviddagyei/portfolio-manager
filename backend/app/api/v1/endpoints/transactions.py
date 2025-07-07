from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from datetime import date
import structlog

from app.core.database import get_db
from app.schemas import (
    Transaction, TransactionCreate, TransactionUpdate, TransactionWithDetails,
    TransactionResponse, TransactionListResponse
)
from app.services.transaction_service import TransactionService

logger = structlog.get_logger()

router = APIRouter()


@router.get("/", response_model=TransactionListResponse)
async def get_transactions(
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of transactions to return"),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    portfolio_id: Optional[int] = Query(None, description="Filter by portfolio ID"),
    asset_id: Optional[int] = Query(None, description="Filter by asset ID"),
    transaction_type: Optional[str] = Query(None, description="Filter by transaction type"),
    start_date: Optional[date] = Query(None, description="Start date filter"),
    end_date: Optional[date] = Query(None, description="End date filter"),
    db: Session = Depends(get_db)
):
    """Get all transactions with optional filtering."""
    try:
        service = TransactionService(db)
        transactions, total = await service.get_transactions(
            skip=skip,
            limit=limit,
            user_id=user_id,
            portfolio_id=portfolio_id,
            asset_id=asset_id,
            transaction_type=transaction_type,
            start_date=start_date,
            end_date=end_date
        )
        
        return TransactionListResponse(
            data=transactions,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        logger.error("Error fetching transactions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=TransactionResponse)
async def create_transaction(
    transaction: TransactionCreate,
    user_id: int = Query(1, description="User ID (placeholder)"),
    db: Session = Depends(get_db)
):
    """Create a new transaction."""
    try:
        service = TransactionService(db)
        created_transaction = await service.create_transaction(transaction, user_id)
        
        return TransactionResponse(
            data=created_transaction,
            message="Transaction created successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Error creating transaction", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{transaction_id}", response_model=TransactionResponse)
async def get_transaction(
    transaction_id: int,
    user_id: Optional[int] = Query(None, description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Get a specific transaction by ID."""
    try:
        service = TransactionService(db)
        transaction = await service.get_transaction(transaction_id, user_id)
        
        if not transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return TransactionResponse(
            data=transaction,
            message="Transaction retrieved successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error fetching transaction", transaction_id=transaction_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{transaction_id}", response_model=TransactionResponse)
async def update_transaction(
    transaction_id: int,
    transaction_update: TransactionUpdate,
    user_id: Optional[int] = Query(None, description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Update a transaction."""
    try:
        service = TransactionService(db)
        updated_transaction = await service.update_transaction(
            transaction_id, transaction_update, user_id
        )
        
        if not updated_transaction:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return TransactionResponse(
            data=updated_transaction,
            message="Transaction updated successfully"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error updating transaction", transaction_id=transaction_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{transaction_id}")
async def delete_transaction(
    transaction_id: int,
    user_id: Optional[int] = Query(None, description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Delete a transaction."""
    try:
        service = TransactionService(db)
        success = await service.delete_transaction(transaction_id, user_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Transaction not found")
        
        return {"success": True, "message": "Transaction deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error deleting transaction", transaction_id=transaction_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/portfolio/{portfolio_id}", response_model=TransactionListResponse)
async def get_portfolio_transactions(
    portfolio_id: int,
    skip: int = Query(0, ge=0, description="Number of transactions to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of transactions to return"),
    user_id: Optional[int] = Query(None, description="User ID for authorization"),
    db: Session = Depends(get_db)
):
    """Get all transactions for a specific portfolio."""
    try:
        service = TransactionService(db)
        transactions, total = await service.get_portfolio_transactions(
            portfolio_id=portfolio_id,
            skip=skip,
            limit=limit,
            user_id=user_id
        )
        
        return TransactionListResponse(
            data=transactions,
            total=total,
            page=skip // limit + 1,
            per_page=limit
        )
    except Exception as e:
        logger.error("Error fetching portfolio transactions", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/bulk", response_model=TransactionListResponse)
async def bulk_create_transactions(
    transactions: List[TransactionCreate],
    user_id: int = Query(1, description="User ID (placeholder)"),
    db: Session = Depends(get_db)
):
    """Create multiple transactions in bulk."""
    try:
        service = TransactionService(db)
        created_transactions = await service.bulk_create_transactions(transactions, user_id)
        
        return TransactionListResponse(
            data=created_transactions,
            total=len(created_transactions),
            page=1,
            per_page=len(created_transactions),
            message=f"Created {len(created_transactions)} transactions successfully"
        )
    except Exception as e:
        logger.error("Error creating bulk transactions", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
