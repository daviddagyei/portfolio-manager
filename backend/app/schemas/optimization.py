"""
Portfolio Optimization Schemas
Pydantic models for portfolio optimization requests and responses
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class OptimizationMethod(str, Enum):
    """Portfolio optimization methods"""
    MAX_SHARPE = "max_sharpe"
    MIN_VOLATILITY = "min_volatility"
    EFFICIENT_RETURN = "efficient_return"
    EFFICIENT_RISK = "efficient_risk"
    MAX_QUADRATIC_UTILITY = "max_quadratic_utility"
    EQUAL_WEIGHT = "equal_weight"
    RISK_BUDGETING = "risk_budgeting"


class ConstraintType(str, Enum):
    """Types of optimization constraints"""
    WEIGHT_BOUNDS = "weight_bounds"
    SECTOR_LIMITS = "sector_limits"
    ASSET_LIMITS = "asset_limits"
    TURNOVER_LIMIT = "turnover_limit"


class AssetConstraint(BaseModel):
    """Individual asset constraint"""
    symbol: str = Field(..., description="Asset symbol")
    min_weight: Optional[float] = Field(None, ge=0, le=1, description="Minimum weight")
    max_weight: Optional[float] = Field(None, ge=0, le=1, description="Maximum weight")
    
    @validator('max_weight')
    def validate_weights(cls, v, values):
        if v is not None and 'min_weight' in values and values['min_weight'] is not None:
            if v < values['min_weight']:
                raise ValueError('max_weight must be greater than or equal to min_weight')
        return v


class SectorConstraint(BaseModel):
    """Sector allocation constraint"""
    sector: str = Field(..., description="Sector name")
    min_allocation: Optional[float] = Field(None, ge=0, le=1, description="Minimum sector allocation")
    max_allocation: Optional[float] = Field(None, ge=0, le=1, description="Maximum sector allocation")


class OptimizationConstraints(BaseModel):
    """Portfolio optimization constraints"""
    min_weight: float = Field(0.0, ge=0, le=1, description="Global minimum weight per asset")
    max_weight: float = Field(1.0, ge=0, le=1, description="Global maximum weight per asset")
    asset_constraints: Optional[List[AssetConstraint]] = Field(None, description="Individual asset constraints")
    sector_constraints: Optional[List[SectorConstraint]] = Field(None, description="Sector constraints")
    max_turnover: Optional[float] = Field(None, ge=0, description="Maximum portfolio turnover")
    
    @validator('max_weight')
    def validate_global_weights(cls, v, values):
        if 'min_weight' in values and v < values['min_weight']:
            raise ValueError('max_weight must be greater than or equal to min_weight')
        return v


class OptimizationRequest(BaseModel):
    """Portfolio optimization request"""
    asset_symbols: List[str] = Field(..., min_items=2, description="List of asset symbols to optimize")
    optimization_method: OptimizationMethod = Field(..., description="Optimization objective")
    lookback_days: int = Field(252, ge=30, le=1260, description="Days of historical data")
    risk_free_rate: float = Field(0.02, ge=0, le=0.1, description="Risk-free rate")
    target_return: Optional[float] = Field(None, description="Target return for efficient_return method")
    target_volatility: Optional[float] = Field(None, gt=0, description="Target volatility for efficient_risk method")
    constraints: Optional[OptimizationConstraints] = Field(None, description="Optimization constraints")
    risk_aversion: float = Field(1.0, gt=0, description="Risk aversion parameter for utility maximization")


class EfficientFrontierRequest(BaseModel):
    """Efficient frontier calculation request"""
    asset_symbols: List[str] = Field(..., min_items=2, description="List of asset symbols")
    lookback_days: int = Field(252, ge=30, le=1260, description="Days of historical data")
    risk_free_rate: float = Field(0.02, ge=0, le=0.1, description="Risk-free rate")
    n_points: int = Field(100, ge=10, le=500, description="Number of frontier points")
    constraints: Optional[OptimizationConstraints] = Field(None, description="Optimization constraints")


class PortfolioWeights(BaseModel):
    """Portfolio weights"""
    weights: Dict[str, float] = Field(..., description="Asset weights")
    
    @validator('weights')
    def validate_weights_sum(cls, v):
        total = sum(v.values())
        if not (0.95 <= total <= 1.05):  # Allow small tolerance
            raise ValueError('Portfolio weights must sum to approximately 1.0')
        return v


class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics"""
    expected_return: float = Field(..., description="Expected annual return")
    volatility: float = Field(..., description="Expected annual volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: Optional[float] = Field(None, description="Maximum drawdown")
    var_95: Optional[float] = Field(None, description="Value at Risk (95%)")
    beta: Optional[float] = Field(None, description="Portfolio beta")


class OptimizedPortfolio(BaseModel):
    """Optimized portfolio result"""
    optimization_method: OptimizationMethod = Field(..., description="Optimization method used")
    weights: Dict[str, float] = Field(..., description="Optimal portfolio weights")
    metrics: PortfolioMetrics = Field(..., description="Portfolio performance metrics")
    optimization_date: datetime = Field(..., description="Optimization timestamp")
    risk_free_rate: float = Field(..., description="Risk-free rate used")
    target_return: Optional[float] = Field(None, description="Target return if applicable")
    target_volatility: Optional[float] = Field(None, description="Target volatility if applicable")


class EfficientFrontierPoint(BaseModel):
    """Single point on efficient frontier"""
    expected_return: float = Field(..., description="Expected return")
    volatility: float = Field(..., description="Volatility")
    weights: Dict[str, float] = Field(..., description="Portfolio weights")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")


class KeyPortfolio(BaseModel):
    """Key optimization portfolio"""
    name: str = Field(..., description="Portfolio name")
    weights: Dict[str, float] = Field(..., description="Portfolio weights")
    expected_return: float = Field(..., description="Expected return")
    volatility: float = Field(..., description="Volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")


class EfficientFrontierResponse(BaseModel):
    """Efficient frontier response"""
    frontier_points: List[EfficientFrontierPoint] = Field(..., description="Efficient frontier points")
    key_portfolios: List[KeyPortfolio] = Field(..., description="Key optimization portfolios")
    assets: List[str] = Field(..., description="Asset symbols used")
    optimization_date: datetime = Field(..., description="Optimization timestamp")
    risk_free_rate: float = Field(..., description="Risk-free rate used")


class DiscreteAllocationRequest(BaseModel):
    """Discrete allocation request"""
    weights: Dict[str, float] = Field(..., description="Portfolio weights")
    total_portfolio_value: float = Field(..., gt=0, description="Total portfolio value")
    latest_prices: Optional[Dict[str, float]] = Field(None, description="Latest asset prices")


class TradeRecommendation(BaseModel):
    """Individual trade recommendation"""
    symbol: str = Field(..., description="Asset symbol")
    action: str = Field(..., description="Buy or sell action")
    current_weight: float = Field(..., description="Current portfolio weight")
    target_weight: float = Field(..., description="Target portfolio weight")
    weight_difference: float = Field(..., description="Weight difference")
    dollar_amount: float = Field(..., description="Dollar amount to trade")
    shares_to_trade: float = Field(..., description="Number of shares to trade")
    current_price: float = Field(..., description="Current asset price")


class RebalancingRequest(BaseModel):
    """Portfolio rebalancing request"""
    portfolio_id: int = Field(..., description="Portfolio ID")
    target_weights: Dict[str, float] = Field(..., description="Target allocation weights")
    tolerance: float = Field(0.05, ge=0.01, le=0.2, description="Rebalancing tolerance threshold")


class RebalancingResponse(BaseModel):
    """Portfolio rebalancing response"""
    rebalancing_needed: bool = Field(..., description="Whether rebalancing is needed")
    current_weights: Dict[str, float] = Field(..., description="Current portfolio weights")
    target_weights: Dict[str, float] = Field(..., description="Target portfolio weights")
    trades: List[TradeRecommendation] = Field(..., description="Trade recommendations")
    total_portfolio_value: float = Field(..., description="Total portfolio value")
    tolerance: float = Field(..., description="Rebalancing tolerance")
    analysis_date: datetime = Field(..., description="Analysis timestamp")


class ScenarioDefinition(BaseModel):
    """Scenario analysis definition"""
    name: str = Field(..., description="Scenario name")
    description: str = Field(..., description="Scenario description")
    return_shock: Optional[Dict[str, Any]] = Field(None, description="Return shock parameters")
    volatility_shock: Optional[Dict[str, Any]] = Field(None, description="Volatility shock parameters")
    correlation_shock: Optional[Dict[str, Any]] = Field(None, description="Correlation shock parameters")


class ScenarioResult(BaseModel):
    """Scenario analysis result"""
    description: str = Field(..., description="Scenario description")
    annualized_return: float = Field(..., description="Expected annual return")
    volatility: float = Field(..., description="Expected volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    var_95: float = Field(..., description="Value at Risk (95%)")
    total_return: float = Field(..., description="Total return over period")


class ScenarioAnalysisRequest(BaseModel):
    """Scenario analysis request"""
    weights: Dict[str, float] = Field(..., description="Portfolio weights")
    asset_symbols: List[str] = Field(..., description="Asset symbols")
    scenarios: List[ScenarioDefinition] = Field(..., description="Scenario definitions")
    lookback_days: int = Field(252, ge=30, description="Days of historical data")


class ScenarioAnalysisResponse(BaseModel):
    """Scenario analysis response"""
    scenarios: Dict[str, ScenarioResult] = Field(..., description="Scenario results")
    base_portfolio_weights: Dict[str, float] = Field(..., description="Base portfolio weights")
    analysis_date: datetime = Field(..., description="Analysis timestamp")


class RiskBudgetingRequest(BaseModel):
    """Risk budgeting request"""
    asset_symbols: List[str] = Field(..., description="Asset symbols")
    risk_budget: Dict[str, float] = Field(..., description="Target risk contribution by asset")
    lookback_days: int = Field(252, ge=30, description="Days of historical data")


class RiskBudgetingResponse(BaseModel):
    """Risk budgeting response"""
    weights: Dict[str, float] = Field(..., description="Risk budgeting portfolio weights")
    risk_contributions: Dict[str, float] = Field(..., description="Actual risk contributions")
    target_risk_budget: Dict[str, float] = Field(..., description="Target risk budget")
    portfolio_volatility: float = Field(..., description="Portfolio volatility")


class DiscreteAllocationResponse(BaseModel):
    """Discrete allocation response"""
    allocation: Dict[str, int] = Field(..., description="Number of shares to buy")
    leftover_cash: float = Field(..., description="Leftover cash after allocation")
    total_allocated: float = Field(..., description="Total amount allocated")
    allocation_percentage: float = Field(..., description="Percentage of portfolio allocated")
    total_value: float = Field(..., description="Total portfolio value")


class OptimizationError(BaseModel):
    """Optimization error response"""
    error_type: str = Field(..., description="Type of error")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")


class BacktestRequest(BaseModel):
    """Portfolio backtest request"""
    weights: Dict[str, float] = Field(..., description="Portfolio weights to backtest")
    start_date: datetime = Field(..., description="Backtest start date")
    end_date: datetime = Field(..., description="Backtest end date")
    rebalancing_frequency: str = Field("monthly", description="Rebalancing frequency")
    transaction_costs: float = Field(0.001, ge=0, le=0.1, description="Transaction costs as percentage")


class BacktestResult(BaseModel):
    """Portfolio backtest result"""
    total_return: float = Field(..., description="Total return over period")
    annualized_return: float = Field(..., description="Annualized return")
    volatility: float = Field(..., description="Annualized volatility")
    sharpe_ratio: float = Field(..., description="Sharpe ratio")
    max_drawdown: float = Field(..., description="Maximum drawdown")
    calmar_ratio: float = Field(..., description="Calmar ratio")
    win_rate: float = Field(..., description="Percentage of winning periods")
    portfolio_values: List[Dict[str, Any]] = Field(..., description="Portfolio value time series")
    returns: List[float] = Field(..., description="Portfolio returns")
    dates: List[datetime] = Field(..., description="Dates for returns")


class BacktestResponse(BaseModel):
    """Portfolio backtest response"""
    backtest_result: BacktestResult = Field(..., description="Backtest results")
    portfolio_weights: Dict[str, float] = Field(..., description="Portfolio weights tested")
    backtest_period: Dict[str, datetime] = Field(..., description="Backtest period")
    parameters: Dict[str, Any] = Field(..., description="Backtest parameters")


# Response wrapper
class OptimizationResponse(BaseModel):
    """Generic optimization response wrapper"""
    success: bool = Field(..., description="Success status")
    data: Optional[Union[
        OptimizedPortfolio,
        EfficientFrontierResponse,
        RebalancingResponse,
        ScenarioAnalysisResponse,
        RiskBudgetingResponse,
        DiscreteAllocationResponse,
        BacktestResponse
    ]] = Field(None, description="Response data")
    error: Optional[OptimizationError] = Field(None, description="Error information")
    message: str = Field(..., description="Response message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
