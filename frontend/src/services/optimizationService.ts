/**
 * Portfolio Optimization Service
 * Client-side service for portfolio optimization API calls
 */

import apiClient from './apiClient';

export interface OptimizationMethod {
  method: string;
  name: string;
  description: string;
  requires_target: boolean;
  target_type?: string;
}

export interface AssetConstraint {
  symbol: string;
  min_weight?: number;
  max_weight?: number;
}

export interface SectorConstraint {
  sector: string;
  min_allocation?: number;
  max_allocation?: number;
}

export interface OptimizationConstraints {
  min_weight: number;
  max_weight: number;
  asset_constraints?: AssetConstraint[];
  sector_constraints?: SectorConstraint[];
  max_turnover?: number;
}

export interface OptimizationRequest {
  asset_symbols: string[];
  optimization_method: string;
  lookback_days: number;
  risk_free_rate: number;
  target_return?: number;
  target_volatility?: number;
  constraints?: OptimizationConstraints;
  risk_aversion?: number;
}

export interface EfficientFrontierRequest {
  asset_symbols: string[];
  lookback_days: number;
  risk_free_rate: number;
  n_points: number;
  constraints?: OptimizationConstraints;
}

export interface PortfolioMetrics {
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown?: number;
  var_95?: number;
  beta?: number;
}

export interface OptimizedPortfolio {
  optimization_method: string;
  weights: Record<string, number>;
  metrics: PortfolioMetrics;
  optimization_date: string;
  risk_free_rate: number;
  target_return?: number;
  target_volatility?: number;
}

export interface FrontierPoint {
  expected_return: number;
  volatility: number;
  weights: Record<string, number>;
  sharpe_ratio: number;
}

export interface KeyPortfolio {
  name: string;
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
}

export interface EfficientFrontierData {
  frontier_points: FrontierPoint[];
  key_portfolios: KeyPortfolio[];
  assets: string[];
  optimization_date: string;
  risk_free_rate: number;
}

export interface RebalancingRequest {
  portfolio_id: number;
  target_weights: Record<string, number>;
  tolerance: number;
}

export interface TradeRecommendation {
  symbol: string;
  action: string;
  current_weight: number;
  target_weight: number;
  weight_difference: number;
  dollar_amount: number;
  shares_to_trade: number;
  current_price: number;
}

export interface RebalancingResponse {
  rebalancing_needed: boolean;
  current_weights: Record<string, number>;
  target_weights: Record<string, number>;
  trades: TradeRecommendation[];
  total_portfolio_value: number;
  tolerance: number;
  analysis_date: string;
}

export interface ScenarioDefinition {
  name: string;
  description: string;
  return_shock?: {
    value: number;
    assets?: string[];
  };
  volatility_shock?: {
    multiplier: number;
    assets?: string[];
  };
  correlation_shock?: {
    factor: number;
  };
}

export interface ScenarioResult {
  description: string;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  var_95: number;
  total_return: number;
}

export interface ScenarioAnalysisRequest {
  weights: Record<string, number>;
  asset_symbols: string[];
  scenarios: ScenarioDefinition[];
  lookback_days: number;
}

export interface ScenarioAnalysisResponse {
  scenarios: Record<string, ScenarioResult>;
  base_portfolio_weights: Record<string, number>;
  analysis_date: string;
}

export interface DiscreteAllocationRequest {
  weights: Record<string, number>;
  total_portfolio_value: number;
  latest_prices?: Record<string, number>;
}

export interface DiscreteAllocationResponse {
  allocation: Record<string, number>;
  leftover_cash: number;
  total_allocated: number;
  allocation_percentage: number;
  total_value: number;
}

export interface RiskBudgetingRequest {
  asset_symbols: string[];
  risk_budget: Record<string, number>;
  lookback_days: number;
}

export interface RiskBudgetingResponse {
  weights: Record<string, number>;
  risk_contributions: Record<string, number>;
  target_risk_budget: Record<string, number>;
  portfolio_volatility: number;
}

export interface BacktestRequest {
  weights: Record<string, number>;
  start_date: string;
  end_date: string;
  rebalancing_frequency: string;
  transaction_costs: number;
}

export interface BacktestResult {
  total_return: number;
  annualized_return: number;
  volatility: number;
  sharpe_ratio: number;
  max_drawdown: number;
  calmar_ratio: number;
  win_rate: number;
  portfolio_values: Array<{ date: string; value: number }>;
  returns: number[];
  dates: string[];
}

export interface BacktestResponse {
  backtest_result: BacktestResult;
  portfolio_weights: Record<string, number>;
  backtest_period: { start_date: string; end_date: string };
  parameters: Record<string, any>;
}

export interface OptimizationResponse<T = any> {
  success: boolean;
  data?: T;
  error?: {
    error_type: string;
    message: string;
    details?: any;
  };
  message: string;
  timestamp: string;
}

class OptimizationService {
  private baseUrl = '/api/v1/optimization';

  /**
   * Get available optimization methods
   */
  async getOptimizationMethods(): Promise<OptimizationMethod[]> {
    const response = await apiClient.get(`${this.baseUrl}/methods`);
    return response.data.data;
  }

  /**
   * Optimize portfolio with specified method and constraints
   */
  async optimizePortfolio(request: OptimizationRequest): Promise<OptimizationResponse<OptimizedPortfolio>> {
    const response = await apiClient.post(`${this.baseUrl}/optimize`, request);
    return response.data;
  }

  /**
   * Calculate efficient frontier
   */
  async calculateEfficientFrontier(request: EfficientFrontierRequest): Promise<OptimizationResponse<EfficientFrontierData>> {
    const response = await apiClient.post(`${this.baseUrl}/efficient-frontier`, request);
    return response.data;
  }

  /**
   * Generate rebalancing suggestions
   */
  async generateRebalancingSuggestions(request: RebalancingRequest): Promise<OptimizationResponse<RebalancingResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/rebalancing`, request);
    return response.data;
  }

  /**
   * Run scenario analysis
   */
  async runScenarioAnalysis(request: ScenarioAnalysisRequest): Promise<OptimizationResponse<ScenarioAnalysisResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/scenario-analysis`, request);
    return response.data;
  }

  /**
   * Calculate risk budgeting allocation
   */
  async calculateRiskBudgeting(request: RiskBudgetingRequest): Promise<OptimizationResponse<RiskBudgetingResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/risk-budgeting`, request);
    return response.data;
  }

  /**
   * Calculate discrete allocation for trading
   */
  async calculateDiscreteAllocation(request: DiscreteAllocationRequest): Promise<OptimizationResponse<DiscreteAllocationResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/discrete-allocation`, request);
    return response.data;
  }

  /**
   * Get current portfolio allocation for optimization
   */
  async getCurrentPortfolioAllocation(portfolioId: number): Promise<{
    portfolio_id: number;
    current_weights: Record<string, number>;
    total_value: number;
    last_updated: string;
  }> {
    const response = await apiClient.get(`${this.baseUrl}/portfolio/${portfolioId}/current-allocation`);
    return response.data.data;
  }

  /**
   * Backtest portfolio strategy
   */
  async backtestPortfolio(request: BacktestRequest): Promise<OptimizationResponse<BacktestResponse>> {
    const response = await apiClient.post(`${this.baseUrl}/backtest`, request);
    return response.data;
  }

  /**
   * Compare multiple optimization strategies
   */
  async compareOptimizationStrategies(
    assetSymbols: string[],
    methods: string[],
    lookbackDays: number = 252,
    riskFreeRate: number = 0.02
  ): Promise<Record<string, OptimizedPortfolio>> {
    const promises = methods.map(method =>
      this.optimizePortfolio({
        asset_symbols: assetSymbols,
        optimization_method: method,
        lookback_days: lookbackDays,
        risk_free_rate: riskFreeRate
      })
    );

    const results = await Promise.allSettled(promises);
    const comparison: Record<string, OptimizedPortfolio> = {};

    results.forEach((result, index) => {
      if (result.status === 'fulfilled' && result.value.success) {
        comparison[methods[index]] = result.value.data!;
      }
    });

    return comparison;
  }

  /**
   * Calculate portfolio concentration metrics
   */
  calculateConcentrationMetrics(weights: Record<string, number>): {
    hhi: number; // Herfindahl-Hirschman Index
    effectiveAssets: number;
    maxWeight: number;
    top3Concentration: number;
    giniCoefficient: number;
  } {
    const weightValues = Object.values(weights).filter(w => w > 0);
    const sortedWeights = weightValues.sort((a, b) => b - a);

    // Herfindahl-Hirschman Index
    const hhi = weightValues.reduce((sum, weight) => sum + weight * weight, 0);

    // Effective number of assets
    const effectiveAssets = 1 / hhi;

    // Maximum weight
    const maxWeight = Math.max(...weightValues);

    // Top 3 concentration
    const top3Concentration = sortedWeights.slice(0, 3).reduce((sum, weight) => sum + weight, 0);

    // Gini coefficient (simplified calculation)
    const n = weightValues.length;
    const sumWeights = weightValues.reduce((sum, weight) => sum + weight, 0);
    let giniSum = 0;
    
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        giniSum += Math.abs(weightValues[i] - weightValues[j]);
      }
    }
    
    const giniCoefficient = giniSum / (2 * n * sumWeights);

    return {
      hhi,
      effectiveAssets,
      maxWeight,
      top3Concentration,
      giniCoefficient
    };
  }

  /**
   * Calculate turnover between two portfolio allocations
   */
  calculateTurnover(
    currentWeights: Record<string, number>,
    targetWeights: Record<string, number>
  ): number {
    const allAssets = new Set([...Object.keys(currentWeights), ...Object.keys(targetWeights)]);
    let totalTurnover = 0;

    allAssets.forEach(asset => {
      const currentWeight = currentWeights[asset] || 0;
      const targetWeight = targetWeights[asset] || 0;
      totalTurnover += Math.abs(targetWeight - currentWeight);
    });

    return totalTurnover / 2; // Divide by 2 since we count both buys and sells
  }

  /**
   * Generate optimization report
   */
  generateOptimizationReport(
    optimizedPortfolio: OptimizedPortfolio,
    currentWeights?: Record<string, number>
  ): {
    summary: string;
    metrics: Record<string, any>;
    concentration: any;
    turnover?: number;
    recommendations: string[];
  } {
    const metrics = optimizedPortfolio.metrics;
    const weights = optimizedPortfolio.weights;
    const concentration = this.calculateConcentrationMetrics(weights);
    
    let turnover: number | undefined;
    if (currentWeights) {
      turnover = this.calculateTurnover(currentWeights, weights);
    }

    const recommendations: string[] = [];

    // Performance recommendations
    if (metrics.sharpe_ratio > 1.5) {
      recommendations.push("Excellent risk-adjusted returns expected");
    } else if (metrics.sharpe_ratio < 0.5) {
      recommendations.push("Consider reviewing asset selection - low risk-adjusted returns");
    }

    // Concentration recommendations
    if (concentration.hhi > 0.25) {
      recommendations.push("Portfolio is highly concentrated - consider diversification");
    }
    if (concentration.maxWeight > 0.4) {
      recommendations.push("Single asset dominates portfolio - reduce concentration risk");
    }

    // Turnover recommendations
    if (turnover && turnover > 0.5) {
      recommendations.push("High turnover required - consider transaction costs");
    }

    const summary = `Optimized portfolio using ${optimizedPortfolio.optimization_method} strategy 
      targeting ${(metrics.expected_return * 100).toFixed(1)}% annual return with 
      ${(metrics.volatility * 100).toFixed(1)}% volatility.`;

    return {
      summary,
      metrics: {
        expectedReturn: metrics.expected_return,
        volatility: metrics.volatility,
        sharpeRatio: metrics.sharpe_ratio,
        maxDrawdown: metrics.max_drawdown,
        var95: metrics.var_95,
        beta: metrics.beta
      },
      concentration,
      turnover,
      recommendations
    };
  }
}

export const optimizationService = new OptimizationService();
