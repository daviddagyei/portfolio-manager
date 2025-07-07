/**
 * Risk Analytics Service
 * Handles API communication for risk analytics endpoints
 */

import apiClient from './apiClient';

// Type definitions
export interface RiskMetrics {
  sharpe_ratio: number;
  beta?: number;
  volatility: number;
  max_drawdown: number;
  var_95: number;
  cvar_95: number;
  calmar_ratio: number;
  sortino_ratio: number;
  information_ratio?: number;
  alpha?: number;
}

export interface PerformanceMetrics {
  total_return: number;
  annualized_return: number;
  annualized_volatility: number;
  skewness: number;
  kurtosis: number;
  positive_periods: number;
  negative_periods: number;
}

export interface RollingMetrics {
  rolling_sharpe: number[];
  rolling_volatility: number[];
  rolling_max_drawdown: number[];
  rolling_var: number[];
}

export interface VaRMetrics {
  historical_var_95: number;
  historical_var_99: number;
  parametric_var_95: number;
  parametric_var_99: number;
  monte_carlo_var_95: number;
  cvar_95: number;
  cvar_99: number;
}

export interface BenchmarkComparison {
  tracking_error: number;
  information_ratio: number;
  beta: number;
  alpha: number;
  correlation: number;
  up_capture: number;
  down_capture: number;
  relative_return: number;
}

export interface CorrelationAnalysis {
  correlation_matrix: Record<string, Record<string, number>>;
  high_correlation_pairs: Array<{
    asset1: string;
    asset2: string;
    correlation: number;
  }>;
  correlation_statistics: Record<string, number>;
  diversification_ratio: number;
  asset_clusters: Record<number, string[]>;
}

export interface ComprehensiveRiskMetrics {
  basic_metrics: RiskMetrics;
  performance_metrics: PerformanceMetrics;
  rolling_metrics: RollingMetrics;
  var_metrics: VaRMetrics;
  benchmark_comparison?: BenchmarkComparison;
  correlation_analysis?: CorrelationAnalysis;
  calculation_date: string;
  period_start: string;
  period_end: string;
  data_points: number;
}

export interface RiskAnalysisRequest {
  returns_data: Array<Record<string, any>>;
  benchmark_data?: Array<Record<string, any>>;
  risk_free_rate?: number;
  rolling_window?: number;
  var_confidence?: number;
  include_benchmark?: boolean;
  include_correlation?: boolean;
}

export interface RiskAnalysisResponse {
  success: boolean;
  data?: ComprehensiveRiskMetrics;
  error?: string;
}

export interface RiskReportRequest {
  returns_data: Array<Record<string, any>>;
  portfolio_name: string;
  benchmark_data?: Array<Record<string, any>>;
  risk_free_rate?: number;
  rolling_window?: number;
}

export interface RiskReportResponse {
  success: boolean;
  data?: Record<string, any>;
  error?: string;
}

export interface VaRAnalysisResult {
  success: boolean;
  portfolio_id: number;
  portfolio_name: string;
  confidence_levels: number[];
  methods: string[];
  var_results: Record<string, Record<string, number>>;
  backtesting_results: Record<string, Record<string, number>>;
  data_points: number;
}

export interface RollingMetricsResult {
  success: boolean;
  portfolio_id: number;
  portfolio_name: string;
  window: number;
  metrics: string[];
  data: Record<string, {
    dates: string[];
    values: number[];
  }>;
  total_data_points: number;
}

export interface CorrelationMatrixResult {
  success: boolean;
  portfolio_id: number;
  portfolio_name: string;
  method: string;
  threshold: number;
  correlation_matrix: Record<string, Record<string, number>>;
  high_correlation_pairs: Array<{
    asset1: string;
    asset2: string;
    correlation: number;
  }>;
  correlation_statistics: Record<string, number>;
  diversification_ratio: number;
  asset_clusters: Record<number, string[]>;
  assets: string[];
  data_points: number;
}

export interface RiskDashboardData {
  portfolio_info: {
    id: number;
    name: string;
    type: string;
    created_at: string;
    updated_at: string;
  };
  risk_metrics: ComprehensiveRiskMetrics;
  risk_report: Record<string, any>;
  benchmark_symbol?: string;
  data_period: {
    start: string;
    end: string;
    data_points: number;
  };
  chart_data: {
    returns: {
      dates: string[];
      values: number[];
    };
    cumulative_returns: {
      dates: string[];
      values: number[];
    };
    rolling_sharpe?: {
      dates: string[];
      values: number[];
    };
    rolling_volatility?: {
      dates: string[];
      values: number[];
    };
  };
}

export interface RiskDashboardResult {
  success: boolean;
  data: RiskDashboardData;
}

class RiskAnalyticsService {
  private baseURL = '/api/v1/risk-analytics';

  /**
   * Perform comprehensive risk analysis on custom data
   */
  async comprehensiveAnalysis(request: RiskAnalysisRequest): Promise<RiskAnalysisResponse> {
    const response = await apiClient.post<RiskAnalysisResponse>(
      `${this.baseURL}/comprehensive-analysis`,
      request
    );
    return response.data;
  }

  /**
   * Generate risk report for custom data
   */
  async generateRiskReport(request: RiskReportRequest): Promise<RiskReportResponse> {
    const response = await apiClient.post<RiskReportResponse>(
      `${this.baseURL}/risk-report`,
      request
    );
    return response.data;
  }

  /**
   * Get risk metrics for a specific portfolio
   */
  async getPortfolioRiskMetrics(
    portfolioId: number,
    riskFreeRate: number = 0.02,
    rollingWindow: number = 252
  ): Promise<RiskAnalysisResponse> {
    const response = await apiClient.get<RiskAnalysisResponse>(
      `${this.baseURL}/risk-metrics/${portfolioId}`,
      {
        params: {
          risk_free_rate: riskFreeRate,
          rolling_window: rollingWindow
        }
      }
    );
    return response.data;
  }

  /**
   * Get benchmark comparison for a portfolio
   */
  async getBenchmarkComparison(
    portfolioId: number,
    benchmarkSymbol: string = 'SPY',
    riskFreeRate: number = 0.02
  ): Promise<RiskAnalysisResponse> {
    const response = await apiClient.get<RiskAnalysisResponse>(
      `${this.baseURL}/benchmark-comparison/${portfolioId}`,
      {
        params: {
          benchmark_symbol: benchmarkSymbol,
          risk_free_rate: riskFreeRate
        }
      }
    );
    return response.data;
  }

  /**
   * Get VaR analysis for a portfolio
   */
  async getVaRAnalysis(
    portfolioId: number,
    confidenceLevels: number[] = [0.05, 0.01],
    methods: string[] = ['historical', 'parametric', 'monte_carlo']
  ): Promise<VaRAnalysisResult> {
    const response = await apiClient.get<VaRAnalysisResult>(
      `${this.baseURL}/var-analysis/${portfolioId}`,
      {
        params: {
          confidence_levels: confidenceLevels,
          methods: methods
        }
      }
    );
    return response.data;
  }

  /**
   * Get rolling metrics for a portfolio
   */
  async getRollingMetrics(
    portfolioId: number,
    metrics: string[] = ['sharpe', 'volatility', 'max_drawdown', 'var'],
    window: number = 252,
    riskFreeRate: number = 0.02
  ): Promise<RollingMetricsResult> {
    const response = await apiClient.get<RollingMetricsResult>(
      `${this.baseURL}/rolling-metrics/${portfolioId}`,
      {
        params: {
          metrics: metrics,
          window: window,
          risk_free_rate: riskFreeRate
        }
      }
    );
    return response.data;
  }

  /**
   * Get correlation matrix for portfolio assets
   */
  async getCorrelationMatrix(
    portfolioId: number,
    method: string = 'pearson',
    threshold: number = 0.7
  ): Promise<CorrelationMatrixResult> {
    const response = await apiClient.get<CorrelationMatrixResult>(
      `${this.baseURL}/correlation-matrix/${portfolioId}`,
      {
        params: {
          method: method,
          threshold: threshold
        }
      }
    );
    return response.data;
  }

  /**
   * Get comprehensive risk dashboard data
   */
  async getRiskDashboard(
    portfolioId: number,
    riskFreeRate: number = 0.02,
    benchmarkSymbol: string = 'SPY'
  ): Promise<RiskDashboardResult> {
    const response = await apiClient.get<RiskDashboardResult>(
      `${this.baseURL}/risk-dashboard/${portfolioId}`,
      {
        params: {
          risk_free_rate: riskFreeRate,
          benchmark_symbol: benchmarkSymbol
        }
      }
    );
    return response.data;
  }

  /**
   * Check risk analytics service health
   */
  async healthCheck(): Promise<{ status: string; service: string; timestamp: string }> {
    const response = await apiClient.get(`${this.baseURL}/health`);
    return response.data;
  }
}

export const riskAnalyticsService = new RiskAnalyticsService();
export default riskAnalyticsService;
