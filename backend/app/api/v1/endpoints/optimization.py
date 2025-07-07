from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
import structlog

from app.core.database import get_db
from app.services.portfolio_optimization_service import PortfolioOptimizationService
from app.schemas.optimization import (
    OptimizationRequest, OptimizationResponse, OptimizedPortfolio,
    EfficientFrontierRequest, EfficientFrontierResponse,
    RebalancingRequest, RebalancingResponse,
    ScenarioAnalysisRequest, ScenarioAnalysisResponse,
    RiskBudgetingRequest, RiskBudgetingResponse,
    DiscreteAllocationRequest, DiscreteAllocationResponse,
    BacktestRequest, BacktestResponse,
    OptimizationError
)

logger = structlog.get_logger()

router = APIRouter()


@router.post("/efficient-frontier", response_model=OptimizationResponse)
async def calculate_efficient_frontier(
    request: EfficientFrontierRequest,
    db: Session = Depends(get_db)
):
    """Calculate efficient frontier for given assets."""
    try:
        service = PortfolioOptimizationService(db)
        
        # Get asset data
        price_data, returns_data = await service.get_asset_data(
            request.asset_symbols, 
            request.lookback_days
        )
        
        # Calculate efficient frontier
        frontier_data = service.calculate_efficient_frontier(
            returns_data,
            request.risk_free_rate,
            request.n_points,
            request.constraints.min_weight if request.constraints else 0.0,
            request.constraints.max_weight if request.constraints else 1.0
        )
        
        # Format response
        frontier_points = [
            {
                "expected_return": ret,
                "volatility": vol,
                "weights": weights,
                "sharpe_ratio": (ret - request.risk_free_rate) / vol if vol > 0 else 0
            }
            for ret, vol, weights in zip(
                frontier_data["frontier"]["returns"],
                frontier_data["frontier"]["volatility"],
                frontier_data["frontier"]["weights"]
            )
        ]
        
        key_portfolios = [
            {
                "name": portfolio["name"],
                "weights": portfolio["weights"],
                "expected_return": portfolio["expected_return"],
                "volatility": portfolio["volatility"],
                "sharpe_ratio": portfolio["sharpe_ratio"]
            }
            for portfolio in frontier_data["key_portfolios"].values()
        ]
        
        response_data = EfficientFrontierResponse(
            frontier_points=frontier_points,
            key_portfolios=key_portfolios,
            assets=frontier_data["assets"],
            optimization_date=frontier_data["optimization_date"],
            risk_free_rate=frontier_data["risk_free_rate"]
        )
        
        return OptimizationResponse(
            success=True,
            data=response_data,
            message="Efficient frontier calculated successfully"
        )
        
    except Exception as e:
        logger.error("Error calculating efficient frontier", error=str(e))
        return OptimizationResponse(
            success=False,
            error=OptimizationError(
                error_type="calculation_error",
                message=str(e)
            ),
            message="Failed to calculate efficient frontier"
        )


@router.post("/optimize", response_model=OptimizationResponse)
async def optimize_portfolio(
    request: OptimizationRequest,
    db: Session = Depends(get_db)
):
    """Optimize portfolio allocation."""
    try:
        service = PortfolioOptimizationService(db)
        
        # Get asset data
        price_data, returns_data = await service.get_asset_data(
            request.asset_symbols, 
            request.lookback_days
        )
        
        # Prepare constraints
        constraints = {}
        if request.constraints:
            constraints["min_weight"] = request.constraints.min_weight
            constraints["max_weight"] = request.constraints.max_weight
            
            if request.constraints.asset_constraints:
                constraints["asset_constraints"] = {
                    ac.symbol: {"min": ac.min_weight, "max": ac.max_weight}
                    for ac in request.constraints.asset_constraints
                }
            
            if request.constraints.sector_constraints:
                constraints["sector_constraints"] = {
                    sc.sector: {"min": sc.min_allocation, "max": sc.max_allocation}
                    for sc in request.constraints.sector_constraints
                }
        
        # Optimize portfolio
        optimization_result = service.optimize_portfolio(
            returns_data,
            request.optimization_method.value,
            request.target_return,
            request.target_volatility,
            request.risk_free_rate,
            constraints if constraints else None
        )
        
        # Format response
        portfolio_metrics = {
            "expected_return": optimization_result["expected_return"],
            "volatility": optimization_result["volatility"],
            "sharpe_ratio": optimization_result["sharpe_ratio"]
        }
        
        response_data = OptimizedPortfolio(
            optimization_method=request.optimization_method,
            weights=optimization_result["weights"],
            metrics=portfolio_metrics,
            optimization_date=optimization_result["optimization_date"],
            risk_free_rate=optimization_result["risk_free_rate"],
            target_return=optimization_result.get("target_return"),
            target_volatility=optimization_result.get("target_volatility")
        )
        
        return OptimizationResponse(
            success=True,
            data=response_data,
            message="Portfolio optimized successfully"
        )
        
    except Exception as e:
        logger.error("Error optimizing portfolio", error=str(e))
        return OptimizationResponse(
            success=False,
            error=OptimizationError(
                error_type="optimization_error",
                message=str(e)
            ),
            message="Failed to optimize portfolio"
        )


@router.post("/rebalancing", response_model=OptimizationResponse)
async def generate_rebalancing_suggestions(
    request: RebalancingRequest,
    db: Session = Depends(get_db)
):
    """Generate portfolio rebalancing suggestions."""
    try:
        service = PortfolioOptimizationService(db)
        
        rebalancing_data = await service.generate_rebalancing_suggestions(
            request.portfolio_id,
            request.target_weights,
            request.tolerance
        )
        
        response_data = RebalancingResponse(**rebalancing_data)
        
        return OptimizationResponse(
            success=True,
            data=response_data,
            message="Rebalancing suggestions generated successfully"
        )
        
    except Exception as e:
        logger.error("Error generating rebalancing suggestions", error=str(e))
        return OptimizationResponse(
            success=False,
            error=OptimizationError(
                error_type="rebalancing_error",
                message=str(e)
            ),
            message="Failed to generate rebalancing suggestions"
        )


@router.post("/scenario-analysis", response_model=OptimizationResponse)
async def run_scenario_analysis(
    request: ScenarioAnalysisRequest,
    db: Session = Depends(get_db)
):
    """Run what-if scenario analysis on portfolio."""
    try:
        service = PortfolioOptimizationService(db)
        
        # Get asset data
        _, returns_data = await service.get_asset_data(
            request.asset_symbols, 
            request.lookback_days
        )
        
        # Convert scenario definitions to dict format
        scenarios = [
            {
                "name": scenario.name,
                "description": scenario.description,
                "return_shock": scenario.return_shock,
                "volatility_shock": scenario.volatility_shock,
                "correlation_shock": scenario.correlation_shock
            }
            for scenario in request.scenarios
        ]
        
        scenario_results = service.run_scenario_analysis(
            request.weights,
            returns_data,
            scenarios
        )
        
        response_data = ScenarioAnalysisResponse(**scenario_results)
        
        return OptimizationResponse(
            success=True,
            data=response_data,
            message="Scenario analysis completed successfully"
        )
        
    except Exception as e:
        logger.error("Error running scenario analysis", error=str(e))
        return OptimizationResponse(
            success=False,
            error=OptimizationError(
                error_type="scenario_error",
                message=str(e)
            ),
            message="Failed to run scenario analysis"
        )


@router.post("/risk-budgeting", response_model=OptimizationResponse)
async def calculate_risk_budgeting(
    request: RiskBudgetingRequest,
    db: Session = Depends(get_db)
):
    """Calculate risk budgeting portfolio allocation."""
    try:
        service = PortfolioOptimizationService(db)
        
        # Get asset data
        _, returns_data = await service.get_asset_data(
            request.asset_symbols, 
            request.lookback_days
        )
        
        risk_budgeting_result = service.calculate_risk_budgeting(
            returns_data,
            request.risk_budget
        )
        
        response_data = RiskBudgetingResponse(**risk_budgeting_result)
        
        return OptimizationResponse(
            success=True,
            data=response_data,
            message="Risk budgeting allocation calculated successfully"
        )
        
    except Exception as e:
        logger.error("Error calculating risk budgeting", error=str(e))
        return OptimizationResponse(
            success=False,
            error=OptimizationError(
                error_type="risk_budgeting_error",
                message=str(e)
            ),
            message="Failed to calculate risk budgeting allocation"
        )


@router.post("/discrete-allocation", response_model=OptimizationResponse)
async def calculate_discrete_allocation(
    request: DiscreteAllocationRequest,
    db: Session = Depends(get_db)
):
    """Calculate discrete allocation for actual trading."""
    try:
        service = PortfolioOptimizationService(db)
        
        # Get latest prices if not provided
        latest_prices = request.latest_prices
        if not latest_prices:
            # Get current prices for assets
            asset_symbols = list(request.weights.keys())
            latest_prices = {}
            
            for symbol in asset_symbols:
                try:
                    price = await service.market_service.get_latest_price(symbol)
                    if price:
                        latest_prices[symbol] = price
                except Exception:
                    continue
        
        if not latest_prices:
            raise ValueError("No price data available for discrete allocation")
        
        allocation_result = service.calculate_discrete_allocation(
            request.weights,
            latest_prices,
            request.total_portfolio_value
        )
        
        response_data = DiscreteAllocationResponse(**allocation_result)
        
        return OptimizationResponse(
            success=True,
            data=response_data,
            message="Discrete allocation calculated successfully"
        )
        
    except Exception as e:
        logger.error("Error calculating discrete allocation", error=str(e))
        return OptimizationResponse(
            success=False,
            error=OptimizationError(
                error_type="allocation_error",
                message=str(e)
            ),
            message="Failed to calculate discrete allocation"
        )


@router.get("/methods")
async def get_optimization_methods():
    """Get available optimization methods."""
    try:
        methods = [
            {
                "method": "max_sharpe",
                "name": "Maximum Sharpe Ratio",
                "description": "Maximize risk-adjusted returns (Sharpe ratio)",
                "requires_target": False
            },
            {
                "method": "min_volatility",
                "name": "Minimum Volatility",
                "description": "Minimize portfolio volatility",
                "requires_target": False
            },
            {
                "method": "efficient_return",
                "name": "Efficient Return",
                "description": "Minimize risk for target return",
                "requires_target": True,
                "target_type": "return"
            },
            {
                "method": "efficient_risk",
                "name": "Efficient Risk",
                "description": "Maximize return for target volatility",
                "requires_target": True,
                "target_type": "volatility"
            },
            {
                "method": "max_quadratic_utility",
                "name": "Maximum Utility",
                "description": "Maximize quadratic utility function",
                "requires_target": False
            },
            {
                "method": "equal_weight",
                "name": "Equal Weight",
                "description": "Equal allocation across all assets",
                "requires_target": False
            },
            {
                "method": "risk_budgeting",
                "name": "Risk Budgeting",
                "description": "Allocate based on risk contribution targets",
                "requires_target": True,
                "target_type": "risk_budget"
            }
        ]
        
        return {
            "success": True,
            "data": methods,
            "message": "Optimization methods retrieved successfully"
        }
        
    except Exception as e:
        logger.error("Error getting optimization methods", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/portfolio/{portfolio_id}/current-allocation")
async def get_current_portfolio_allocation(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get current portfolio allocation for optimization."""
    try:
        from app.services.portfolio_calculation_engine import PortfolioCalculationEngine
        
        calc_engine = PortfolioCalculationEngine(db)
        allocation_data = await calc_engine.get_portfolio_allocation(portfolio_id)
        
        # Convert to weights format
        current_weights = {}
        if allocation_data and allocation_data.get("by_asset"):
            for asset in allocation_data["by_asset"]:
                current_weights[asset["symbol"]] = float(asset["percentage"]) / 100
        
        return {
            "success": True,
            "data": {
                "portfolio_id": portfolio_id,
                "current_weights": current_weights,
                "total_value": allocation_data.get("total_value", 0),
                "last_updated": allocation_data.get("last_updated")
            },
            "message": "Current portfolio allocation retrieved successfully"
        }
        
    except Exception as e:
        logger.error("Error getting current portfolio allocation", error=str(e))
        raise HTTPException(status_code=500, detail="Internal server error")
