/**
 * Charts Component Index
 * Centralized export for all chart components
 */

// Core Advanced Chart Components
export { default as PerformanceTimeSeriesChart } from './PerformanceTimeSeriesChart';
export { default as RiskMetricsVisualization } from './RiskMetricsVisualization';
export { default as RollingMetricsChart } from './RollingMetricsCharts';
export { default as AssetAllocationChart } from './AssetAllocationChart';
export { default as PortfolioBenchmarkComparison } from './PortfolioBenchmarkComparison';
export { default as EnhancedReturnDistribution } from './EnhancedReturnDistribution';

// Re-export advanced chart types
export type {
  TimeSeriesDataPoint,
  ChartDataset,
  ChartMetrics,
  RollingMetrics,
  ReturnDistribution,
  AllocationData,
  ComparisonData,
  DrawdownData,
  PerformanceMetrics,
  ChartType,
  TimeFrame,
  ChartConfig,
  ChartTheme
} from '../../types/charts';
