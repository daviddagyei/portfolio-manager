"""
Risk Analytics Engine - Core Module
Comprehensive risk and performance metrics for portfolio management.

Author: Portfolio Manager Team
Date: July 2025
Version: 1.0
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import scipy.stats as stats
try:
    import empyrical as emp
except ImportError:
    emp = None
    print("Warning: empyrical library not available. Some features may be limited.")

# Constants
TRADING_DAYS_PER_YEAR = 252
RISK_FREE_RATE = 0.02  # 2% annual risk-free rate


class RiskMetrics:
    """
    Core risk metrics class combining Empyrical library with custom calculations.
    Inspired by FINM 250 solutions and quantitative finance best practices.
    """
    
    @staticmethod
    def calculate_return_metrics(returns: pd.Series, 
                               risk_free_rate: float = RISK_FREE_RATE,
                               periods: int = TRADING_DAYS_PER_YEAR) -> Dict[str, float]:
        """
        Calculate comprehensive return metrics using both Empyrical and custom functions.
        
        Args:
            returns: Time series of returns
            risk_free_rate: Annual risk-free rate
            periods: Number of periods per year for annualization
            
        Returns:
            Dictionary of return metrics
        """
        metrics = {}
        
        # Using Empyrical if available
        if emp is not None:
            try:
                metrics['annual_return_emp'] = emp.annual_return(returns, periods=periods)
                metrics['annual_volatility_emp'] = emp.annual_volatility(returns, periods=periods)
                metrics['sharpe_ratio_emp'] = emp.sharpe_ratio(returns, risk_free=risk_free_rate, periods=periods)
                metrics['sortino_ratio_emp'] = emp.sortino_ratio(returns, required_return=risk_free_rate, periods=periods)
                metrics['calmar_ratio_emp'] = emp.calmar_ratio(returns, periods=periods)
            except Exception as e:
                print(f"Warning: Error using empyrical library: {e}")
        
        # Custom calculations (always available)
        metrics['annual_return'] = returns.mean() * periods
        metrics['annual_volatility'] = returns.std() * np.sqrt(periods)
        
        if metrics['annual_volatility'] > 0:
            metrics['sharpe_ratio'] = (metrics['annual_return'] - risk_free_rate) / metrics['annual_volatility']
        else:
            metrics['sharpe_ratio'] = 0.0
        
        # Additional custom metrics
        metrics['skewness'] = returns.skew()
        metrics['kurtosis'] = returns.kurtosis()
        metrics['downside_deviation'] = RiskMetrics._downside_deviation(returns, risk_free_rate, periods)
        
        # Sortino ratio calculation
        if metrics['downside_deviation'] > 0:
            metrics['sortino_ratio'] = (metrics['annual_return'] - risk_free_rate) / metrics['downside_deviation']
        else:
            metrics['sortino_ratio'] = 0.0
        
        return metrics
    
    @staticmethod
    def calculate_risk_metrics(returns: pd.Series, 
                             benchmark: pd.Series = None,
                             periods: int = TRADING_DAYS_PER_YEAR) -> Dict[str, Any]:
        """
        Calculate comprehensive risk metrics.
        
        Args:
            returns: Time series of returns
            benchmark: Benchmark returns (e.g., S&P 500)
            periods: Number of periods per year
            
        Returns:
            Dictionary of risk metrics
        """
        metrics = {}
        
        # Using Empyrical if available
        if emp is not None:
            try:
                metrics['max_drawdown_emp'] = emp.max_drawdown(returns)
                metrics['var_95_emp'] = emp.value_at_risk(returns, cutoff=0.05)
                metrics['cvar_95_emp'] = emp.conditional_value_at_risk(returns, cutoff=0.05)
            except Exception as e:
                print(f"Warning: Error using empyrical library: {e}")
        
        # Custom VaR calculations
        metrics['var_95_historical'] = RiskMetrics._historical_var(returns, confidence_level=0.95)
        metrics['var_99_historical'] = RiskMetrics._historical_var(returns, confidence_level=0.99)
        metrics['var_95_parametric'] = RiskMetrics._parametric_var(returns, confidence_level=0.95)
        
        # Drawdown analysis
        drawdown_info = RiskMetrics._drawdown_analysis(returns)
        metrics.update(drawdown_info)
        
        # Beta calculation if benchmark provided
        if benchmark is not None:
            metrics['beta'] = RiskMetrics._calculate_beta(returns, benchmark)
            metrics['alpha'] = RiskMetrics._calculate_alpha(returns, benchmark, periods)
            metrics['correlation'] = returns.corr(benchmark)
            metrics['r_squared'] = metrics['correlation'] ** 2
            
            if not np.isnan(metrics['beta']) and metrics['beta'] != 0:
                metrics['treynor_ratio'] = (returns.mean() * periods) / metrics['beta']
            else:
                metrics['treynor_ratio'] = np.nan
                
            metrics['information_ratio'] = RiskMetrics._information_ratio(returns, benchmark, periods)
            metrics['tracking_error'] = RiskMetrics._tracking_error(returns, benchmark, periods)
        
        return metrics
    
    @staticmethod
    def _downside_deviation(returns: pd.Series, target_return: float, periods: int) -> float:
        """Calculate downside deviation."""
        target_return_per_period = target_return / periods
        negative_returns = returns[returns < target_return_per_period]
        if len(negative_returns) == 0:
            return 0.0
        return negative_returns.std() * np.sqrt(periods)
    
    @staticmethod
    def _historical_var(returns: pd.Series, confidence_level: float) -> float:
        """Calculate historical Value at Risk."""
        if len(returns) == 0:
            return np.nan
        return np.percentile(returns, (1 - confidence_level) * 100)
    
    @staticmethod
    def _parametric_var(returns: pd.Series, confidence_level: float) -> float:
        """Calculate parametric Value at Risk assuming normal distribution."""
        if len(returns) == 0:
            return np.nan
        mean = returns.mean()
        std = returns.std()
        z_score = stats.norm.ppf(1 - confidence_level)
        return mean + z_score * std
    
    @staticmethod
    def _drawdown_analysis(returns: pd.Series) -> Dict[str, Any]:
        """Detailed drawdown analysis."""
        if len(returns) == 0:
            return {
                'max_drawdown': np.nan,
                'max_drawdown_date': None,
                'peak_date': None,
                'recovery_date': None,
                'drawdown_duration': None,
                'avg_drawdown': np.nan,
                'drawdown_periods': 0
            }
        
        cumulative_returns = (1 + returns).cumprod()
        running_max = cumulative_returns.cummax()
        drawdown = (cumulative_returns - running_max) / running_max
        
        max_drawdown = drawdown.min()
        max_drawdown_idx = drawdown.idxmin() if not pd.isna(drawdown.min()) else None
        
        # Find peak and recovery
        peak_idx = None
        recovery_idx = None
        duration = None
        
        if max_drawdown_idx is not None:
            peak_idx = running_max.loc[:max_drawdown_idx].idxmax()
            
            # Find recovery point
            peak_value = running_max.loc[peak_idx]
            post_drawdown = cumulative_returns.loc[max_drawdown_idx:]
            recovery_points = post_drawdown[post_drawdown >= peak_value]
            
            if not recovery_points.empty:
                recovery_idx = recovery_points.index[0]
                # Calculate duration in days or periods
                if hasattr(recovery_idx, 'days'):
                    duration = (recovery_idx - peak_idx).days
                else:
                    duration = len(returns.loc[peak_idx:recovery_idx])
        
        return {
            'max_drawdown': max_drawdown,
            'max_drawdown_date': max_drawdown_idx,
            'peak_date': peak_idx,
            'recovery_date': recovery_idx,
            'drawdown_duration': duration,
            'avg_drawdown': drawdown[drawdown < 0].mean() if len(drawdown[drawdown < 0]) > 0 else np.nan,
            'drawdown_periods': len(drawdown[drawdown < 0])
        }
    
    @staticmethod
    def _calculate_beta(returns: pd.Series, benchmark: pd.Series) -> float:
        """Calculate beta using regression."""
        # Align the series
        aligned_data = pd.DataFrame({'returns': returns, 'benchmark': benchmark}).dropna()
        
        if len(aligned_data) < 2:
            return np.nan
            
        covariance = aligned_data['returns'].cov(aligned_data['benchmark'])
        benchmark_variance = aligned_data['benchmark'].var()
        
        return covariance / benchmark_variance if benchmark_variance != 0 else np.nan
    
    @staticmethod
    def _calculate_alpha(returns: pd.Series, benchmark: pd.Series, periods: int) -> float:
        """Calculate alpha (excess return over benchmark adjusted for beta)."""
        beta = RiskMetrics._calculate_beta(returns, benchmark)
        if np.isnan(beta):
            return np.nan
        
        annual_return = returns.mean() * periods
        annual_benchmark_return = benchmark.mean() * periods
        
        return annual_return - (beta * annual_benchmark_return)
    
    @staticmethod
    def _information_ratio(returns: pd.Series, benchmark: pd.Series, periods: int) -> float:
        """Calculate information ratio."""
        excess_returns = returns - benchmark
        if len(excess_returns.dropna()) == 0:
            return np.nan
        
        excess_mean = excess_returns.mean()
        excess_std = excess_returns.std()
        
        if excess_std == 0:
            return np.nan
        
        return (excess_mean * periods) / (excess_std * np.sqrt(periods))
    
    @staticmethod
    def _tracking_error(returns: pd.Series, benchmark: pd.Series, periods: int) -> float:
        """Calculate tracking error."""
        excess_returns = returns - benchmark
        if len(excess_returns.dropna()) == 0:
            return np.nan
        return excess_returns.std() * np.sqrt(periods)


class RollingMetrics:
    """
    Class for calculating rolling risk metrics over time windows.
    """
    
    @staticmethod
    def rolling_sharpe_ratio(returns: pd.Series, window: int = 252, 
                           risk_free_rate: float = RISK_FREE_RATE) -> pd.Series:
        """Calculate rolling Sharpe ratio."""
        rolling_mean = returns.rolling(window=window).mean() * TRADING_DAYS_PER_YEAR
        rolling_std = returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
        return (rolling_mean - risk_free_rate) / rolling_std
    
    @staticmethod
    def rolling_volatility(returns: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling volatility (annualized)."""
        return returns.rolling(window=window).std() * np.sqrt(TRADING_DAYS_PER_YEAR)
    
    @staticmethod
    def rolling_beta(returns: pd.Series, benchmark: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling beta."""
        def calculate_beta(y, x):
            if len(y) < 2 or len(x) < 2:
                return np.nan
            covariance = np.cov(y, x)[0, 1]
            variance = np.var(x)
            return covariance / variance if variance != 0 else np.nan
        
        rolling_beta = pd.Series(index=returns.index, dtype=float)
        
        for i in range(window, len(returns)):
            y_window = returns.iloc[i-window:i]
            x_window = benchmark.iloc[i-window:i]
            rolling_beta.iloc[i] = calculate_beta(y_window, x_window)
        
        return rolling_beta
    
    @staticmethod
    def rolling_alpha(returns: pd.Series, benchmark: pd.Series, window: int = 252,
                     risk_free_rate: float = RISK_FREE_RATE) -> pd.Series:
        """Calculate rolling alpha."""
        rolling_beta = RollingMetrics.rolling_beta(returns, benchmark, window)
        
        rolling_portfolio_return = returns.rolling(window=window).mean() * TRADING_DAYS_PER_YEAR
        rolling_benchmark_return = benchmark.rolling(window=window).mean() * TRADING_DAYS_PER_YEAR
        
        return rolling_portfolio_return - (rolling_beta * rolling_benchmark_return)
    
    @staticmethod
    def rolling_max_drawdown(returns: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling maximum drawdown."""
        rolling_max_dd = pd.Series(index=returns.index, dtype=float)
        
        for i in range(window, len(returns)):
            window_returns = returns.iloc[i-window:i]
            cumulative_returns = (1 + window_returns).cumprod()
            running_max = cumulative_returns.cummax()
            drawdown = (cumulative_returns - running_max) / running_max
            rolling_max_dd.iloc[i] = drawdown.min()
        
        return rolling_max_dd
    
    @staticmethod
    def rolling_var(returns: pd.Series, window: int = 252, confidence_level: float = 0.95) -> pd.Series:
        """Calculate rolling Value at Risk."""
        return returns.rolling(window=window).quantile(1 - confidence_level)


class BenchmarkComparison:
    """
    Class for comprehensive benchmark comparison analysis.
    """
    
    @staticmethod
    def compare_performance(portfolio_returns: pd.Series, benchmark_returns: pd.Series,
                          periods: int = TRADING_DAYS_PER_YEAR) -> pd.DataFrame:
        """
        Compare portfolio performance against benchmark.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            periods: Number of periods per year
            
        Returns:
            DataFrame with side-by-side comparison
        """
        # Calculate metrics for both
        portfolio_metrics = RiskMetrics.calculate_return_metrics(portfolio_returns)
        portfolio_risk = RiskMetrics.calculate_risk_metrics(portfolio_returns, benchmark_returns)
        portfolio_metrics.update(portfolio_risk)
        
        benchmark_metrics = RiskMetrics.calculate_return_metrics(benchmark_returns)
        benchmark_risk = RiskMetrics.calculate_risk_metrics(benchmark_returns)
        benchmark_metrics.update(benchmark_risk)
        
        # Key metrics for comparison
        key_metrics = [
            'annual_return', 'annual_volatility', 'sharpe_ratio',
            'max_drawdown', 'var_95_historical', 'skewness', 'kurtosis'
        ]
        
        comparison_data = []
        for metric in key_metrics:
            portfolio_val = portfolio_metrics.get(metric, np.nan)
            benchmark_val = benchmark_metrics.get(metric, np.nan)
            
            if not np.isnan(portfolio_val) and not np.isnan(benchmark_val):
                difference = portfolio_val - benchmark_val
                outperformance = "✅" if difference > 0 else "❌"
                
                # Exception for risk metrics where lower is better
                if metric in ['annual_volatility', 'max_drawdown', 'var_95_historical']:
                    outperformance = "✅" if difference < 0 else "❌"
                
                comparison_data.append({
                    'Metric': metric.replace('_', ' ').title(),
                    'Portfolio': portfolio_val,
                    'Benchmark': benchmark_val,
                    'Difference': difference,
                    'Outperformance': outperformance
                })
        
        return pd.DataFrame(comparison_data)
    
    @staticmethod
    def relative_performance_analysis(portfolio_returns: pd.Series, benchmark_returns: pd.Series) -> Dict:
        """
        Analyze relative performance metrics.
        
        Args:
            portfolio_returns: Portfolio return series
            benchmark_returns: Benchmark return series
            
        Returns:
            Dictionary with relative performance metrics
        """
        # Align the series
        aligned_data = pd.DataFrame({'portfolio': portfolio_returns, 'benchmark': benchmark_returns}).dropna()
        
        if len(aligned_data) == 0:
            return {}
        
        excess_returns = aligned_data['portfolio'] - aligned_data['benchmark']
        
        # Calculate relative performance metrics
        relative_metrics = {
            'total_excess_return': excess_returns.sum(),
            'annualized_excess_return': excess_returns.mean() * TRADING_DAYS_PER_YEAR,
            'excess_volatility': excess_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR),
            'win_rate': (excess_returns > 0).mean(),
            'average_win': excess_returns[excess_returns > 0].mean() if len(excess_returns[excess_returns > 0]) > 0 else np.nan,
            'average_loss': excess_returns[excess_returns < 0].mean() if len(excess_returns[excess_returns < 0]) > 0 else np.nan,
            'best_relative_day': excess_returns.max(),
            'worst_relative_day': excess_returns.min(),
            'up_capture_ratio': BenchmarkComparison._capture_ratio(aligned_data['portfolio'], aligned_data['benchmark'], True),
            'down_capture_ratio': BenchmarkComparison._capture_ratio(aligned_data['portfolio'], aligned_data['benchmark'], False)
        }
        
        # Information ratio
        if relative_metrics['excess_volatility'] > 0:
            relative_metrics['information_ratio'] = relative_metrics['annualized_excess_return'] / relative_metrics['excess_volatility']
        else:
            relative_metrics['information_ratio'] = np.nan
        
        return relative_metrics
    
    @staticmethod
    def _capture_ratio(portfolio_returns: pd.Series, benchmark_returns: pd.Series, upside: bool = True) -> float:
        """Calculate up/down capture ratio."""
        if upside:
            mask = benchmark_returns > 0
        else:
            mask = benchmark_returns < 0
        
        portfolio_filtered = portfolio_returns[mask]
        benchmark_filtered = benchmark_returns[mask]
        
        if len(portfolio_filtered) == 0 or len(benchmark_filtered) == 0:
            return np.nan
        
        portfolio_avg = portfolio_filtered.mean()
        benchmark_avg = benchmark_filtered.mean()
        
        return portfolio_avg / benchmark_avg if benchmark_avg != 0 else np.nan


class CorrelationAnalysis:
    """
    Class for correlation analysis between assets.
    """
    
    @staticmethod
    def calculate_correlation_matrix(returns_df: pd.DataFrame) -> pd.DataFrame:
        """Calculate correlation matrix for multiple assets."""
        return returns_df.corr()
    
    @staticmethod
    def find_correlation_extremes(correlation_matrix: pd.DataFrame, n_pairs: int = 5) -> Dict:
        """
        Find most and least correlated pairs of assets.
        
        Args:
            correlation_matrix: Correlation matrix DataFrame
            n_pairs: Number of pairs to return
            
        Returns:
            Dictionary with most and least correlated pairs
        """
        # Convert correlation matrix to series and remove self-correlations
        corr_series = correlation_matrix.unstack()
        corr_series = corr_series[corr_series != 1.0]
        
        # Remove duplicate pairs
        unique_pairs = []
        seen_pairs = set()
        
        for (asset1, asset2), corr in corr_series.items():
            pair = tuple(sorted([asset1, asset2]))
            if pair not in seen_pairs:
                unique_pairs.append({
                    'asset1': asset1,
                    'asset2': asset2,
                    'correlation': corr
                })
                seen_pairs.add(pair)
        
        # Sort by correlation
        unique_pairs.sort(key=lambda x: abs(x['correlation']), reverse=True)
        
        most_correlated = unique_pairs[:n_pairs]
        least_correlated = unique_pairs[-n_pairs:]
        
        return {
            'most_correlated_pairs': most_correlated,
            'least_correlated_pairs': least_correlated
        }
    
    @staticmethod
    def rolling_correlation(returns1: pd.Series, returns2: pd.Series, window: int = 252) -> pd.Series:
        """Calculate rolling correlation between two return series."""
        return returns1.rolling(window=window).corr(returns2)


class VaRCalculator:
    """
    Advanced Value at Risk calculation methods.
    """
    
    @staticmethod
    def historical_var(returns: pd.Series, confidence_levels: list = [0.95, 0.99]) -> Dict[str, float]:
        """Calculate historical VaR for multiple confidence levels."""
        var_results = {}
        for confidence_level in confidence_levels:
            var_results[f'var_{int(confidence_level*100)}'] = np.percentile(returns, (1 - confidence_level) * 100)
        return var_results
    
    @staticmethod
    def parametric_var(returns: pd.Series, confidence_levels: list = [0.95, 0.99]) -> Dict[str, float]:
        """Calculate parametric VaR assuming normal distribution."""
        mean = returns.mean()
        std = returns.std()
        
        var_results = {}
        for confidence_level in confidence_levels:
            z_score = stats.norm.ppf(1 - confidence_level)
            var_results[f'var_{int(confidence_level*100)}_parametric'] = mean + z_score * std
        
        return var_results
    
    @staticmethod
    def conditional_var(returns: pd.Series, confidence_levels: list = [0.95, 0.99]) -> Dict[str, float]:
        """Calculate Conditional VaR (Expected Shortfall)."""
        cvar_results = {}
        for confidence_level in confidence_levels:
            var_threshold = np.percentile(returns, (1 - confidence_level) * 100)
            tail_losses = returns[returns <= var_threshold]
            cvar_results[f'cvar_{int(confidence_level*100)}'] = tail_losses.mean() if len(tail_losses) > 0 else np.nan
        
        return cvar_results
    
    @staticmethod
    def monte_carlo_var(returns: pd.Series, confidence_levels: list = [0.95, 0.99], 
                       n_simulations: int = 10000) -> Dict[str, float]:
        """Calculate Monte Carlo VaR."""
        # Fit normal distribution to historical returns
        mean = returns.mean()
        std = returns.std()
        
        # Generate random scenarios
        simulated_returns = np.random.normal(mean, std, n_simulations)
        
        var_results = {}
        for confidence_level in confidence_levels:
            var_results[f'var_{int(confidence_level*100)}_mc'] = np.percentile(simulated_returns, (1 - confidence_level) * 100)
        
        return var_results
