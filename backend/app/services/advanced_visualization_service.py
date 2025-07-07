"""
Advanced Visualization Service
Provides enhanced chart data and visualization capabilities using Plotly and advanced analytics
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.utils import PlotlyJSONEncoder
import json
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import logging
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.diagnostic import jarque_bera
import seaborn as sns
import matplotlib.pyplot as plt
import io
import base64

from ..models.portfolio import Portfolio
from ..models.price_data import PriceData
from ..models.asset import Asset
from .portfolio_calculator import PortfolioCalculator
from .risk_analytics_service import RiskAnalyticsService

logger = logging.getLogger(__name__)

class AdvancedVisualizationService:
    """Service for generating advanced portfolio visualizations and chart data"""
    
    def __init__(self):
        self.calculator = PortfolioCalculator()
        self.risk_service = RiskAnalyticsService()
    
    async def generate_performance_time_series_data(
        self,
        portfolio_id: int,
        benchmark_symbol: str = "SPY",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        chart_type: str = "cumulative"
    ) -> Dict[str, Any]:
        """Generate comprehensive time series data for portfolio performance"""
        try:
            # Get portfolio data
            portfolio_data = await self.calculator.get_portfolio_performance(
                portfolio_id, start_date, end_date
            )
            
            # Get benchmark data
            benchmark_data = await self._get_benchmark_data(
                benchmark_symbol, start_date, end_date
            )
            
            # Calculate different chart types
            if chart_type == "cumulative":
                portfolio_values = self._calculate_cumulative_returns(portfolio_data['returns'])
                benchmark_values = self._calculate_cumulative_returns(benchmark_data['returns'])
            elif chart_type == "normalized":
                portfolio_values = self._normalize_to_base_100(portfolio_data['values'])
                benchmark_values = self._normalize_to_base_100(benchmark_data['values'])
            else:  # returns
                portfolio_values = portfolio_data['returns']
                benchmark_values = benchmark_data['returns']
            
            return {
                "portfolio": [
                    {"date": date.isoformat(), "value": value}
                    for date, value in zip(portfolio_data['dates'], portfolio_values)
                ],
                "benchmark": [
                    {"date": date.isoformat(), "value": value}
                    for date, value in zip(benchmark_data['dates'], benchmark_values)
                ],
                "riskFreeRate": await self._get_risk_free_rate_data(
                    start_date, end_date
                ) if chart_type != "returns" else None
            }
        except Exception as e:
            logger.error(f"Error generating time series data: {e}")
            raise
    
    async def generate_risk_metrics_visualization_data(
        self,
        portfolio_id: int,
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """Generate comprehensive risk metrics visualization data"""
        try:
            portfolio_data = await self.calculator.get_portfolio_performance(
                portfolio_id, 
                datetime.now() - timedelta(days=lookback_days),
                datetime.now()
            )
            
            returns = portfolio_data['returns']
            dates = portfolio_data['dates']
            
            # Calculate drawdown data
            drawdown_data = self._calculate_drawdown_data(portfolio_data['values'])
            
            # Calculate rolling volatility
            volatility_data = self._calculate_rolling_volatility(returns, dates, window=30)
            
            # Calculate rolling VaR
            var_data = self._calculate_rolling_var(returns, dates, confidence=0.95, window=30)
            
            # Generate return distribution
            return_distribution = self._generate_return_distribution(returns)
            
            # Calculate performance metrics
            performance_metrics = await self.risk_service.calculate_performance_metrics(
                returns
            )
            
            return {
                "drawdownData": {
                    "dates": [d.isoformat() for d in dates],
                    "drawdowns": drawdown_data['drawdowns'],
                    "underwater": drawdown_data['underwater'],
                    "peaks": drawdown_data['peaks'],
                    "valleys": drawdown_data['valleys']
                },
                "volatilityData": [
                    {"date": date.isoformat(), "value": vol}
                    for date, vol in zip(volatility_data['dates'], volatility_data['volatility'])
                ],
                "varData": [
                    {"date": date.isoformat(), "value": var}
                    for date, var in zip(var_data['dates'], var_data['var'])
                ],
                "returnDistribution": return_distribution,
                "performanceMetrics": performance_metrics
            }
        except Exception as e:
            logger.error(f"Error generating risk metrics data: {e}")
            raise
    
    async def generate_rolling_metrics_data(
        self,
        portfolio_id: int,
        benchmark_symbol: str = "SPY",
        window: int = 30,
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """Generate rolling metrics data for dynamic analysis"""
        try:
            portfolio_data = await self.calculator.get_portfolio_performance(
                portfolio_id,
                datetime.now() - timedelta(days=lookback_days),
                datetime.now()
            )
            
            benchmark_data = await self._get_benchmark_data(
                benchmark_symbol,
                datetime.now() - timedelta(days=lookback_days),
                datetime.now()
            )
            
            returns_portfolio = portfolio_data['returns']
            returns_benchmark = benchmark_data['returns']
            dates = portfolio_data['dates']
            
            # Calculate rolling metrics
            rolling_sharpe = self._calculate_rolling_sharpe(returns_portfolio, window)
            rolling_volatility = self._calculate_rolling_volatility(
                returns_portfolio, dates, window
            )['volatility']
            rolling_beta = self._calculate_rolling_beta(
                returns_portfolio, returns_benchmark, window
            )
            rolling_alpha = self._calculate_rolling_alpha(
                returns_portfolio, returns_benchmark, window
            )
            rolling_correlation = self._calculate_rolling_correlation(
                returns_portfolio, returns_benchmark, window
            )
            
            # Align dates (rolling metrics have fewer data points)
            aligned_dates = dates[window-1:]
            
            return {
                "dates": [d.isoformat() for d in aligned_dates],
                "sharpeRatio": rolling_sharpe,
                "volatility": rolling_volatility,
                "beta": rolling_beta,
                "alpha": rolling_alpha,
                "correlation": rolling_correlation
            }
        except Exception as e:
            logger.error(f"Error generating rolling metrics data: {e}")
            raise
    
    async def generate_asset_allocation_data(
        self,
        portfolio_id: int
    ) -> Dict[str, Any]:
        """Generate comprehensive asset allocation data"""
        try:
            holdings = await self.calculator.get_portfolio_holdings(portfolio_id)
            
            # Calculate allocations by different criteria
            holdings_data = []
            sector_allocations = {}
            asset_class_allocations = {}
            total_value = sum(holding['value'] for holding in holdings)
            
            for holding in holdings:
                weight = holding['value'] / total_value
                
                holdings_data.append({
                    "symbol": holding['symbol'],
                    "name": holding['name'],
                    "weight": weight,
                    "value": holding['value'],
                    "sector": holding.get('sector', 'Unknown'),
                    "assetClass": holding.get('asset_class', 'Equity')
                })
                
                # Aggregate by sector
                sector = holding.get('sector', 'Unknown')
                if sector not in sector_allocations:
                    sector_allocations[sector] = {"name": sector, "weight": 0, "value": 0}
                sector_allocations[sector]["weight"] += weight
                sector_allocations[sector]["value"] += holding['value']
                
                # Aggregate by asset class
                asset_class = holding.get('asset_class', 'Equity')
                if asset_class not in asset_class_allocations:
                    asset_class_allocations[asset_class] = {
                        "name": asset_class, "weight": 0, "value": 0
                    }
                asset_class_allocations[asset_class]["weight"] += weight
                asset_class_allocations[asset_class]["value"] += holding['value']
            
            return {
                "holdings": holdings_data,
                "sectorAllocations": list(sector_allocations.values()),
                "assetClassAllocations": list(asset_class_allocations.values())
            }
        except Exception as e:
            logger.error(f"Error generating allocation data: {e}")
            raise
    
    async def generate_portfolio_benchmark_comparison(
        self,
        portfolio_id: int,
        benchmark_symbol: str = "SPY",
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """Generate comprehensive portfolio vs benchmark comparison data"""
        try:
            portfolio_data = await self.calculator.get_portfolio_performance(
                portfolio_id,
                datetime.now() - timedelta(days=lookback_days),
                datetime.now()
            )
            
            benchmark_data = await self._get_benchmark_data(
                benchmark_symbol,
                datetime.now() - timedelta(days=lookback_days),
                datetime.now()
            )
            
            # Calculate relative performance
            outperformance = [
                p_ret - b_ret 
                for p_ret, b_ret in zip(portfolio_data['returns'], benchmark_data['returns'])
            ]
            
            # Calculate metrics for both
            portfolio_metrics = await self.risk_service.calculate_performance_metrics(
                portfolio_data['returns']
            )
            benchmark_metrics = await self.risk_service.calculate_performance_metrics(
                benchmark_data['returns']
            )
            
            # Add relative metrics
            portfolio_metrics.update({
                "informationRatio": self._calculate_information_ratio(
                    portfolio_data['returns'], benchmark_data['returns']
                ),
                "trackingError": np.std(outperformance) * np.sqrt(252)
            })
            
            return {
                "data": {
                    "portfolio": [
                        {"date": date.isoformat(), "value": value}
                        for date, value in zip(portfolio_data['dates'], portfolio_data['values'])
                    ],
                    "benchmark": [
                        {"date": date.isoformat(), "value": value}
                        for date, value in zip(benchmark_data['dates'], benchmark_data['values'])
                    ],
                    "outperformance": [
                        {"date": date.isoformat(), "value": value}
                        for date, value in zip(portfolio_data['dates'], outperformance)
                    ]
                },
                "portfolioMetrics": portfolio_metrics,
                "benchmarkMetrics": benchmark_metrics
            }
        except Exception as e:
            logger.error(f"Error generating comparison data: {e}")
            raise
    
    async def generate_return_distribution_data(
        self,
        portfolio_id: int,
        benchmark_symbol: Optional[str] = None,
        lookback_days: int = 252
    ) -> Dict[str, Any]:
        """Generate enhanced return distribution analysis"""
        try:
            portfolio_data = await self.calculator.get_portfolio_performance(
                portfolio_id,
                datetime.now() - timedelta(days=lookback_days),
                datetime.now()
            )
            
            returns = portfolio_data['returns']
            distribution_data = self._generate_return_distribution(returns)
            
            result = {
                "data": distribution_data
            }
            
            # Add benchmark comparison if requested
            if benchmark_symbol:
                benchmark_data = await self._get_benchmark_data(
                    benchmark_symbol,
                    datetime.now() - timedelta(days=lookback_days),
                    datetime.now()
                )
                benchmark_distribution = self._generate_return_distribution(
                    benchmark_data['returns']
                )
                result["benchmarkData"] = benchmark_distribution
            
            return result
        except Exception as e:
            logger.error(f"Error generating distribution data: {e}")
            raise
    
    def generate_plotly_interactive_chart(
        self,
        chart_type: str,
        data: Dict[str, Any],
        **kwargs
    ) -> str:
        """Generate interactive Plotly charts as JSON"""
        try:
            if chart_type == "performance_comparison":
                fig = self._create_performance_comparison_plot(data, **kwargs)
            elif chart_type == "risk_heatmap":
                fig = self._create_risk_heatmap(data, **kwargs)
            elif chart_type == "correlation_matrix":
                fig = self._create_correlation_matrix(data, **kwargs)
            elif chart_type == "monte_carlo_simulation":
                fig = self._create_monte_carlo_plot(data, **kwargs)
            else:
                raise ValueError(f"Unknown chart type: {chart_type}")
            
            return json.dumps(fig, cls=PlotlyJSONEncoder)
        except Exception as e:
            logger.error(f"Error generating Plotly chart: {e}")
            raise
    
    # Helper methods
    def _calculate_cumulative_returns(self, returns: List[float]) -> List[float]:
        """Calculate cumulative returns from daily returns"""
        cumulative = [1.0]
        for ret in returns:
            cumulative.append(cumulative[-1] * (1 + ret))
        return cumulative[1:]
    
    def _normalize_to_base_100(self, values: List[float]) -> List[float]:
        """Normalize values to base 100"""
        if not values:
            return []
        base = values[0]
        return [v / base * 100 for v in values]
    
    def _calculate_drawdown_data(self, values: List[float]) -> Dict[str, List]:
        """Calculate drawdown data including underwater periods"""
        peak = values[0]
        drawdowns = []
        underwater = []
        peaks = []
        valleys = []
        
        for value in values:
            if value > peak:
                peak = value
            
            drawdown = (value - peak) / peak
            drawdowns.append(drawdown)
            underwater.append(drawdown < -0.001)  # 0.1% threshold
            peaks.append(peak)
            valleys.append(value if drawdown < 0 else peak)
        
        return {
            "drawdowns": drawdowns,
            "underwater": underwater,
            "peaks": peaks,
            "valleys": valleys
        }
    
    def _calculate_rolling_volatility(
        self, 
        returns: List[float], 
        dates: List[datetime], 
        window: int = 30
    ) -> Dict[str, List]:
        """Calculate rolling volatility"""
        df = pd.DataFrame({'returns': returns}, index=dates)
        rolling_vol = df['returns'].rolling(window=window).std() * np.sqrt(252)
        
        return {
            "dates": rolling_vol.dropna().index.tolist(),
            "volatility": rolling_vol.dropna().tolist()
        }
    
    def _calculate_rolling_var(
        self,
        returns: List[float],
        dates: List[datetime],
        confidence: float = 0.95,
        window: int = 30
    ) -> Dict[str, List]:
        """Calculate rolling Value at Risk"""
        df = pd.DataFrame({'returns': returns}, index=dates)
        rolling_var = df['returns'].rolling(window=window).quantile(1 - confidence)
        
        return {
            "dates": rolling_var.dropna().index.tolist(),
            "var": rolling_var.dropna().tolist()
        }
    
    def _generate_return_distribution(self, returns: List[float]) -> Dict[str, Any]:
        """Generate comprehensive return distribution data"""
        returns_array = np.array(returns)
        
        # Calculate bins and frequencies
        hist, bin_edges = np.histogram(returns_array, bins=30, density=False)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        
        # Calculate statistics
        statistics = {
            "mean": float(np.mean(returns_array)),
            "median": float(np.median(returns_array)),
            "standardDeviation": float(np.std(returns_array)),
            "skewness": float(stats.skew(returns_array)),
            "kurtosis": float(stats.kurtosis(returns_array)),
            "var95": float(np.percentile(returns_array, 5)),
            "var99": float(np.percentile(returns_array, 1))
        }
        
        return {
            "returns": returns,
            "bins": bin_centers.tolist(),
            "frequencies": hist.tolist(),
            "statistics": statistics
        }
    
    def _calculate_rolling_sharpe(self, returns: List[float], window: int) -> List[float]:
        """Calculate rolling Sharpe ratio"""
        df = pd.DataFrame({'returns': returns})
        rolling_mean = df['returns'].rolling(window=window).mean()
        rolling_std = df['returns'].rolling(window=window).std()
        rolling_sharpe = (rolling_mean / rolling_std) * np.sqrt(252)
        return rolling_sharpe.dropna().tolist()
    
    def _calculate_rolling_beta(
        self, 
        portfolio_returns: List[float], 
        benchmark_returns: List[float], 
        window: int
    ) -> List[float]:
        """Calculate rolling beta"""
        df = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        })
        
        rolling_beta = []
        for i in range(window - 1, len(df)):
            p_slice = df['portfolio'].iloc[i-window+1:i+1]
            b_slice = df['benchmark'].iloc[i-window+1:i+1]
            
            covariance = np.cov(p_slice, b_slice)[0][1]
            variance = np.var(b_slice)
            beta = covariance / variance if variance != 0 else 0
            rolling_beta.append(beta)
        
        return rolling_beta
    
    def _calculate_rolling_alpha(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float],
        window: int,
        risk_free_rate: float = 0.02
    ) -> List[float]:
        """Calculate rolling alpha"""
        df = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        })
        
        rolling_alpha = []
        daily_rf = risk_free_rate / 252
        
        for i in range(window - 1, len(df)):
            p_slice = df['portfolio'].iloc[i-window+1:i+1]
            b_slice = df['benchmark'].iloc[i-window+1:i+1]
            
            # Calculate beta for this window
            covariance = np.cov(p_slice, b_slice)[0][1]
            variance = np.var(b_slice)
            beta = covariance / variance if variance != 0 else 0
            
            # Calculate alpha
            portfolio_excess = np.mean(p_slice) - daily_rf
            benchmark_excess = np.mean(b_slice) - daily_rf
            alpha = portfolio_excess - beta * benchmark_excess
            rolling_alpha.append(alpha * 252)  # Annualize
        
        return rolling_alpha
    
    def _calculate_rolling_correlation(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float],
        window: int
    ) -> List[float]:
        """Calculate rolling correlation"""
        df = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        })
        
        rolling_corr = df['portfolio'].rolling(window=window).corr(df['benchmark'])
        return rolling_corr.dropna().tolist()
    
    def _calculate_information_ratio(
        self,
        portfolio_returns: List[float],
        benchmark_returns: List[float]
    ) -> float:
        """Calculate information ratio"""
        excess_returns = [p - b for p, b in zip(portfolio_returns, benchmark_returns)]
        return np.mean(excess_returns) / np.std(excess_returns) * np.sqrt(252)
    
    async def _get_benchmark_data(
        self,
        symbol: str,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> Dict[str, Any]:
        """Get benchmark data - placeholder implementation"""
        # This would integrate with your actual market data service
        # For now, return dummy data
        if not start_date:
            start_date = datetime.now() - timedelta(days=252)
        if not end_date:
            end_date = datetime.now()
        
        # Generate dummy benchmark data
        dates = pd.date_range(start_date, end_date, freq='D')
        returns = np.random.normal(0.0008, 0.012, len(dates))  # ~SPY-like returns
        values = [100]
        for ret in returns:
            values.append(values[-1] * (1 + ret))
        
        return {
            "dates": dates.tolist(),
            "returns": returns.tolist(),
            "values": values[1:]
        }
    
    async def _get_risk_free_rate_data(
        self,
        start_date: Optional[datetime],
        end_date: Optional[datetime]
    ) -> List[Dict[str, Any]]:
        """Get risk-free rate data"""
        # Placeholder - would integrate with treasury data
        if not start_date:
            start_date = datetime.now() - timedelta(days=252)
        if not end_date:
            end_date = datetime.now()
        
        dates = pd.date_range(start_date, end_date, freq='D')
        risk_free_rate = 0.02  # 2% annual
        daily_rate = risk_free_rate / 252
        
        cumulative_value = 100
        result = []
        for date in dates:
            cumulative_value *= (1 + daily_rate)
            result.append({
                "date": date.isoformat(),
                "value": cumulative_value
            })
        
        return result
    
    def _create_performance_comparison_plot(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Create interactive performance comparison plot"""
        fig = go.Figure()
        
        # Add portfolio line
        fig.add_trace(go.Scatter(
            x=[d['date'] for d in data['portfolio']],
            y=[d['value'] for d in data['portfolio']],
            mode='lines',
            name='Portfolio',
            line=dict(color='blue', width=2)
        ))
        
        # Add benchmark line
        if 'benchmark' in data:
            fig.add_trace(go.Scatter(
                x=[d['date'] for d in data['benchmark']],
                y=[d['value'] for d in data['benchmark']],
                mode='lines',
                name='Benchmark',
                line=dict(color='red', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title='Portfolio Performance Comparison',
            xaxis_title='Date',
            yaxis_title='Cumulative Return',
            hovermode='x unified'
        )
        
        return fig
    
    def _create_risk_heatmap(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Create risk metrics heatmap"""
        # Placeholder implementation
        fig = go.Figure(data=go.Heatmap(
            z=[[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            x=['Metric 1', 'Metric 2', 'Metric 3'],
            y=['Period 1', 'Period 2', 'Period 3']
        ))
        
        fig.update_layout(title='Risk Metrics Heatmap')
        return fig
    
    def _create_correlation_matrix(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Create correlation matrix heatmap"""
        # Placeholder implementation
        correlation_matrix = np.corrcoef(np.random.rand(5, 100))
        
        fig = go.Figure(data=go.Heatmap(
            z=correlation_matrix,
            colorscale='RdBu',
            zmid=0
        ))
        
        fig.update_layout(title='Asset Correlation Matrix')
        return fig
    
    def _create_monte_carlo_plot(self, data: Dict[str, Any], **kwargs) -> go.Figure:
        """Create Monte Carlo simulation plot"""
        # Placeholder implementation
        simulations = 1000
        time_horizon = 252
        
        fig = go.Figure()
        
        for i in range(min(100, simulations)):  # Show only 100 paths
            returns = np.random.normal(0.001, 0.02, time_horizon)
            cumulative = np.cumprod(1 + returns)
            fig.add_trace(go.Scatter(
                y=cumulative,
                mode='lines',
                line=dict(width=0.5, color='rgba(0,100,80,0.2)'),
                showlegend=False
            ))
        
        fig.update_layout(
            title='Monte Carlo Simulation',
            xaxis_title='Trading Days',
            yaxis_title='Portfolio Value'
        )
        
        return fig
