from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import date
from decimal import Decimal
import structlog
import io

from app.core.database import get_db
from app.schemas import (
    Portfolio, PortfolioCreate, PortfolioUpdate, PortfolioResponse,
    PortfolioListResponse, PortfolioSummary
)
from app.models import Portfolio as PortfolioModel
from app.services.portfolio_service import PortfolioService
from app.services.portfolio_calculation_engine import PortfolioCalculationEngine
from app.services.data_import_export_service import DataImportExportService
from app.services.portfolio_history_service import PortfolioHistoryService

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


@router.get("/{portfolio_id}/calculate", response_model=dict)
async def calculate_portfolio_values(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Calculate and update portfolio values and performance metrics."""
    try:
        engine = PortfolioCalculationEngine(db)
        result = await engine.calculate_portfolio_values(portfolio_id)
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio values calculated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error calculating portfolio values", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/performance", response_model=dict)
async def get_portfolio_performance(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="Start date for performance calculation"),
    end_date: Optional[date] = Query(None, description="End date for performance calculation"),
    db: Session = Depends(get_db)
):
    """Get portfolio performance metrics over a time period."""
    try:
        engine = PortfolioCalculationEngine(db)
        result = await engine.calculate_portfolio_performance(
            portfolio_id, start_date, end_date
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio performance calculated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error calculating portfolio performance", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/allocation", response_model=dict)
async def get_portfolio_allocation(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get portfolio allocation by asset, sector, and asset type."""
    try:
        engine = PortfolioCalculationEngine(db)
        result = await engine.get_portfolio_allocation(portfolio_id)
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio allocation retrieved successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting portfolio allocation", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/history", response_model=dict)
async def get_portfolio_history(
    portfolio_id: int,
    days: int = Query(30, ge=1, le=365, description="Number of days of history"),
    db: Session = Depends(get_db)
):
    """Get portfolio value history over the last N days."""
    try:
        engine = PortfolioCalculationEngine(db)
        result = await engine.get_portfolio_history(portfolio_id, days)
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio history retrieved successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error getting portfolio history", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{portfolio_id}/import/transactions")
async def import_transactions(
    portfolio_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import transactions from CSV/Excel file."""
    try:
        # Check file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Only CSV and Excel files are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Initialize import service
        import_service = DataImportExportService(db)
        
        # Import based on file type
        if file.filename.endswith('.csv'):
            result = await import_service.import_transactions_from_csv(
                file_content, portfolio_id
            )
        else:
            result = await import_service.import_from_excel(
                file_content, import_type='transactions'
            )
        
        return {
            "success": result['success'],
            "data": {
                "transactions_parsed": result['total_parsed'],
                "errors": result['errors'],
                "error_count": result['error_count']
            },
            "message": f"Processed {result['total_parsed']} transactions with {result['error_count']} errors"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error importing transactions", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{portfolio_id}/import/holdings")
async def import_holdings(
    portfolio_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Import current holdings from CSV/Excel file."""
    try:
        # Check file type
        if not file.filename.endswith(('.csv', '.xlsx', '.xls')):
            raise HTTPException(
                status_code=400, 
                detail="Only CSV and Excel files are supported"
            )
        
        # Read file content
        file_content = await file.read()
        
        # Initialize import service
        import_service = DataImportExportService(db)
        
        # Import based on file type
        if file.filename.endswith('.csv'):
            result = await import_service.import_holdings_from_csv(
                file_content, portfolio_id
            )
        else:
            result = await import_service.import_from_excel(
                file_content, import_type='holdings'
            )
        
        return {
            "success": result['success'],
            "data": {
                "holdings_parsed": result['total_parsed'],
                "errors": result['errors'],
                "error_count": result['error_count']
            },
            "message": f"Processed {result['total_parsed']} holdings with {result['error_count']} errors"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error importing holdings", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/export/transactions")
async def export_transactions(
    portfolio_id: int,
    format: str = Query("csv", description="Export format: csv or excel"),
    include_details: bool = Query(True, description="Include detailed information"),
    db: Session = Depends(get_db)
):
    """Export portfolio transactions to CSV or Excel."""
    try:
        # Get transactions
        from app.services.transaction_service import TransactionService
        transaction_service = TransactionService(db)
        transactions, _ = await transaction_service.get_portfolio_transactions(portfolio_id)
        
        # Convert to dict format
        transactions_data = [
            {
                'transaction_id': t.id,
                'portfolio_id': t.portfolio_id,
                'portfolio_name': t.portfolio_name,
                'asset_id': t.asset_id,
                'asset_symbol': t.asset_symbol,
                'asset_name': t.asset_name,
                'transaction_type': t.transaction_type,
                'quantity': t.quantity,
                'price': t.price,
                'total_amount': t.total_amount,
                'fees': t.fees,
                'transaction_date': t.transaction_date.isoformat(),
                'notes': t.notes,
                'created_at': t.created_at.isoformat()
            }
            for t in transactions
        ]
        
        # Initialize export service
        export_service = DataImportExportService(db)
        
        if format.lower() == 'csv':
            # Export as CSV
            csv_content = await export_service.export_transactions_to_csv(
                transactions_data, include_details
            )
            
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_transactions.csv"
                }
            )
        
        elif format.lower() == 'excel':
            # Export as Excel
            excel_content = await export_service.export_to_excel({
                'transactions': transactions_data
            })
            
            return StreamingResponse(
                io.BytesIO(excel_content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_transactions.xlsx"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'excel'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting transactions", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/export/summary")
async def export_portfolio_summary(
    portfolio_id: int,
    format: str = Query("csv", description="Export format: csv or excel"),
    db: Session = Depends(get_db)
):
    """Export complete portfolio summary to CSV or Excel."""
    try:
        # Get portfolio calculation engine
        engine = PortfolioCalculationEngine(db)
        
        # Get all portfolio data
        portfolio_values = await engine.calculate_portfolio_values(portfolio_id)
        portfolio_allocation = await engine.get_portfolio_allocation(portfolio_id)
        portfolio_performance = await engine.calculate_portfolio_performance(portfolio_id)
        
        # Initialize export service
        export_service = DataImportExportService(db)
        
        if format.lower() == 'csv':
            # Export as CSV
            csv_content = await export_service.export_portfolio_summary_to_csv(portfolio_values)
            
            return StreamingResponse(
                io.StringIO(csv_content),
                media_type="text/csv",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_summary.csv"
                }
            )
        
        elif format.lower() == 'excel':
            # Export as Excel
            excel_content = await export_service.export_to_excel({
                'portfolio_summary': portfolio_values,
                'holdings': portfolio_values['holdings'],
                'allocation': portfolio_allocation,
                'performance': portfolio_performance
            })
            
            return StreamingResponse(
                io.BytesIO(excel_content),
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={
                    "Content-Disposition": f"attachment; filename=portfolio_{portfolio_id}_summary.xlsx"
                }
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported format. Use 'csv' or 'excel'")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error exporting portfolio summary", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/transactions")
async def get_transaction_template():
    """Get CSV template for transaction import."""
    try:
        import_service = DataImportExportService()
        template = import_service.get_transaction_template()
        
        return StreamingResponse(
            io.StringIO(template),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=transaction_template.csv"
            }
        )
        
    except Exception as e:
        logger.error("Error getting transaction template", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/templates/holdings")
async def get_holdings_template():
    """Get CSV template for holdings import."""
    try:
        import_service = DataImportExportService()
        template = import_service.get_holdings_template()
        
        return StreamingResponse(
            io.StringIO(template),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=holdings_template.csv"
            }
        )
        
    except Exception as e:
        logger.error("Error getting holdings template", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/calculate-all")
async def calculate_all_portfolios(
    db: Session = Depends(get_db)
):
    """Calculate values for all active portfolios."""
    try:
        engine = PortfolioCalculationEngine(db)
        results = await engine.calculate_all_portfolios()
        
        return {
            "success": True,
            "data": results,
            "message": f"Calculated values for {len(results)} portfolios"
        }
        
    except Exception as e:
        logger.error("Error calculating all portfolios", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{portfolio_id}/snapshot")
async def record_portfolio_snapshot(
    portfolio_id: int,
    snapshot_date: Optional[date] = Query(None, description="Date for snapshot (default: today)"),
    db: Session = Depends(get_db)
):
    """Record a daily portfolio snapshot for history tracking."""
    try:
        history_service = PortfolioHistoryService(db)
        result = await history_service.record_daily_snapshot(portfolio_id, snapshot_date)
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio snapshot recorded successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error recording portfolio snapshot", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/history/detailed")
async def get_portfolio_detailed_history(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="Start date for history"),
    end_date: Optional[date] = Query(None, description="End date for history"),
    limit: int = Query(100, ge=1, le=365, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """Get detailed portfolio history with daily snapshots."""
    try:
        history_service = PortfolioHistoryService(db)
        result = await history_service.get_portfolio_history(
            portfolio_id, start_date, end_date, limit
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio history retrieved successfully"
        }
    except Exception as e:
        logger.error("Error getting portfolio history", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/performance-metrics")
async def get_portfolio_performance_metrics(
    portfolio_id: int,
    start_date: Optional[date] = Query(None, description="Start date for metrics calculation"),
    end_date: Optional[date] = Query(None, description="End date for metrics calculation"),
    db: Session = Depends(get_db)
):
    """Get advanced portfolio performance metrics (volatility, Sharpe ratio, etc.)."""
    try:
        history_service = PortfolioHistoryService(db)
        result = await history_service.calculate_performance_metrics(
            portfolio_id, start_date, end_date
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Performance metrics calculated successfully"
        }
    except Exception as e:
        logger.error("Error calculating performance metrics", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/snapshots/all")
async def record_all_portfolios_snapshot(
    snapshot_date: Optional[date] = Query(None, description="Date for snapshot (default: today)"),
    db: Session = Depends(get_db)
):
    """Record daily snapshots for all active portfolios."""
    try:
        history_service = PortfolioHistoryService(db)
        result = await history_service.record_all_portfolios_snapshot(snapshot_date)
        
        return {
            "success": True,
            "data": result,
            "message": "All portfolio snapshots recorded successfully"
        }
    except Exception as e:
        logger.error("Error recording all portfolio snapshots", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/compare")
async def compare_portfolios(
    portfolio_ids: List[int] = Query(..., description="List of portfolio IDs to compare"),
    start_date: Optional[date] = Query(None, description="Start date for comparison"),
    end_date: Optional[date] = Query(None, description="End date for comparison"),
    db: Session = Depends(get_db)
):
    """Compare performance of multiple portfolios."""
    try:
        history_service = PortfolioHistoryService(db)
        result = await history_service.get_portfolio_comparison(
            portfolio_ids, start_date, end_date
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio comparison completed successfully"
        }
    except Exception as e:
        logger.error("Error comparing portfolios", portfolio_ids=portfolio_ids, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{portfolio_id}/holdings")
async def get_portfolio_holdings(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get all holdings for a portfolio with detailed information."""
    try:
        service = PortfolioService(db)
        holdings = await service.get_portfolio_holdings(portfolio_id)
        
        return {
            "success": True,
            "data": holdings,
            "message": "Portfolio holdings retrieved successfully"
        }
    except Exception as e:
        logger.error("Error getting portfolio holdings", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{portfolio_id}/holdings/{asset_id}")
async def update_portfolio_holding(
    portfolio_id: int,
    asset_id: int,
    quantity: Decimal = Query(..., description="New quantity for the holding"),
    current_price: Optional[Decimal] = Query(None, description="Current price per unit"),
    db: Session = Depends(get_db)
):
    """Update a specific portfolio holding."""
    try:
        service = PortfolioService(db)
        result = await service.update_portfolio_holding(
            portfolio_id, asset_id, quantity, current_price
        )
        
        return {
            "success": True,
            "data": result,
            "message": "Portfolio holding updated successfully"
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error("Error updating portfolio holding", portfolio_id=portfolio_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{user_id}/aggregation")
async def get_user_portfolio_aggregation(
    user_id: int,
    db: Session = Depends(get_db)
):
    """Get aggregated portfolio data across all portfolios for a user."""
    try:
        service = PortfolioService(db)
        result = await service.get_portfolio_aggregation(user_id)
        
        return {
            "success": True,
            "data": result,
            "message": "User portfolio aggregation retrieved successfully"
        }
    except Exception as e:
        logger.error("Error getting user portfolio aggregation", user_id=user_id, error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/calculate-all")
async def run_calculate_all_task(
    db: Session = Depends(get_db)
):
    """Run background task to calculate all portfolio values."""
    try:
        from app.services.portfolio_task_service import PortfolioTaskService
        
        result = await PortfolioTaskService.calculate_all_portfolios_task()
        
        return {
            "success": result['success'],
            "data": result,
            "message": "Portfolio calculation task completed"
        }
    except Exception as e:
        logger.error("Error running calculate all task", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/daily-snapshots")
async def run_daily_snapshots_task(
    snapshot_date: Optional[date] = Query(None, description="Date for snapshot (default: today)"),
    db: Session = Depends(get_db)
):
    """Run background task to record daily portfolio snapshots."""
    try:
        from app.services.portfolio_task_service import PortfolioTaskService
        
        result = await PortfolioTaskService.record_daily_snapshots_task(snapshot_date)
        
        return {
            "success": result['success'],
            "data": result,
            "message": "Daily snapshots task completed"
        }
    except Exception as e:
        logger.error("Error running daily snapshots task", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks/update-prices")
async def run_update_prices_task(
    db: Session = Depends(get_db)
):
    """Run background task to update portfolio holdings with latest prices."""
    try:
        from app.services.portfolio_task_service import PortfolioTaskService
        
        result = await PortfolioTaskService.update_portfolio_prices_task()
        
        return {
            "success": result['success'],
            "data": result,
            "message": "Portfolio prices update task completed"
        }
    except Exception as e:
        logger.error("Error running update prices task", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))


# ...existing endpoints...
