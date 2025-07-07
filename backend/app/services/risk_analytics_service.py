"""
Comprehensive Risk Analytics Service

This module provides comprehensive risk analytics capabilities including:
- Risk and performance metrics calculation
- Rolling metrics analysis
- Benchmark comparison
- Value at Risk (VaR) calculations
- Correlation analysis
- Risk reporting and assessment

Based on the FINM 250 solution notebooks and industry best practices.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import empyrical
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.stats import pearsonr, spearmanr
from sklearn.cluster import KMeans
from pydantic import BaseModel, Field
from enum import Enum


class RiskLevel(str, Enum):
    """Risk level assessment"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class RiskMetrics(BaseModel):
    """Risk metrics data model"""
    sharpe_ratio: float = Field(description="Sharpe ratio")
    beta: Optional[float] = Field(None, description="Beta coefficient")
    volatility: float = Field(description="Annualized volatility")
    max_drawdown: float = Field(description="Maximum drawdown")
    var_95: float = Field(description="Value at Risk (95%)")
    cvar_95: float = Field(description="Conditional Value at Risk (95%)")
    calmar_ratio: float = Field(description="Calmar ratio")
    sortino_ratio: float = Field(description="Sortino ratio")
    information_ratio: Optional[float] = Field(None, description="Information ratio")
    alpha: Optional[float] = Field(None, description="Alpha")


class CorrelationAnalysis(BaseModel):
    """Correlation analysis results"""
    correlation_matrix: Dict[str, Dict[str, float]]
    high_correlation_pairs: List[Dict[str, Any]]
    correlation_statistics: Dict[str, float]
    diversification_ratio: float
    asset_clusters: Dict[int, List[str]]


class ComprehensiveRiskMetrics(BaseModel):
    """Complete risk metrics for a portfolio"""
    basic_metrics: RiskMetrics
    performance_metrics: Dict[str, float]
    rolling_metrics: Dict[str, List[float]]
    var_metrics: Dict[str, float]
    benchmark_comparison: Optional[Dict[str, Any]] = None
    correlation_analysis: Optional[CorrelationAnalysis] = None
    calculation_date: datetime
    period_start: datetime
    period_end: datetime
    data_points: int


class RiskCalculator:
    """
    Risk and performance metrics calculator using both custom and Empyrical functions
    """
    
    def __init__(self, returns: pd.Series, risk_free_rate: float = 0.02):
        self.returns = returns.dropna()
        self.risk_free_rate = risk_free_rate
        self.trading_days = 252
    
    def sharpe_ratio(self) -> float:
        """Calculate Sharpe ratio"""
        return empyrical.sharpe_ratio(self.returns, risk_free=self.risk_free_rate)
    
    def volatility(self) -> float:
        """Calculate annualized volatility"""
        return empyrical.annual_volatility(self.returns)
    
    def max_drawdown(self) -> float:
        """Calculate maximum drawdown"""
        return empyrical.max_drawdown(self.returns)
    
    def calmar_ratio(self) -> float:
        """Calculate Calmar ratio"""
        return empyrical.calmar_ratio(self.returns)
    
    def sortino_ratio(self) -> float:
        """Calculate Sortino ratio"""
        return empyrical.sortino_ratio(self.returns, required_return=self.risk_free_rate)
    
    def beta(self, benchmark_returns: pd.Series) -> float:
        """Calculate beta relative to benchmark"""
        if benchmark_returns is None:
            return None
        aligned_returns = self.returns.align(benchmark_returns, join='inner')
        return empyrical.beta(aligned_returns[0], aligned_returns[1])
    
    def alpha(self, benchmark_returns: pd.Series) -> float:
        """Calculate alpha relative to benchmark"""
        if benchmark_returns is None:
            return None
        aligned_returns = self.returns.align(benchmark_returns, join='inner')
        return empyrical.alpha(aligned_returns[0], aligned_returns[1], risk_free=self.risk_free_rate)
    
    def information_ratio(self, benchmark_returns: pd.Series) -> float:
        """Calculate information ratio"""
        if benchmark_returns is None:
            return None
        
        aligned_returns = self.returns.align(benchmark_returns, join='inner')
        excess_returns = aligned_returns[0] - aligned_returns[1]
        
        if excess_returns.std() == 0:
            return 0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(self.trading_days)
    
    def total_return(self) -> float:
        """Calculate total return"""
        return empyrical.cum_returns_final(self.returns)
    
    def annualized_return(self) -> float:
        """Calculate annualized return"""
        return empyrical.annual_return(self.returns)
    
    def skewness(self) -> float:
        """Calculate skewness"""
        return stats.skew(self.returns.dropna())
    
    def kurtosis(self) -> float:
        """Calculate kurtosis"""
        return stats.kurtosis(self.returns.dropna())
    
    def positive_periods(self) -> int:
        """Count positive return periods"""
        return (self.returns > 0).sum()


class RollingMetrics:
    """
    Rolling metrics calculator for time-series analysis
    """
    
    def __init__(self, returns_data: pd.DataFrame, risk_free_rate: float = 0.02):
        self.returns_data = returns_data
        self.risk_free_rate = risk_free_rate
        self.trading_days = 252
    
    def rolling_sharpe_ratio(self, window: int = 252) -> pd.Series:
        """Calculate rolling Sharpe ratio"""
        portfolio_returns = self.returns_data.iloc[:, 0]
        rolling_mean = portfolio_returns.rolling(window=window).mean()
        rolling_std = portfolio_returns.rolling(window=window).std()
        
        daily_rf = self.risk_free_rate / self.trading_days
        return ((rolling_mean - daily_rf) / rolling_std) * np.sqrt(self.trading_days)
    
    def rolling_volatility(self, window: int = 252) -> pd.Series:
        """Calculate rolling volatility"""
        portfolio_returns = self.returns_data.iloc[:, 0]
        return portfolio_returns.rolling(window=window).std() * np.sqrt(self.trading_days)
    
    def rolling_max_drawdown(self, window: int = 252) -> pd.Series:
        """Calculate rolling maximum drawdown"""
        portfolio_returns = self.returns_data.iloc[:, 0]
        
        def rolling_max_dd(x):
            cum_returns = (1 + x).cumprod()
            running_max = cum_returns.expanding().max()
            drawdown = (cum_returns - running_max) / running_max
            return drawdown.min()
        
        return portfolio_returns.rolling(window=window).apply(rolling_max_dd, raw=False)
    
    def rolling_var(self, window: int = 252, confidence: float = 0.05) -> pd.Series:
        """Calculate rolling VaR"""
        portfolio_returns = self.returns_data.iloc[:, 0]
        return portfolio_returns.rolling(window=window).quantile(confidence)
    
    def rolling_beta(self, benchmark_returns: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling beta"""
        portfolio_returns = self.returns_data.iloc[:, 0]
        
        def rolling_beta_calc(x, y):
            if len(x) < 2 or len(y) < 2:
                return np.nan
            return np.cov(x, y)[0, 1] / np.var(y)
        
        return portfolio_returns.rolling(window=window).apply(
            lambda x: rolling_beta_calc(x, benchmark_returns.loc[x.index]), 
            raw=False
        )


class BenchmarkComparator:
    """
    Benchmark comparison and relative performance analysis
    """
    
    def __init__(self, portfolio_returns: pd.Series, benchmark_returns: pd.Series, risk_free_rate: float = 0.02):
        aligned_returns = portfolio_returns.align(benchmark_returns, join='inner')
        self.portfolio_returns = aligned_returns[0]
        self.benchmark_returns = aligned_returns[1]
        self.risk_free_rate = risk_free_rate
        self.trading_days = 252
    
    def tracking_error(self) -> float:
        """Calculate tracking error"""
        excess_returns = self.portfolio_returns - self.benchmark_returns
        return excess_returns.std() * np.sqrt(self.trading_days)
    
    def information_ratio(self) -> float:
        """Calculate information ratio"""
        excess_returns = self.portfolio_returns - self.benchmark_returns
        if excess_returns.std() == 0:
            return 0
        return excess_returns.mean() / excess_returns.std() * np.sqrt(self.trading_days)
    
    def beta(self) -> float:
        """Calculate beta"""
        return np.cov(self.portfolio_returns, self.benchmark_returns)[0, 1] / np.var(self.benchmark_returns)
    
    def alpha(self) -> float:
        """Calculate alpha"""
        portfolio_return = self.portfolio_returns.mean() * self.trading_days
        benchmark_return = self.benchmark_returns.mean() * self.trading_days
        beta = self.beta()
        
        return portfolio_return - (self.risk_free_rate + beta * (benchmark_return - self.risk_free_rate))
    
    def correlation(self) -> float:
        """Calculate correlation"""
        return np.corrcoef(self.portfolio_returns, self.benchmark_returns)[0, 1]
    
    def up_capture_ratio(self) -> float:
        """Calculate up capture ratio"""
        up_market = self.benchmark_returns > 0
        if up_market.sum() == 0:
            return 0
        
        portfolio_up = self.portfolio_returns[up_market].mean()
        benchmark_up = self.benchmark_returns[up_market].mean()
        
        return portfolio_up / benchmark_up if benchmark_up != 0 else 0
    
    def down_capture_ratio(self) -> float:
        """Calculate down capture ratio"""
        down_market = self.benchmark_returns < 0
        if down_market.sum() == 0:
            return 0
        
        portfolio_down = self.portfolio_returns[down_market].mean()
        benchmark_down = self.benchmark_returns[down_market].mean()
        
        return portfolio_down / benchmark_down if benchmark_down != 0 else 0
    
    def relative_performance(self) -> float:
        """Calculate relative performance"""
        portfolio_total = empyrical.cum_returns_final(self.portfolio_returns)
        benchmark_total = empyrical.cum_returns_final(self.benchmark_returns)
        
        return portfolio_total - benchmark_total


class VaRCalculator:
    """
    Value at Risk (VaR) and Expected Shortfall (ES) calculator
    """
    
    def __init__(self, returns: pd.Series):
        self.returns = returns.dropna()
    
    def historical_var(self, confidence: float = 0.05) -> float:
        """Calculate historical VaR"""
        return self.returns.quantile(confidence)
    
    def parametric_var(self, confidence: float = 0.05) -> float:
        """Calculate parametric VaR (assuming normal distribution)"""
        z_score = stats.norm.ppf(confidence)
        return self.returns.mean() + z_score * self.returns.std()
    
    def monte_carlo_var(self, confidence: float = 0.05, n_simulations: int = 10000) -> float:
        """Calculate Monte Carlo VaR"""
        mean_return = self.returns.mean()
        std_return = self.returns.std()
        
        # Generate random returns
        simulated_returns = np.random.normal(mean_return, std_return, n_simulations)
        
        return np.percentile(simulated_returns, confidence * 100)
    
    def conditional_var(self, confidence: float = 0.05) -> float:
        """Calculate Conditional VaR (Expected Shortfall)"""
        var_threshold = self.historical_var(confidence)
        return self.returns[self.returns <= var_threshold].mean()
    
    def var_backtesting(self, confidence: float = 0.05, window: int = 252) -> Dict[str, float]:
        """Perform VaR backtesting"""
        violations = 0
        total_forecasts = 0
        
        for i in range(window, len(self.returns)):
            historical_data = self.returns.iloc[i-window:i]
            var_forecast = historical_data.quantile(confidence)
            actual_return = self.returns.iloc[i]
            
            if actual_return <= var_forecast:
                violations += 1
            total_forecasts += 1
        
        violation_rate = violations / total_forecasts if total_forecasts > 0 else 0
        expected_rate = confidence
        
        return {
            'violation_rate': violation_rate,
            'expected_rate': expected_rate,
            'violations': violations,
            'total_forecasts': total_forecasts
        }


class CorrelationAnalyzer:
    """
    Comprehensive correlation analysis for asset returns
    """
    
    def __init__(self, returns_data: pd.DataFrame):
        self.returns_data = returns_data.copy()
        self.assets = returns_data.columns.tolist()
    
    def calculate_correlation_matrix(self, method='pearson') -> pd.DataFrame:
        """Calculate correlation matrix between assets"""
        return self.returns_data.corr(method=method)
    
    def rolling_correlation(self, asset1: str, asset2: str, window: int = 252) -> pd.Series:
        """Calculate rolling correlation between two assets"""
        return self.returns_data[asset1].rolling(window=window).corr(self.returns_data[asset2])
    
    def find_correlation_pairs(self, threshold: float = 0.8, absolute: bool = True) -> List[Tuple[str, str, float]]:
        """Find asset pairs with high correlation"""
        corr_matrix = self.calculate_correlation_matrix()
        
        pairs = []
        for i in range(len(self.assets)):
            for j in range(i+1, len(self.assets)):
                asset1, asset2 = self.assets[i], self.assets[j]
                correlation = corr_matrix.loc[asset1, asset2]
                
                if absolute:
                    if abs(correlation) >= threshold:
                        pairs.append((asset1, asset2, correlation))
                else:
                    if correlation >= threshold:
                        pairs.append((asset1, asset2, correlation))
        
        return sorted(pairs, key=lambda x: abs(x[2]), reverse=True)
    
    def correlation_clustering(self, n_clusters: int = 3) -> Dict[int, List[str]]:
        """Cluster assets based on correlation"""
        corr_matrix = self.calculate_correlation_matrix()
        distance_matrix = 1 - corr_matrix.abs()
        
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(distance_matrix)
        
        asset_clusters = {}
        for i, asset in enumerate(self.assets):
            cluster_id = clusters[i]
            if cluster_id not in asset_clusters:
                asset_clusters[cluster_id] = []
            asset_clusters[cluster_id].append(asset)
        
        return asset_clusters
    
    def diversification_ratio(self, weights: np.ndarray = None) -> float:
        """Calculate diversification ratio"""
        if weights is None:
            weights = np.ones(len(self.assets)) / len(self.assets)
        
        # Individual asset volatilities
        individual_vols = self.returns_data.std() * np.sqrt(252)
        
        # Portfolio volatility
        cov_matrix = self.returns_data.cov() * 252
        portfolio_vol = np.sqrt(np.dot(weights.T, np.dot(cov_matrix, weights)))
        
        # Weighted average of individual volatilities
        weighted_avg_vol = np.dot(weights, individual_vols)
        
        return weighted_avg_vol / portfolio_vol
    
    def correlation_statistics(self) -> Dict[str, float]:
        """Calculate comprehensive correlation statistics"""
        corr_matrix = self.calculate_correlation_matrix()
        
        # Extract upper triangle correlations (excluding diagonal)
        correlations = []
        for i in range(len(self.assets)):
            for j in range(i+1, len(self.assets)):
                correlations.append(corr_matrix.iloc[i, j])
        
        correlations = np.array(correlations)
        
        return {
            'mean_correlation': np.mean(correlations),
            'median_correlation': np.median(correlations),
            'std_correlation': np.std(correlations),
            'min_correlation': np.min(correlations),
            'max_correlation': np.max(correlations),
            'q25_correlation': np.percentile(correlations, 25),
            'q75_correlation': np.percentile(correlations, 75),
            'negative_correlations': np.sum(correlations < 0),
            'high_correlations': np.sum(correlations > 0.7),
            'low_correlations': np.sum(correlations < 0.3)
        }


class RiskAnalyticsService:
    """
    Comprehensive risk analytics service that integrates all components
    """
    
    def __init__(self):
        self.risk_calculator = None
        self.rolling_metrics = None
        self.benchmark_comparator = None
        self.var_calculator = None
        self.correlation_analyzer = None
    
    def initialize_with_data(self, 
                           returns_data: pd.DataFrame,
                           benchmark_data: pd.DataFrame = None,
                           risk_free_rate: float = 0.02):
        """Initialize the service with data"""
        self.returns_data = returns_data
        self.benchmark_data = benchmark_data
        self.risk_free_rate = risk_free_rate
        
        # Initialize all components
        self.risk_calculator = RiskCalculator(returns_data.iloc[:, 0], risk_free_rate)
        self.rolling_metrics = RollingMetrics(returns_data)
        self.var_calculator = VaRCalculator(returns_data.iloc[:, 0])
        self.correlation_analyzer = CorrelationAnalyzer(returns_data)
        
        if benchmark_data is not None:
            self.benchmark_comparator = BenchmarkComparator(
                returns_data.iloc[:, 0], 
                benchmark_data.iloc[:, 0], 
                risk_free_rate
            )
    
    def calculate_comprehensive_risk_metrics(self, 
                                           rolling_window: int = 252,
                                           var_confidence: float = 0.05,
                                           include_benchmark: bool = True,
                                           include_correlation: bool = True) -> ComprehensiveRiskMetrics:
        """Calculate comprehensive risk metrics"""
        if self.risk_calculator is None:
            raise ValueError("Service not initialized with data")
        
        # Basic risk metrics
        basic_metrics = RiskMetrics(
            sharpe_ratio=self.risk_calculator.sharpe_ratio(),
            beta=self.risk_calculator.beta(
                self.benchmark_data.iloc[:, 0] if self.benchmark_data is not None else None
            ),
            volatility=self.risk_calculator.volatility(),
            max_drawdown=self.risk_calculator.max_drawdown(),
            var_95=self.var_calculator.historical_var(confidence=0.05),
            cvar_95=self.var_calculator.conditional_var(confidence=0.05),
            calmar_ratio=self.risk_calculator.calmar_ratio(),
            sortino_ratio=self.risk_calculator.sortino_ratio(),
            information_ratio=self.risk_calculator.information_ratio(
                self.benchmark_data.iloc[:, 0] if self.benchmark_data is not None else None
            ),
            alpha=self.risk_calculator.alpha(
                self.benchmark_data.iloc[:, 0] if self.benchmark_data is not None else None
            )
        )
        
        # Performance metrics
        performance_metrics = {
            'total_return': self.risk_calculator.total_return(),
            'annualized_return': self.risk_calculator.annualized_return(),
            'annualized_volatility': self.risk_calculator.volatility(),
            'skewness': self.risk_calculator.skewness(),
            'kurtosis': self.risk_calculator.kurtosis(),
            'positive_periods': self.risk_calculator.positive_periods(),
            'negative_periods': len(self.returns_data) - self.risk_calculator.positive_periods()
        }
        
        # Rolling metrics
        rolling_metrics = {
            'rolling_sharpe': self.rolling_metrics.rolling_sharpe_ratio(window=rolling_window).dropna().tolist(),
            'rolling_volatility': self.rolling_metrics.rolling_volatility(window=rolling_window).dropna().tolist(),
            'rolling_max_drawdown': self.rolling_metrics.rolling_max_drawdown(window=rolling_window).dropna().tolist(),
            'rolling_var': self.rolling_metrics.rolling_var(window=rolling_window, confidence=var_confidence).dropna().tolist()
        }
        
        # VaR metrics
        var_metrics = {
            'historical_var_95': self.var_calculator.historical_var(confidence=0.05),
            'historical_var_99': self.var_calculator.historical_var(confidence=0.01),
            'parametric_var_95': self.var_calculator.parametric_var(confidence=0.05),
            'parametric_var_99': self.var_calculator.parametric_var(confidence=0.01),
            'monte_carlo_var_95': self.var_calculator.monte_carlo_var(confidence=0.05),
            'cvar_95': self.var_calculator.conditional_var(confidence=0.05),
            'cvar_99': self.var_calculator.conditional_var(confidence=0.01)
        }
        
        # Benchmark comparison
        benchmark_comparison = None
        if include_benchmark and self.benchmark_comparator is not None:
            benchmark_comparison = {
                'tracking_error': self.benchmark_comparator.tracking_error(),
                'information_ratio': self.benchmark_comparator.information_ratio(),
                'beta': self.benchmark_comparator.beta(),
                'alpha': self.benchmark_comparator.alpha(),
                'correlation': self.benchmark_comparator.correlation(),
                'up_capture': self.benchmark_comparator.up_capture_ratio(),
                'down_capture': self.benchmark_comparator.down_capture_ratio(),
                'relative_return': self.benchmark_comparator.relative_performance()
            }
        
        # Correlation analysis
        correlation_analysis = None
        if include_correlation and len(self.returns_data.columns) > 1:
            corr_matrix = self.correlation_analyzer.calculate_correlation_matrix()
            high_corr_pairs = self.correlation_analyzer.find_correlation_pairs(threshold=0.7)
            corr_stats = self.correlation_analyzer.correlation_statistics()
            div_ratio = self.correlation_analyzer.diversification_ratio()
            clusters = self.correlation_analyzer.correlation_clustering()
            
            correlation_analysis = CorrelationAnalysis(
                correlation_matrix=corr_matrix.to_dict(),
                high_correlation_pairs=[
                    {"asset1": pair[0], "asset2": pair[1], "correlation": pair[2]}
                    for pair in high_corr_pairs
                ],
                correlation_statistics=corr_stats,
                diversification_ratio=div_ratio,
                asset_clusters=clusters
            )
        
        return ComprehensiveRiskMetrics(
            basic_metrics=basic_metrics,
            performance_metrics=performance_metrics,
            rolling_metrics=rolling_metrics,
            var_metrics=var_metrics,
            benchmark_comparison=benchmark_comparison,
            correlation_analysis=correlation_analysis,
            calculation_date=datetime.now(),
            period_start=self.returns_data.index[0],
            period_end=self.returns_data.index[-1],
            data_points=len(self.returns_data)
        )
    
    def generate_risk_report(self, 
                           portfolio_name: str = "Portfolio",
                           rolling_window: int = 252) -> Dict[str, Any]:
        """Generate a comprehensive risk report"""
        metrics = self.calculate_comprehensive_risk_metrics(rolling_window=rolling_window)
        
        report = {
            'portfolio_name': portfolio_name,
            'report_date': datetime.now().isoformat(),
            'period': {
                'start': metrics.period_start.isoformat(),
                'end': metrics.period_end.isoformat(),
                'data_points': metrics.data_points
            },
            'executive_summary': {
                'annualized_return': metrics.performance_metrics['annualized_return'],
                'volatility': metrics.basic_metrics.volatility,
                'sharpe_ratio': metrics.basic_metrics.sharpe_ratio,
                'max_drawdown': metrics.basic_metrics.max_drawdown,
                'var_95': metrics.basic_metrics.var_95
            },
            'detailed_metrics': metrics.dict(),
            'risk_assessment': self._assess_risk_level(metrics),
            'recommendations': self._generate_recommendations(metrics)
        }
        
        return report
    
    def _assess_risk_level(self, metrics: ComprehensiveRiskMetrics) -> str:
        """Assess overall risk level based on metrics"""
        risk_score = 0
        
        # Volatility assessment
        if metrics.basic_metrics.volatility > 0.25:
            risk_score += 3
        elif metrics.basic_metrics.volatility > 0.15:
            risk_score += 2
        else:
            risk_score += 1
        
        # Max drawdown assessment
        if abs(metrics.basic_metrics.max_drawdown) > 0.30:
            risk_score += 3
        elif abs(metrics.basic_metrics.max_drawdown) > 0.20:
            risk_score += 2
        else:
            risk_score += 1
        
        # Sharpe ratio assessment
        if metrics.basic_metrics.sharpe_ratio < 0.5:
            risk_score += 3
        elif metrics.basic_metrics.sharpe_ratio < 1.0:
            risk_score += 2
        else:
            risk_score += 1
        
        if risk_score >= 7:
            return RiskLevel.HIGH.value
        elif risk_score >= 5:
            return RiskLevel.MEDIUM.value
        else:
            return RiskLevel.LOW.value
    
    def _generate_recommendations(self, metrics: ComprehensiveRiskMetrics) -> List[str]:
        """Generate recommendations based on risk metrics"""
        recommendations = []
        
        if metrics.basic_metrics.sharpe_ratio < 0.5:
            recommendations.append("Consider improving risk-adjusted returns through better asset selection")
        
        if abs(metrics.basic_metrics.max_drawdown) > 0.25:
            recommendations.append("High drawdown detected - consider implementing stop-loss strategies")
        
        if metrics.basic_metrics.volatility > 0.20:
            recommendations.append("High volatility - consider diversification or hedging strategies")
        
        if metrics.correlation_analysis and metrics.correlation_analysis.diversification_ratio < 1.5:
            recommendations.append("Low diversification - consider adding uncorrelated assets")
        
        if metrics.benchmark_comparison and metrics.benchmark_comparison['information_ratio'] < 0:
            recommendations.append("Underperforming benchmark - review investment strategy")
        
        return recommendations
