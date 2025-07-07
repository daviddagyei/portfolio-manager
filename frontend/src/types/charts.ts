/**
 * Chart Types and Interfaces
 * Common types used across all chart components
 */

export interface TimeSeriesDataPoint {
  date: string;
  value: number;
  label?: string;
}

export interface ChartDataset {
  label: string;
  data: TimeSeriesDataPoint[];
  color?: string;
  borderColor?: string;
  backgroundColor?: string;
  borderDash?: number[];
  fill?: boolean;
  tension?: number;
}

export interface ChartMetrics {
  sharpeRatio: number;
  volatility: number;
  maxDrawdown: number;
  var95: number;
  beta?: number;
  alpha?: number;
  totalReturn: number;
  annualizedReturn: number;
}

export interface RollingMetrics {
  dates: string[];
  sharpeRatio: number[];
  volatility: number[];
  beta?: number[];
  alpha?: number[];
  correlation?: number[];
}

export interface ReturnDistribution {
  returns: number[];
  frequencies: number[];
  bins: number[];
  statistics: {
    mean: number;
    median: number;
    standardDeviation: number;
    skewness: number;
    kurtosis: number;
    var95: number;
    var99: number;
  };
}

export interface AllocationData {
  symbol: string;
  name: string;
  weight: number;
  value: number;
  sector?: string;
  assetClass?: string;
  color?: string;
}

export interface ComparisonData {
  portfolio: TimeSeriesDataPoint[];
  benchmark: TimeSeriesDataPoint[];
  riskFreeRate?: TimeSeriesDataPoint[];
  outperformance?: TimeSeriesDataPoint[];
}

export interface DrawdownData {
  dates: string[];
  drawdowns: number[];
  underwater: boolean[];
  peaks: number[];
  valleys: number[];
}

export interface PerformanceMetrics {
  totalReturn: number;
  annualizedReturn: number;
  volatility: number;
  sharpeRatio: number;
  sortinoRatio: number;
  maxDrawdown: number;
  calmarRatio: number;
  var95: number;
  var99: number;
  skewness: number;
  kurtosis: number;
  beta?: number;
  alpha?: number;
  informationRatio?: number;
  trackingError?: number;
}

export type ChartType = 'line' | 'bar' | 'pie' | 'doughnut' | 'scatter' | 'histogram';

export type TimeFrame = '1M' | '3M' | '6M' | '1Y' | '2Y' | '3Y' | '5Y' | 'MAX';

export interface ChartConfig {
  type: ChartType;
  responsive: boolean;
  maintainAspectRatio: boolean;
  height?: number;
  showLegend: boolean;
  showTooltip: boolean;
  showGrid: boolean;
  timeFrame?: TimeFrame;
}

export interface ChartTheme {
  primary: string;
  secondary: string;
  success: string;
  warning: string;
  error: string;
  background: string;
  surface: string;
  onSurface: string;
  grid: string;
}
