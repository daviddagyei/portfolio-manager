"""
Risk Analytics API Endpoints

This module provides FastAPI endpoints for the comprehensive risk analytics service.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
import numpy as np
from pydantic import BaseModel, Field

from ....services.risk_analytics_service import (
    RiskAnalyticsService,
    ComprehensiveRiskMetrics,
    RiskMetrics,
    CorrelationAnalysis,
    RiskLevel,
    RollingMetrics
)

router = APIRouter(prefix="/risk-analytics", tags=["risk-analytics"])


class RiskAnalysisRequest(BaseModel):
    """Request model for risk analysis"""
    returns_data: List[Dict[str, Any]] = Field(description="Returns data as list of dictionaries")
    benchmark_data: Optional[List[Dict[str, Any]]] = Field(None, description="Benchmark data (optional)")
    risk_free_rate: float = Field(0.02, description="Risk-free rate")
    rolling_window: int = Field(252, description="Rolling window for calculations")
    var_confidence: float = Field(0.05, description="VaR confidence level")
    include_benchmark: bool = Field(True, description="Include benchmark comparison")
    include_correlation: bool = Field(True, description="Include correlation analysis")


class RiskReportRequest(BaseModel):
    """Request model for risk report generation"""
    returns_data: List[Dict[str, Any]] = Field(description="Returns data as list of dictionaries")
    portfolio_name: str = Field("Portfolio", description="Name of the portfolio")
    benchmark_data: Optional[List[Dict[str, Any]]] = Field(None, description="Benchmark data (optional)")
    risk_free_rate: float = Field(0.02, description="Risk-free rate")
    rolling_window: int = Field(252, description="Rolling window for calculations")


class RiskAnalysisResponse(BaseModel):
    """Response model for risk analysis"""
    success: bool
    data: Optional[ComprehensiveRiskMetrics] = None
    error: Optional[str] = None


class RiskReportResponse(BaseModel):
    """Response model for risk report"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/comprehensive-analysis", response_model=RiskAnalysisResponse)
async def comprehensive_risk_analysis(request: RiskAnalysisRequest):
    """
    Perform comprehensive risk analysis on portfolio returns
    
    This endpoint calculates a full suite of risk metrics including:
    - Basic risk metrics (Sharpe ratio, volatility, max drawdown, etc.)
    - Performance metrics (returns, skewness, kurtosis)
    - Rolling metrics (rolling Sharpe, volatility, VaR)
    - VaR calculations (historical, parametric, Monte Carlo)
    - Benchmark comparison (if benchmark data provided)
    - Correlation analysis (if multiple assets)
    """
    try:
        # Validate and convert data to DataFrame
        if not request.returns_data:
            raise HTTPException(status_code=400, detail="Returns data cannot be empty")
        
        returns_df = pd.DataFrame(request.returns_data)
        
        # Parse dates if present
        if 'date' in returns_df.columns:
            returns_df['date'] = pd.to_datetime(returns_df['date'])
            returns_df.set_index('date', inplace=True)
        
        benchmark_df = None
        if request.benchmark_data:
            benchmark_df = pd.DataFrame(request.benchmark_data)
            if 'date' in benchmark_df.columns:
                benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
                benchmark_df.set_index('date', inplace=True)
        
        # Initialize service
        service = RiskAnalyticsService()
        service.initialize_with_data(
            returns_df, 
            benchmark_df, 
            request.risk_free_rate
        )
        
        # Calculate comprehensive metrics
        metrics = service.calculate_comprehensive_risk_metrics(
            rolling_window=request.rolling_window,
            var_confidence=request.var_confidence,
            include_benchmark=request.include_benchmark,
            include_correlation=request.include_correlation
        )
        
        return RiskAnalysisResponse(success=True, data=metrics)
        
    except Exception as e:
        return RiskAnalysisResponse(success=False, error=str(e))


@router.post("/risk-report", response_model=RiskReportResponse)
async def generate_risk_report(request: RiskReportRequest):
    """
    Generate a comprehensive risk report
    
    This endpoint generates a detailed risk report including:
    - Executive summary with key metrics
    - Detailed risk analysis
    - Risk level assessment
    - Recommendations for improvement
    """
    try:
        # Validate and convert data to DataFrame
        if not request.returns_data:
            raise HTTPException(status_code=400, detail="Returns data cannot be empty")
        
        returns_df = pd.DataFrame(request.returns_data)
        
        # Parse dates if present
        if 'date' in returns_df.columns:
            returns_df['date'] = pd.to_datetime(returns_df['date'])
            returns_df.set_index('date', inplace=True)
        
        benchmark_df = None
        if request.benchmark_data:
            benchmark_df = pd.DataFrame(request.benchmark_data)
            if 'date' in benchmark_df.columns:
                benchmark_df['date'] = pd.to_datetime(benchmark_df['date'])
                benchmark_df.set_index('date', inplace=True)
        
        # Initialize service
        service = RiskAnalyticsService()
        service.initialize_with_data(
            returns_df, 
            benchmark_df, 
            request.risk_free_rate
        )
        
        # Generate report
        report = service.generate_risk_report(
            request.portfolio_name, 
            request.rolling_window
        )
        
        return RiskReportResponse(success=True, data=report)
        
    except Exception as e:
        return RiskReportResponse(success=False, error=str(e))


@router.get("/risk-metrics/{portfolio_id}")
async def get_portfolio_risk_metrics(
    portfolio_id: int,
    risk_free_rate: float = Query(0.02, description="Risk-free rate"),
    rolling_window: int = Query(252, description="Rolling window for calculations")
):
    """
    Get risk metrics for a specific portfolio
    
    This endpoint retrieves risk metrics for a portfolio stored in the database.
    """
    try:
        from sqlalchemy.orm import Session
        from ....core.database import SessionLocal
        from ....services.portfolio_service import PortfolioService
        from ....services.portfolio_calculation_engine import PortfolioCalculationEngine
        
        # Get database session
        db: Session = SessionLocal()
        try:
            # Get portfolio service
            portfolio_service = PortfolioService(db)
            
            # Fetch portfolio
            portfolio = await portfolio_service.get_portfolio(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Get portfolio calculation engine
            calc_engine = PortfolioCalculationEngine(db)
            
            # Calculate portfolio returns
            returns_data = await calc_engine.calculate_portfolio_returns(portfolio_id)
            
            if returns_data is None or len(returns_data) < 30:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient historical data for risk analysis (minimum 30 days required)"
                )
            
            # Initialize risk analytics service
            service = RiskAnalyticsService()
            service.initialize_with_data(returns_data, risk_free_rate=risk_free_rate)
            
            # Calculate comprehensive metrics
            metrics = service.calculate_comprehensive_risk_metrics(
                rolling_window=rolling_window,
                include_benchmark=False,
                include_correlation=False
            )
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "data": metrics
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/benchmark-comparison/{portfolio_id}")
async def get_benchmark_comparison(
    portfolio_id: int,
    benchmark_symbol: str = Query("SPY", description="Benchmark symbol"),
    risk_free_rate: float = Query(0.02, description="Risk-free rate")
):
    """
    Get benchmark comparison for a specific portfolio
    
    This endpoint compares portfolio performance against a benchmark.
    """
    try:
        from sqlalchemy.orm import Session
        from ....core.database import SessionLocal
        from ....services.portfolio_service import PortfolioService
        from ....services.portfolio_calculation_engine import PortfolioCalculationEngine
        from ....services.market_data_service import MarketDataService
        
        # Get database session
        db: Session = SessionLocal()
        try:
            # Get portfolio service
            portfolio_service = PortfolioService(db)
            
            # Fetch portfolio
            portfolio = await portfolio_service.get_portfolio(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Get portfolio calculation engine
            calc_engine = PortfolioCalculationEngine(db)
            
            # Calculate portfolio returns
            returns_data = await calc_engine.calculate_portfolio_returns(portfolio_id)
            
            if returns_data is None or len(returns_data) < 30:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient historical data for benchmark comparison (minimum 30 days required)"
                )
            
            # Get market data service for benchmark
            market_service = MarketDataService()
            
            # Get benchmark data
            start_date = returns_data.index[0]
            end_date = returns_data.index[-1]
            
            benchmark_data = await market_service.get_asset_returns(
                benchmark_symbol, 
                start_date, 
                end_date
            )
            
            if benchmark_data is None or len(benchmark_data) < 30:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient benchmark data for {benchmark_symbol}"
                )
            
            # Initialize risk analytics service
            service = RiskAnalyticsService()
            service.initialize_with_data(
                returns_data, 
                benchmark_data, 
                risk_free_rate=risk_free_rate
            )
            
            # Calculate comprehensive metrics with benchmark
            metrics = service.calculate_comprehensive_risk_metrics(
                include_benchmark=True,
                include_correlation=False
            )
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "benchmark_symbol": benchmark_symbol,
                "data": metrics
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/correlation-matrix/{portfolio_id}")
async def get_correlation_matrix(
    portfolio_id: int,
    method: str = Query("pearson", description="Correlation method"),
    threshold: float = Query(0.7, description="High correlation threshold")
):
    """
    Get correlation matrix for portfolio assets
    
    This endpoint calculates and returns the correlation matrix for assets
    in a portfolio.
    """
    try:
        from sqlalchemy.orm import Session
        from ....core.database import SessionLocal
        from ....services.portfolio_service import PortfolioService
        from ....services.portfolio_calculation_engine import PortfolioCalculationEngine
        
        # Get database session
        db: Session = SessionLocal()
        try:
            # Get portfolio service
            portfolio_service = PortfolioService(db)
            
            # Fetch portfolio
            portfolio = await portfolio_service.get_portfolio(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Get portfolio calculation engine
            calc_engine = PortfolioCalculationEngine(db)
            
            # Get portfolio holdings and their returns
            holdings = await calc_engine.get_portfolio_holdings(portfolio_id)
            if not holdings or len(holdings) < 2:
                raise HTTPException(
                    status_code=400, 
                    detail="Portfolio must have at least 2 assets for correlation analysis"
                )
            
            # Get asset returns data
            asset_returns = await calc_engine.calculate_asset_returns(portfolio_id)
            
            if asset_returns is None or len(asset_returns) < 30:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient historical data for correlation analysis (minimum 30 days required)"
                )
            
            # Initialize correlation analyzer
            from ....services.risk_analytics_service import CorrelationAnalyzer
            corr_analyzer = CorrelationAnalyzer(asset_returns)
            
            # Calculate correlation matrix
            correlation_matrix = corr_analyzer.calculate_correlation_matrix(method=method)
            
            # Find high correlation pairs
            high_corr_pairs = corr_analyzer.find_correlation_pairs(threshold=threshold)
            
            # Calculate correlation statistics
            corr_stats = corr_analyzer.correlation_statistics()
            
            # Calculate diversification ratio
            diversification_ratio = corr_analyzer.diversification_ratio()
            
            # Cluster assets
            clusters = corr_analyzer.correlation_clustering(n_clusters=min(3, len(asset_returns.columns)))
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "method": method,
                "threshold": threshold,
                "correlation_matrix": correlation_matrix.to_dict(),
                "high_correlation_pairs": [
                    {
                        "asset1": pair[0],
                        "asset2": pair[1],
                        "correlation": pair[2]
                    }
                    for pair in high_corr_pairs
                ],
                "correlation_statistics": corr_stats,
                "diversification_ratio": diversification_ratio,
                "asset_clusters": clusters,
                "assets": list(asset_returns.columns),
                "data_points": len(asset_returns)
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/var-analysis/{portfolio_id}")
async def get_var_analysis(
    portfolio_id: int,
    confidence_levels: List[float] = Query([0.05, 0.01], description="VaR confidence levels"),
    methods: List[str] = Query(["historical", "parametric", "monte_carlo"], description="VaR methods")
):
    """
    Get Value at Risk analysis for a portfolio
    
    This endpoint calculates VaR using multiple methods and confidence levels.
    """
    try:
        from sqlalchemy.orm import Session
        from ....core.database import SessionLocal
        from ....services.portfolio_service import PortfolioService
        from ....services.portfolio_calculation_engine import PortfolioCalculationEngine
        
        # Get database session
        db: Session = SessionLocal()
        try:
            # Get portfolio service
            portfolio_service = PortfolioService(db)
            
            # Fetch portfolio
            portfolio = await portfolio_service.get_portfolio(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Get portfolio calculation engine
            calc_engine = PortfolioCalculationEngine(db)
            
            # Calculate portfolio returns
            returns_data = await calc_engine.calculate_portfolio_returns(portfolio_id)
            
            if returns_data is None or len(returns_data) < 30:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient historical data for VaR analysis (minimum 30 days required)"
                )
            
            # Initialize VaR calculator
            from ....services.risk_analytics_service import VaRCalculator
            var_calculator = VaRCalculator(returns_data.iloc[:, 0])
            
            # Calculate VaR for all methods and confidence levels
            var_results = {}
            
            for confidence in confidence_levels:
                confidence_key = f"{confidence*100:.0f}%"
                var_results[confidence_key] = {}
                
                if "historical" in methods:
                    var_results[confidence_key]["historical"] = var_calculator.historical_var(confidence)
                
                if "parametric" in methods:
                    var_results[confidence_key]["parametric"] = var_calculator.parametric_var(confidence)
                
                if "monte_carlo" in methods:
                    var_results[confidence_key]["monte_carlo"] = var_calculator.monte_carlo_var(confidence)
                
                # Always calculate CVaR
                var_results[confidence_key]["cvar"] = var_calculator.conditional_var(confidence)
            
            # Add backtesting results
            backtesting_results = {}
            for confidence in confidence_levels:
                confidence_key = f"{confidence*100:.0f}%"
                backtesting_results[confidence_key] = var_calculator.var_backtesting(confidence)
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "confidence_levels": confidence_levels,
                "methods": methods,
                "var_results": var_results,
                "backtesting_results": backtesting_results,
                "data_points": len(returns_data)
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/rolling-metrics/{portfolio_id}")
async def get_rolling_metrics(
    portfolio_id: int,
    metrics: List[str] = Query(["sharpe", "volatility", "max_drawdown", "var"], description="Rolling metrics to calculate"),
    window: int = Query(252, description="Rolling window size"),
    risk_free_rate: float = Query(0.02, description="Risk-free rate")
):
    """
    Get rolling metrics for a portfolio
    
    This endpoint calculates rolling risk metrics over time.
    """
    try:
        from sqlalchemy.orm import Session
        from ....core.database import SessionLocal
        from ....services.portfolio_service import PortfolioService
        from ....services.portfolio_calculation_engine import PortfolioCalculationEngine
        
        # Get database session
        db: Session = SessionLocal()
        try:
            # Get portfolio service
            portfolio_service = PortfolioService(db)
            
            # Fetch portfolio
            portfolio = await portfolio_service.get_portfolio(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Get portfolio calculation engine
            calc_engine = PortfolioCalculationEngine(db)
            
            # Calculate portfolio returns
            returns_data = await calc_engine.calculate_portfolio_returns(portfolio_id)
            
            if returns_data is None or len(returns_data) < window:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Insufficient historical data for rolling metrics (minimum {window} days required)"
                )
            
            # Initialize rolling metrics calculator
            from ....services.risk_analytics_service import RollingMetrics
            rolling_calc = RollingMetrics(returns_data, risk_free_rate)
            
            # Calculate requested metrics
            rolling_results = {}
            dates = returns_data.index[window-1:].tolist()  # Dates for rolling results
            
            if "sharpe" in metrics:
                rolling_sharpe = rolling_calc.rolling_sharpe_ratio(window).dropna()
                rolling_results["sharpe"] = {
                    "dates": [d.isoformat() for d in rolling_sharpe.index],
                    "values": rolling_sharpe.tolist()
                }
            
            if "volatility" in metrics:
                rolling_vol = rolling_calc.rolling_volatility(window).dropna()
                rolling_results["volatility"] = {
                    "dates": [d.isoformat() for d in rolling_vol.index],
                    "values": rolling_vol.tolist()
                }
            
            if "max_drawdown" in metrics:
                rolling_dd = rolling_calc.rolling_max_drawdown(window).dropna()
                rolling_results["max_drawdown"] = {
                    "dates": [d.isoformat() for d in rolling_dd.index],
                    "values": rolling_dd.tolist()
                }
            
            if "var" in metrics:
                rolling_var = rolling_calc.rolling_var(window).dropna()
                rolling_results["var"] = {
                    "dates": [d.isoformat() for d in rolling_var.index],
                    "values": rolling_var.tolist()
                }
            
            return {
                "success": True,
                "portfolio_id": portfolio_id,
                "portfolio_name": portfolio.name,
                "window": window,
                "metrics": metrics,
                "data": rolling_results,
                "total_data_points": len(returns_data)
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/risk-dashboard/{portfolio_id}")
async def get_risk_dashboard(
    portfolio_id: int,
    risk_free_rate: float = Query(0.02, description="Risk-free rate"),
    benchmark_symbol: str = Query("SPY", description="Benchmark symbol")
):
    """
    Get comprehensive risk dashboard data
    
    This endpoint provides all the data needed for a risk analytics dashboard.
    """
    try:
        from sqlalchemy.orm import Session
        from ....core.database import SessionLocal
        from ....services.portfolio_service import PortfolioService
        from ....services.portfolio_calculation_engine import PortfolioCalculationEngine
        from ....services.market_data_service import MarketDataService
        
        # Get database session
        db: Session = SessionLocal()
        try:
            # Get portfolio service
            portfolio_service = PortfolioService(db)
            
            # Fetch portfolio
            portfolio = await portfolio_service.get_portfolio(portfolio_id)
            if not portfolio:
                raise HTTPException(status_code=404, detail="Portfolio not found")
            
            # Get portfolio calculation engine
            calc_engine = PortfolioCalculationEngine(db)
            
            # Calculate portfolio returns
            returns_data = await calc_engine.calculate_portfolio_returns(portfolio_id)
            
            if returns_data is None or len(returns_data) < 30:
                raise HTTPException(
                    status_code=400, 
                    detail="Insufficient historical data for risk dashboard (minimum 30 days required)"
                )
            
            # Try to get benchmark data
            benchmark_data = None
            try:
                market_service = MarketDataService()
                start_date = returns_data.index[0]
                end_date = returns_data.index[-1]
                
                benchmark_data = await market_service.get_asset_returns(
                    benchmark_symbol, 
                    start_date, 
                    end_date
                )
            except Exception as e:
                # If benchmark fails, continue without it
                pass
            
            # Initialize risk analytics service
            service = RiskAnalyticsService()
            service.initialize_with_data(
                returns_data, 
                benchmark_data, 
                risk_free_rate=risk_free_rate
            )
            
            # Calculate comprehensive metrics
            metrics = service.calculate_comprehensive_risk_metrics(
                rolling_window=252,
                include_benchmark=benchmark_data is not None,
                include_correlation=len(returns_data.columns) > 1
            )
            
            # Generate risk report
            report = service.generate_risk_report(portfolio.name)
            
            # Create dashboard data
            dashboard_data = {
                "portfolio_info": {
                    "id": portfolio_id,
                    "name": portfolio.name,
                    "type": portfolio.portfolio_type,
                    "created_at": portfolio.created_at.isoformat(),
                    "updated_at": portfolio.updated_at.isoformat()
                },
                "risk_metrics": metrics,
                "risk_report": report,
                "benchmark_symbol": benchmark_symbol if benchmark_data is not None else None,
                "data_period": {
                    "start": returns_data.index[0].isoformat(),
                    "end": returns_data.index[-1].isoformat(),
                    "data_points": len(returns_data)
                },
                "chart_data": {
                    "returns": {
                        "dates": [d.isoformat() for d in returns_data.index],
                        "values": returns_data.iloc[:, 0].tolist()
                    },
                    "cumulative_returns": {
                        "dates": [d.isoformat() for d in returns_data.index],
                        "values": (1 + returns_data.iloc[:, 0]).cumprod().tolist()
                    }
                }
            }
            
            # Add rolling metrics for charts
            if len(returns_data) >= 252:
                from ....services.risk_analytics_service import RollingMetrics
                rolling_calc = RollingMetrics(returns_data, risk_free_rate)
                
                rolling_sharpe = rolling_calc.rolling_sharpe_ratio(252).dropna()
                rolling_vol = rolling_calc.rolling_volatility(252).dropna()
                
                dashboard_data["chart_data"]["rolling_sharpe"] = {
                    "dates": [d.isoformat() for d in rolling_sharpe.index],
                    "values": rolling_sharpe.tolist()
                }
                
                dashboard_data["chart_data"]["rolling_volatility"] = {
                    "dates": [d.isoformat() for d in rolling_vol.index],
                    "values": rolling_vol.tolist()
                }
            
            return {
                "success": True,
                "data": dashboard_data
            }
            
        finally:
            db.close()
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


# Health check endpoint
@router.get("/health")
async def health_check():
    """Health check endpoint for risk analytics service"""
    return {"status": "healthy", "service": "risk-analytics", "timestamp": datetime.now().isoformat()}
