/**
 * Chart Data Types
 * Common type definitions for chart components
 */

// Time series data types
export interface TimeSeriesDataPoint {
  date: string;
  value: number;
}

export interface PerformanceTimeSeriesData {
  portfolio: TimeSeriesDataPoint[];
  benchmark?: TimeSeriesDataPoint[];
  riskFreeRate?: TimeSeriesDataPoint[];
}

// Risk metrics data types
export interface RiskDataPoint {
  date: string;
  value: number;
}

export interface RiskMetricsData {
  drawdown: RiskDataPoint[];
  volatility: RiskDataPoint[];
  var95: RiskDataPoint[];
  var99: RiskDataPoint[];
  returns: RiskDataPoint[];
}

// Rolling metrics data types
export interface RollingDataPoint {
  date: string;
  value: number;
}

export interface RollingMetricsData {
  sharpe: RollingDataPoint[];
  beta: RollingDataPoint[];
  alpha: RollingDataPoint[];
  correlation: RollingDataPoint[];
  informationRatio: RollingDataPoint[];
  treynorRatio: RollingDataPoint[];
}

// Asset allocation data types
export interface AllocationItem {
  label: string;
  value: number;
  percentage: number;
  color?: string;
  category?: string;
  subItems?: AllocationItem[];
}

export interface AssetAllocationData {
  byAsset: AllocationItem[];
  bySector: AllocationItem[];
  byAssetClass: AllocationItem[];
  byGeography?: AllocationItem[];
  byMarketCap?: AllocationItem[];
}

// Portfolio comparison data types
export interface PerformanceDataPoint {
  date: string;
  portfolio: number;
  benchmark: number;
}

export interface ComparisonMetrics {
  totalReturn: { portfolio: number; benchmark: number };
  volatility: { portfolio: number; benchmark: number };
  sharpeRatio: { portfolio: number; benchmark: number };
  maxDrawdown: { portfolio: number; benchmark: number };
  beta: number;
  alpha: number;
  correlation: number;
  informationRatio: number;
  trackingError: number;
  upCapture: number;
  downCapture: number;
}

export interface PortfolioComparisonData {
  performanceData: PerformanceDataPoint[];
  metrics: ComparisonMetrics;
  benchmarkName: string;
  portfolioName: string;
}

// Return distribution data types
export interface ReturnDataPoint {
  date: string;
  return: number;
}

export interface DistributionStats {
  mean: number;
  median: number;
  standardDeviation: number;
  skewness: number;
  kurtosis: number;
  var95: number;
  var99: number;
  cvar95: number;
  cvar99: number;
  jarqueBera: number;
  shapiroWilk: number;
  positiveReturns: number;
  negativeReturns: number;
  maxReturn: number;
  minReturn: number;
}

export interface ReturnDistributionData {
  returns: ReturnDataPoint[];
  benchmarkReturns?: ReturnDataPoint[];
  stats: DistributionStats;
  benchmarkStats?: DistributionStats;
}
