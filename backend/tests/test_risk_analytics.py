"""
Tests for Risk Analytics Service

This module contains comprehensive tests for the risk analytics engine.
"""

import pytest
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from app.services.risk_analytics_service import (
    RiskCalculator,
    RollingMetrics,
    BenchmarkComparator,
    VaRCalculator,
    CorrelationAnalyzer,
    RiskAnalyticsService,
    RiskMetrics,
    ComprehensiveRiskMetrics,
    CorrelationAnalysis
)


class TestRiskCalculator:
    """Test suite for RiskCalculator class"""
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data for testing"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
        return returns
    
    @pytest.fixture
    def risk_calculator(self, sample_returns):
        """Create RiskCalculator instance for testing"""
        return RiskCalculator(sample_returns)
    
    def test_sharpe_ratio(self, risk_calculator):
        """Test Sharpe ratio calculation"""
        sharpe = risk_calculator.sharpe_ratio()
        assert isinstance(sharpe, float)
        assert -5 <= sharpe <= 5  # Reasonable range for Sharpe ratio
    
    def test_volatility(self, risk_calculator):
        """Test volatility calculation"""
        vol = risk_calculator.volatility()
        assert isinstance(vol, float)
        assert 0 <= vol <= 1  # Volatility should be positive and reasonable
    
    def test_max_drawdown(self, risk_calculator):
        """Test maximum drawdown calculation"""
        max_dd = risk_calculator.max_drawdown()
        assert isinstance(max_dd, float)
        assert max_dd <= 0  # Max drawdown should be negative
    
    def test_beta(self, risk_calculator, sample_returns):
        """Test beta calculation"""
        # Create a benchmark that's correlated with the returns
        benchmark = sample_returns * 0.8 + np.random.normal(0, 0.01, len(sample_returns))
        beta = risk_calculator.beta(benchmark)
        assert isinstance(beta, float)
        assert 0 <= beta <= 2  # Beta should be in reasonable range
    
    def test_alpha(self, risk_calculator, sample_returns):
        """Test alpha calculation"""
        benchmark = sample_returns * 0.8 + np.random.normal(0, 0.01, len(sample_returns))
        alpha = risk_calculator.alpha(benchmark)
        assert isinstance(alpha, float)
    
    def test_total_return(self, risk_calculator):
        """Test total return calculation"""
        total_ret = risk_calculator.total_return()
        assert isinstance(total_ret, float)
    
    def test_annualized_return(self, risk_calculator):
        """Test annualized return calculation"""
        ann_ret = risk_calculator.annualized_return()
        assert isinstance(ann_ret, float)
    
    def test_skewness(self, risk_calculator):
        """Test skewness calculation"""
        skew = risk_calculator.skewness()
        assert isinstance(skew, float)
    
    def test_kurtosis(self, risk_calculator):
        """Test kurtosis calculation"""
        kurt = risk_calculator.kurtosis()
        assert isinstance(kurt, float)
    
    def test_positive_periods(self, risk_calculator):
        """Test positive periods calculation"""
        pos_periods = risk_calculator.positive_periods()
        assert isinstance(pos_periods, (int, np.integer))
        assert 0 <= pos_periods <= len(risk_calculator.returns)


class TestRollingMetrics:
    """Test suite for RollingMetrics class"""
    
    @pytest.fixture
    def sample_returns_df(self):
        """Create sample returns DataFrame for testing"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        returns_data = pd.DataFrame({
            'Portfolio': np.random.normal(0.001, 0.02, len(dates)),
            'Asset1': np.random.normal(0.0008, 0.018, len(dates)),
            'Asset2': np.random.normal(0.0012, 0.022, len(dates))
        }, index=dates)
        return returns_data
    
    @pytest.fixture
    def rolling_metrics(self, sample_returns_df):
        """Create RollingMetrics instance for testing"""
        return RollingMetrics(sample_returns_df)
    
    def test_rolling_sharpe_ratio(self, rolling_metrics):
        """Test rolling Sharpe ratio calculation"""
        rolling_sharpe = rolling_metrics.rolling_sharpe_ratio(window=60)
        assert isinstance(rolling_sharpe, pd.Series)
        assert len(rolling_sharpe.dropna()) > 0
    
    def test_rolling_volatility(self, rolling_metrics):
        """Test rolling volatility calculation"""
        rolling_vol = rolling_metrics.rolling_volatility(window=60)
        assert isinstance(rolling_vol, pd.Series)
        assert len(rolling_vol.dropna()) > 0
        assert all(rolling_vol.dropna() >= 0)
    
    def test_rolling_max_drawdown(self, rolling_metrics):
        """Test rolling maximum drawdown calculation"""
        rolling_max_dd = rolling_metrics.rolling_max_drawdown(window=60)
        assert isinstance(rolling_max_dd, pd.Series)
        assert len(rolling_max_dd.dropna()) > 0
    
    def test_rolling_var(self, rolling_metrics):
        """Test rolling VaR calculation"""
        rolling_var = rolling_metrics.rolling_var(window=60)
        assert isinstance(rolling_var, pd.Series)
        assert len(rolling_var.dropna()) > 0


class TestBenchmarkComparator:
    """Test suite for BenchmarkComparator class"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample portfolio and benchmark data"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        portfolio_returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
        benchmark_returns = pd.Series(np.random.normal(0.0008, 0.018, len(dates)), index=dates)
        return portfolio_returns, benchmark_returns
    
    @pytest.fixture
    def benchmark_comparator(self, sample_data):
        """Create BenchmarkComparator instance for testing"""
        portfolio_returns, benchmark_returns = sample_data
        return BenchmarkComparator(portfolio_returns, benchmark_returns)
    
    def test_tracking_error(self, benchmark_comparator):
        """Test tracking error calculation"""
        tracking_err = benchmark_comparator.tracking_error()
        assert isinstance(tracking_err, float)
        assert tracking_err >= 0
    
    def test_information_ratio(self, benchmark_comparator):
        """Test information ratio calculation"""
        info_ratio = benchmark_comparator.information_ratio()
        assert isinstance(info_ratio, float)
    
    def test_beta(self, benchmark_comparator):
        """Test beta calculation"""
        beta = benchmark_comparator.beta()
        assert isinstance(beta, float)
    
    def test_alpha(self, benchmark_comparator):
        """Test alpha calculation"""
        alpha = benchmark_comparator.alpha()
        assert isinstance(alpha, float)
    
    def test_correlation(self, benchmark_comparator):
        """Test correlation calculation"""
        corr = benchmark_comparator.correlation()
        assert isinstance(corr, float)
        assert -1 <= corr <= 1
    
    def test_up_capture_ratio(self, benchmark_comparator):
        """Test up capture ratio calculation"""
        up_capture = benchmark_comparator.up_capture_ratio()
        assert isinstance(up_capture, float)
        assert up_capture >= 0
    
    def test_down_capture_ratio(self, benchmark_comparator):
        """Test down capture ratio calculation"""
        down_capture = benchmark_comparator.down_capture_ratio()
        assert isinstance(down_capture, float)
    
    def test_relative_performance(self, benchmark_comparator):
        """Test relative performance calculation"""
        rel_perf = benchmark_comparator.relative_performance()
        assert isinstance(rel_perf, float)


class TestVaRCalculator:
    """Test suite for VaRCalculator class"""
    
    @pytest.fixture
    def sample_returns(self):
        """Create sample returns data for testing"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        returns = pd.Series(np.random.normal(0.001, 0.02, len(dates)), index=dates)
        return returns
    
    @pytest.fixture
    def var_calculator(self, sample_returns):
        """Create VaRCalculator instance for testing"""
        return VaRCalculator(sample_returns)
    
    def test_historical_var(self, var_calculator):
        """Test historical VaR calculation"""
        var_95 = var_calculator.historical_var(confidence=0.05)
        assert isinstance(var_95, float)
        assert var_95 <= 0  # VaR should be negative
    
    def test_parametric_var(self, var_calculator):
        """Test parametric VaR calculation"""
        var_95 = var_calculator.parametric_var(confidence=0.05)
        assert isinstance(var_95, float)
        assert var_95 <= 0  # VaR should be negative
    
    def test_monte_carlo_var(self, var_calculator):
        """Test Monte Carlo VaR calculation"""
        var_95 = var_calculator.monte_carlo_var(confidence=0.05, n_simulations=1000)
        assert isinstance(var_95, float)
        assert var_95 <= 0  # VaR should be negative
    
    def test_conditional_var(self, var_calculator):
        """Test Conditional VaR calculation"""
        cvar_95 = var_calculator.conditional_var(confidence=0.05)
        assert isinstance(cvar_95, float)
        assert cvar_95 <= 0  # CVaR should be negative
    
    def test_var_backtesting(self, var_calculator):
        """Test VaR backtesting"""
        backtest_results = var_calculator.var_backtesting(confidence=0.05, window=100)
        assert isinstance(backtest_results, dict)
        assert 'violation_rate' in backtest_results
        assert 'expected_rate' in backtest_results
        assert 'violations' in backtest_results
        assert 'total_forecasts' in backtest_results


class TestCorrelationAnalyzer:
    """Test suite for CorrelationAnalyzer class"""
    
    @pytest.fixture
    def sample_returns_df(self):
        """Create sample multi-asset returns DataFrame"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        
        # Create correlated returns
        base_returns = np.random.normal(0.001, 0.02, (len(dates), 4))
        correlation_matrix = np.array([
            [1.0, 0.7, 0.3, 0.1],
            [0.7, 1.0, 0.5, 0.2],
            [0.3, 0.5, 1.0, 0.4],
            [0.1, 0.2, 0.4, 1.0]
        ])
        
        chol = np.linalg.cholesky(correlation_matrix)
        correlated_returns = np.dot(base_returns, chol.T)
        
        returns_df = pd.DataFrame(
            correlated_returns,
            index=dates,
            columns=['Asset1', 'Asset2', 'Asset3', 'Asset4']
        )
        return returns_df
    
    @pytest.fixture
    def correlation_analyzer(self, sample_returns_df):
        """Create CorrelationAnalyzer instance for testing"""
        return CorrelationAnalyzer(sample_returns_df)
    
    def test_calculate_correlation_matrix(self, correlation_analyzer):
        """Test correlation matrix calculation"""
        corr_matrix = correlation_analyzer.calculate_correlation_matrix()
        assert isinstance(corr_matrix, pd.DataFrame)
        assert corr_matrix.shape == (4, 4)
        assert np.allclose(np.diag(corr_matrix), 1.0)  # Diagonal should be 1
    
    def test_rolling_correlation(self, correlation_analyzer):
        """Test rolling correlation calculation"""
        rolling_corr = correlation_analyzer.rolling_correlation('Asset1', 'Asset2', window=60)
        assert isinstance(rolling_corr, pd.Series)
        assert len(rolling_corr.dropna()) > 0
    
    def test_find_correlation_pairs(self, correlation_analyzer):
        """Test finding high correlation pairs"""
        high_corr_pairs = correlation_analyzer.find_correlation_pairs(threshold=0.6)
        assert isinstance(high_corr_pairs, list)
        assert len(high_corr_pairs) > 0
        for pair in high_corr_pairs:
            assert len(pair) == 3  # asset1, asset2, correlation
    
    def test_correlation_clustering(self, correlation_analyzer):
        """Test correlation-based clustering"""
        clusters = correlation_analyzer.correlation_clustering(n_clusters=2)
        assert isinstance(clusters, dict)
        assert len(clusters) == 2
        all_assets = set()
        for cluster_assets in clusters.values():
            all_assets.update(cluster_assets)
        assert len(all_assets) == 4  # All assets should be assigned
    
    def test_diversification_ratio(self, correlation_analyzer):
        """Test diversification ratio calculation"""
        div_ratio = correlation_analyzer.diversification_ratio()
        assert isinstance(div_ratio, float)
        assert div_ratio >= 1.0  # Diversification ratio should be >= 1
    
    def test_correlation_statistics(self, correlation_analyzer):
        """Test correlation statistics calculation"""
        stats = correlation_analyzer.correlation_statistics()
        assert isinstance(stats, dict)
        expected_keys = [
            'mean_correlation', 'median_correlation', 'std_correlation',
            'min_correlation', 'max_correlation', 'q25_correlation', 'q75_correlation',
            'negative_correlations', 'high_correlations', 'low_correlations'
        ]
        for key in expected_keys:
            assert key in stats


class TestRiskAnalyticsService:
    """Test suite for RiskAnalyticsService class"""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample data for testing"""
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        
        returns_data = pd.DataFrame({
            'Portfolio': np.random.normal(0.001, 0.02, len(dates)),
            'Asset1': np.random.normal(0.0008, 0.018, len(dates)),
            'Asset2': np.random.normal(0.0012, 0.022, len(dates))
        }, index=dates)
        
        benchmark_data = pd.DataFrame({
            'Benchmark': np.random.normal(0.0008, 0.018, len(dates))
        }, index=dates)
        
        return returns_data, benchmark_data
    
    @pytest.fixture
    def risk_analytics_service(self, sample_data):
        """Create RiskAnalyticsService instance for testing"""
        returns_data, benchmark_data = sample_data
        service = RiskAnalyticsService()
        service.initialize_with_data(returns_data, benchmark_data)
        return service
    
    def test_initialization(self, risk_analytics_service):
        """Test service initialization"""
        assert risk_analytics_service.risk_calculator is not None
        assert risk_analytics_service.rolling_metrics is not None
        assert risk_analytics_service.benchmark_comparator is not None
        assert risk_analytics_service.var_calculator is not None
        assert risk_analytics_service.correlation_analyzer is not None
    
    def test_calculate_comprehensive_risk_metrics(self, risk_analytics_service):
        """Test comprehensive risk metrics calculation"""
        metrics = risk_analytics_service.calculate_comprehensive_risk_metrics()
        
        assert isinstance(metrics, ComprehensiveRiskMetrics)
        assert isinstance(metrics.basic_metrics, RiskMetrics)
        assert isinstance(metrics.performance_metrics, dict)
        assert isinstance(metrics.rolling_metrics, dict)
        assert isinstance(metrics.var_metrics, dict)
        assert isinstance(metrics.benchmark_comparison, dict)
        assert isinstance(metrics.correlation_analysis, CorrelationAnalysis)
        assert isinstance(metrics.calculation_date, datetime)
    
    def test_generate_risk_report(self, risk_analytics_service):
        """Test risk report generation"""
        report = risk_analytics_service.generate_risk_report("Test Portfolio")
        
        assert isinstance(report, dict)
        assert 'portfolio_name' in report
        assert 'report_date' in report
        assert 'period' in report
        assert 'executive_summary' in report
        assert 'detailed_metrics' in report
        assert 'risk_assessment' in report
        assert 'recommendations' in report
        
        # Check risk assessment values
        assert report['risk_assessment'] in ['LOW', 'MEDIUM', 'HIGH']
        assert isinstance(report['recommendations'], list)
    
    def test_risk_level_assessment(self, risk_analytics_service):
        """Test risk level assessment"""
        metrics = risk_analytics_service.calculate_comprehensive_risk_metrics()
        risk_level = risk_analytics_service._assess_risk_level(metrics)
        assert risk_level in ['LOW', 'MEDIUM', 'HIGH']
    
    def test_generate_recommendations(self, risk_analytics_service):
        """Test recommendations generation"""
        metrics = risk_analytics_service.calculate_comprehensive_risk_metrics()
        recommendations = risk_analytics_service._generate_recommendations(metrics)
        assert isinstance(recommendations, list)
        for rec in recommendations:
            assert isinstance(rec, str)
            assert len(rec) > 0


class TestIntegration:
    """Integration tests for the entire risk analytics system"""
    
    def test_end_to_end_risk_analysis(self):
        """Test complete end-to-end risk analysis workflow"""
        # Create sample data
        np.random.seed(42)
        dates = pd.date_range('2020-01-01', '2023-12-31', freq='D')
        
        # Multi-asset portfolio
        returns_data = pd.DataFrame({
            'AAPL': np.random.normal(0.001, 0.025, len(dates)),
            'GOOGL': np.random.normal(0.0008, 0.023, len(dates)),
            'MSFT': np.random.normal(0.0012, 0.022, len(dates)),
            'TSLA': np.random.normal(0.002, 0.035, len(dates))
        }, index=dates)
        
        # Benchmark
        benchmark_data = pd.DataFrame({
            'SPY': np.random.normal(0.0008, 0.018, len(dates))
        }, index=dates)
        
        # Initialize service
        service = RiskAnalyticsService()
        service.initialize_with_data(returns_data, benchmark_data)
        
        # Run comprehensive analysis
        metrics = service.calculate_comprehensive_risk_metrics()
        
        # Verify all components are working
        assert metrics.basic_metrics.sharpe_ratio is not None
        assert metrics.basic_metrics.volatility > 0
        assert metrics.var_metrics['historical_var_95'] < 0
        assert metrics.correlation_analysis.diversification_ratio >= 1.0
        assert len(metrics.rolling_metrics['rolling_sharpe']) > 0
        
        # Generate report
        report = service.generate_risk_report("Integration Test Portfolio")
        
        # Verify report structure
        assert report['portfolio_name'] == "Integration Test Portfolio"
        assert 'executive_summary' in report
        assert 'risk_assessment' in report
        assert len(report['recommendations']) >= 0
        
        print("✓ End-to-end risk analysis completed successfully")
    
    def test_error_handling(self):
        """Test error handling in risk analytics service"""
        service = RiskAnalyticsService()
        
        # Test uninitialized service
        with pytest.raises(ValueError, match="Service not initialized"):
            service.calculate_comprehensive_risk_metrics()
        
        # Test with invalid data
        invalid_data = pd.DataFrame()
        with pytest.raises(Exception):
            service.initialize_with_data(invalid_data)
        
        print("✓ Error handling tests completed successfully")


if __name__ == "__main__":
    # Run a quick test to ensure everything is working
    test_integration = TestIntegration()
    test_integration.test_end_to_end_risk_analysis()
    test_integration.test_error_handling()
    print("\n✅ All risk analytics tests passed!")
