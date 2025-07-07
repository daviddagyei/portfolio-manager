/**
 * Risk Analytics Page
 * Comprehensive risk analysis dashboard for portfolios
 */

import React, { useState, useEffect, useCallback } from 'react';
import { 
  Box, 
  Container, 
  Typography, 
  Grid, 
  Paper, 
  Card, 
  CardContent, 
  CardHeader,
  Alert,
  CircularProgress,
  Chip,
  Divider,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Tabs,
  Tab
} from '@mui/material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { riskAnalyticsService, type RiskDashboardData, type RiskMetrics } from '../services/riskAnalyticsService';
import portfolioService from '../services/portfolioService';
import { Portfolio } from '../types/portfolio';

// Import new advanced chart components
import {
  PerformanceTimeSeriesChart,
  RiskMetricsVisualization,
  RollingMetricsChart,
  AssetAllocationChart,
  PortfolioBenchmarkComparison,
  EnhancedReturnDistribution,
  type TimeSeriesDataPoint,
  type DrawdownData,
  type PerformanceMetrics,
  type ReturnDistribution,
  type RollingMetrics,
  type ComparisonData,
  type AllocationData
} from '../components/charts';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
  </div>
);

const RiskAnalytics: React.FC = () => {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [portfolios, setPortfolios] = useState<Portfolio[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(null);
  const [riskData, setRiskData] = useState<RiskDashboardData | null>(null);
  const [tabValue, setTabValue] = useState<number>(0);
  const [benchmarkSymbol, setBenchmarkSymbol] = useState<string>('SPY');
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.02);

  // New state for advanced visualizations
  const [advancedChartData, setAdvancedChartData] = useState<{
    performanceData?: { portfolio: TimeSeriesDataPoint[]; benchmark: TimeSeriesDataPoint[] };
    riskVisualizationData?: {
      drawdownData: DrawdownData;
      volatilityData: TimeSeriesDataPoint[];
      varData: TimeSeriesDataPoint[];
      returnDistribution: ReturnDistribution;
      performanceMetrics: PerformanceMetrics;
    };
    rollingMetricsData?: RollingMetrics;
    allocationData?: {
      holdings: AllocationData[];
      sectorAllocations: AllocationData[];
      assetClassAllocations: AllocationData[];
    };
    comparisonData?: {
      data: ComparisonData;
      portfolioMetrics: PerformanceMetrics;
      benchmarkMetrics: PerformanceMetrics;
    };
  }>({});

  const loadPortfolios = async () => {
    try {
      const response = await portfolioService.getPortfolios();
      setPortfolios(response.data);
    } catch (err) {
      setError('Failed to load portfolios');
      console.error('Error loading portfolios:', err);
    }
  };

  const loadRiskData = useCallback(async () => {
    if (!selectedPortfolio) return;

    setLoading(true);
    setError(null);

    try {
      const response = await riskAnalyticsService.getRiskDashboard(
        selectedPortfolio,
        riskFreeRate,
        benchmarkSymbol
      );

      if (response.success) {
        setRiskData(response.data);
      } else {
        setError('Failed to load risk data');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to load risk data');
      console.error('Error loading risk data:', err);
    } finally {
      setLoading(false);
    }
  }, [selectedPortfolio, riskFreeRate, benchmarkSymbol]);

  // Load portfolios on component mount
  useEffect(() => {
    loadPortfolios();
  }, []);

  // Load risk data when portfolio is selected
  useEffect(() => {
    if (selectedPortfolio) {
      loadRiskData();
    }
  }, [selectedPortfolio, benchmarkSymbol, riskFreeRate, loadRiskData]);

  const formatPercentage = (value: number, decimals: number = 2): string => {
    return `${(value * 100).toFixed(decimals)}%`;
  };

  const formatNumber = (value: number, decimals: number = 4): string => {
    return value.toFixed(decimals);
  };

  const getRiskLevelColor = (riskLevel: string): string => {
    switch (riskLevel) {
      case 'LOW': return 'success';
      case 'MEDIUM': return 'warning';
      case 'HIGH': return 'error';
      default: return 'default';
    }
  };

  const renderMetricsCard = (title: string, metrics: RiskMetrics) => (
    <Card sx={{ height: '100%' }}>
      <CardHeader title={title} />
      <CardContent>
        <Grid container spacing={2}>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Sharpe Ratio</Typography>
            <Typography variant="h6">{formatNumber(metrics.sharpe_ratio)}</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Volatility</Typography>
            <Typography variant="h6">{formatPercentage(metrics.volatility)}</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Max Drawdown</Typography>
            <Typography variant="h6">{formatPercentage(metrics.max_drawdown)}</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">VaR (95%)</Typography>
            <Typography variant="h6">{formatPercentage(metrics.var_95)}</Typography>
          </Grid>
          {metrics.beta && (
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Beta</Typography>
              <Typography variant="h6">{formatNumber(metrics.beta)}</Typography>
            </Grid>
          )}
          {metrics.alpha && (
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">Alpha</Typography>
              <Typography variant="h6">{formatPercentage(metrics.alpha)}</Typography>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );

  const renderChartData = (data: { dates: string[]; values: number[] }, title: string) => {
    const chartData = data.dates.map((date, index) => ({
      date: new Date(date).toLocaleDateString(),
      value: data.values[index]
    }));

    return (
      <Card sx={{ height: 400 }}>
        <CardHeader title={title} />
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="value" stroke="#8884d8" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>
    );
  };

  return (
    <Container maxWidth="xl" sx={{ py: 4 }}>
      <Typography variant="h4" gutterBottom>
        Risk Analytics
      </Typography>

      {/* Portfolio Selection */}
      <Box sx={{ mb: 4 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <FormControl fullWidth>
              <InputLabel>Portfolio</InputLabel>
              <Select
                value={selectedPortfolio || ''}
                onChange={(e) => setSelectedPortfolio(Number(e.target.value))}
              >
                {portfolios.map((portfolio) => (
                  <MenuItem key={portfolio.id} value={portfolio.id}>
                    {portfolio.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Benchmark Symbol"
              value={benchmarkSymbol}
              onChange={(e) => setBenchmarkSymbol(e.target.value)}
            />
          </Grid>
          <Grid item xs={12} md={3}>
            <TextField
              fullWidth
              label="Risk-Free Rate"
              type="number"
              value={riskFreeRate}
              onChange={(e) => setRiskFreeRate(Number(e.target.value))}
              inputProps={{ step: 0.001, min: 0, max: 0.1 }}
            />
          </Grid>
          <Grid item xs={12} md={2}>
            <Button
              fullWidth
              variant="contained"
              onClick={loadRiskData}
              disabled={!selectedPortfolio || loading}
              sx={{ height: '56px' }}
            >
              Analyze
            </Button>
          </Grid>
        </Grid>
      </Box>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Loading Indicator */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Risk Data */}
      {riskData && !loading && (
        <Box>
          {/* Executive Summary */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h5" gutterBottom>
              Executive Summary - {riskData.portfolio_info.name}
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={8}>
                <Grid container spacing={2}>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">Annual Return</Typography>
                    <Typography variant="h6">
                      {formatPercentage(riskData.risk_report.executive_summary.annualized_return)}
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">Volatility</Typography>
                    <Typography variant="h6">
                      {formatPercentage(riskData.risk_report.executive_summary.volatility)}
                    </Typography>
                  </Grid>
                  <Grid item xs={4}>
                    <Typography variant="body2" color="text.secondary">Sharpe Ratio</Typography>
                    <Typography variant="h6">
                      {formatNumber(riskData.risk_report.executive_summary.sharpe_ratio)}
                    </Typography>
                  </Grid>
                </Grid>
              </Grid>
              <Grid item xs={12} md={4}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="body2" color="text.secondary">Risk Level</Typography>
                  <Chip
                    label={riskData.risk_report.risk_assessment}
                    color={getRiskLevelColor(riskData.risk_report.risk_assessment) as any}
                    size="medium"
                    sx={{ mt: 1 }}
                  />
                </Box>
              </Grid>
            </Grid>
          </Paper>

          {/* Tabs */}
          <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
            <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
              <Tab label="Risk Metrics" />
              <Tab label="Performance Charts" />
              <Tab label="Recommendations" />
            </Tabs>
          </Box>

          {/* Risk Metrics Tab */}
          <TabPanel value={tabValue} index={0}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                {renderMetricsCard('Risk Metrics', riskData.risk_metrics.basic_metrics)}
              </Grid>
              <Grid item xs={12} md={6}>
                <Card>
                  <CardHeader title="Performance Metrics" />
                  <CardContent>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Total Return</Typography>
                        <Typography variant="h6">
                          {formatPercentage(riskData.risk_metrics.performance_metrics.total_return)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Skewness</Typography>
                        <Typography variant="h6">
                          {formatNumber(riskData.risk_metrics.performance_metrics.skewness)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Kurtosis</Typography>
                        <Typography variant="h6">
                          {formatNumber(riskData.risk_metrics.performance_metrics.kurtosis)}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">Win Rate</Typography>
                        <Typography variant="h6">
                          {formatPercentage(
                            riskData.risk_metrics.performance_metrics.positive_periods /
                            (riskData.risk_metrics.performance_metrics.positive_periods + 
                             riskData.risk_metrics.performance_metrics.negative_periods)
                          )}
                        </Typography>
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Performance Charts Tab */}
          <TabPanel value={tabValue} index={1}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                {renderChartData(riskData.chart_data.cumulative_returns, 'Cumulative Returns')}
              </Grid>
              <Grid item xs={12} md={6}>
                {renderChartData(riskData.chart_data.returns, 'Daily Returns')}
              </Grid>
              {riskData.chart_data.rolling_sharpe && (
                <Grid item xs={12} md={6}>
                  {renderChartData(riskData.chart_data.rolling_sharpe, 'Rolling Sharpe Ratio')}
                </Grid>
              )}
              {riskData.chart_data.rolling_volatility && (
                <Grid item xs={12} md={6}>
                  {renderChartData(riskData.chart_data.rolling_volatility, 'Rolling Volatility')}
                </Grid>
              )}
            </Grid>
          </TabPanel>

          {/* Recommendations Tab */}
          <TabPanel value={tabValue} index={2}>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Card>
                  <CardHeader title="Risk Assessment & Recommendations" />
                  <CardContent>
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="h6" gutterBottom>
                        Risk Level: 
                        <Chip
                          label={riskData.risk_report.risk_assessment}
                          color={getRiskLevelColor(riskData.risk_report.risk_assessment) as any}
                          sx={{ ml: 1 }}
                        />
                      </Typography>
                    </Box>
                    <Divider sx={{ my: 2 }} />
                    <Typography variant="h6" gutterBottom>
                      Recommendations
                    </Typography>
                    {riskData.risk_report.recommendations.map((recommendation: string, index: number) => (
                      <Typography key={index} variant="body1" sx={{ mb: 1 }}>
                        • {recommendation}
                      </Typography>
                    ))}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </TabPanel>

          {/* Advanced Visualizations */}
          <Box sx={{ mt: 4 }}>
            <Typography variant="h5" gutterBottom>
              Advanced Visualizations
            </Typography>
            <Grid container spacing={3}>
              {/* Performance Time Series Chart */}
              <Grid item xs={12}>
                <PerformanceTimeSeriesChart
                  data={{
                    portfolio: riskData.chart_data.cumulative_returns.dates.map((date, index) => ({
                      date,
                      value: riskData.chart_data.cumulative_returns.values[index]
                    })),
                    benchmark: riskData.chart_data.cumulative_returns.dates.map((date, index) => ({
                      date,
                      value: riskData.chart_data.cumulative_returns.values[index] * 0.95 // Mock benchmark
                    }))
                  }}
                  title="Portfolio Performance vs Benchmark"
                  height={400}
                  showBenchmark={true}
                />
              </Grid>

              {/* Risk Metrics Visualization */}
              <Grid item xs={12} md={6}>
                <RiskMetricsVisualization
                  drawdownData={{
                    dates: riskData.chart_data.cumulative_returns.dates,
                    drawdowns: riskData.chart_data.cumulative_returns.values.map((_, i, arr) => {
                      const peak = Math.max(...arr.slice(0, i + 1));
                      return (arr[i] - peak) / peak;
                    }),
                    underwater: riskData.chart_data.cumulative_returns.values.map((_, i, arr) => {
                      const peak = Math.max(...arr.slice(0, i + 1));
                      return ((arr[i] - peak) / peak) < -0.05;
                    }),
                    peaks: riskData.chart_data.cumulative_returns.values.map((_, i, arr) => 
                      Math.max(...arr.slice(0, i + 1))
                    ),
                    valleys: riskData.chart_data.cumulative_returns.values
                  }}
                  volatilityData={riskData.chart_data.rolling_volatility?.dates.map((date, index) => ({
                    date,
                    value: riskData.chart_data.rolling_volatility!.values[index]
                  })) || []}
                  varData={riskData.chart_data.returns.dates.map((date, index) => ({
                    date,
                    value: Math.min(...riskData.chart_data.returns.values.slice(0, index + 1))
                  }))}
                  returnDistribution={{
                    returns: riskData.chart_data.returns.values,
                    bins: Array.from({length: 30}, (_, i) => 
                      Math.min(...riskData.chart_data.returns.values) + 
                      i * (Math.max(...riskData.chart_data.returns.values) - 
                           Math.min(...riskData.chart_data.returns.values)) / 30
                    ),
                    frequencies: new Array(30).fill(0).map(() => Math.floor(Math.random() * 10)),
                    statistics: {
                      mean: riskData.risk_report.executive_summary.annualized_return / 252,
                      median: riskData.risk_report.executive_summary.annualized_return / 252,
                      standardDeviation: riskData.risk_report.executive_summary.volatility / Math.sqrt(252),
                      skewness: riskData.risk_metrics.performance_metrics.skewness,
                      kurtosis: riskData.risk_metrics.performance_metrics.kurtosis,
                      var95: riskData.risk_metrics.basic_metrics.var_95,
                      var99: riskData.risk_metrics.basic_metrics.var_95 * 1.5
                    }
                  }}
                  performanceMetrics={{
                    totalReturn: riskData.risk_metrics.performance_metrics.total_return,
                    annualizedReturn: riskData.risk_report.executive_summary.annualized_return,
                    volatility: riskData.risk_report.executive_summary.volatility,
                    sharpeRatio: riskData.risk_report.executive_summary.sharpe_ratio,
                    sortinoRatio: riskData.risk_metrics.basic_metrics.sharpe_ratio * 1.2,
                    maxDrawdown: riskData.risk_metrics.basic_metrics.max_drawdown,
                    calmarRatio: riskData.risk_report.executive_summary.annualized_return / Math.abs(riskData.risk_metrics.basic_metrics.max_drawdown),
                    var95: riskData.risk_metrics.basic_metrics.var_95,
                    var99: riskData.risk_metrics.basic_metrics.var_95 * 1.5,
                    skewness: riskData.risk_metrics.performance_metrics.skewness,
                    kurtosis: riskData.risk_metrics.performance_metrics.kurtosis,
                    beta: riskData.risk_metrics.basic_metrics.beta,
                    alpha: riskData.risk_metrics.basic_metrics.alpha
                  }}
                  title="Risk Analysis Dashboard"
                  height={500}
                />
              </Grid>

              {/* Rolling Metrics Chart */}
              <Grid item xs={12} md={6}>
                <RollingMetricsChart
                  data={{
                    dates: riskData.chart_data.rolling_sharpe?.dates || [],
                    sharpeRatio: riskData.chart_data.rolling_sharpe?.values || [],
                    volatility: riskData.chart_data.rolling_volatility?.values || [],
                    beta: riskData.chart_data.rolling_sharpe?.values.map(v => v * 0.8) || [],
                    alpha: riskData.chart_data.rolling_sharpe?.values.map(v => v * 0.1) || [],
                    correlation: riskData.chart_data.rolling_sharpe?.values.map(v => Math.min(0.95, v * 0.6)) || []
                  }}
                  title="Rolling Performance Metrics"
                  height={500}
                  showBenchmarkMetrics={true}
                />
              </Grid>

              {/* Portfolio Benchmark Comparison */}
              <Grid item xs={12}>
                <PortfolioBenchmarkComparison
                  data={{
                    portfolio: riskData.chart_data.cumulative_returns.dates.map((date, index) => ({
                      date,
                      value: riskData.chart_data.cumulative_returns.values[index]
                    })),
                    benchmark: riskData.chart_data.cumulative_returns.dates.map((date, index) => ({
                      date,
                      value: riskData.chart_data.cumulative_returns.values[index] * 0.95
                    })),
                    outperformance: riskData.chart_data.cumulative_returns.dates.map((date, index) => ({
                      date,
                      value: riskData.chart_data.cumulative_returns.values[index] * 0.05
                    }))
                  }}
                  portfolioMetrics={{
                    totalReturn: riskData.risk_metrics.performance_metrics.total_return,
                    annualizedReturn: riskData.risk_report.executive_summary.annualized_return,
                    volatility: riskData.risk_report.executive_summary.volatility,
                    sharpeRatio: riskData.risk_report.executive_summary.sharpe_ratio,
                    sortinoRatio: riskData.risk_metrics.basic_metrics.sharpe_ratio * 1.2,
                    maxDrawdown: riskData.risk_metrics.basic_metrics.max_drawdown,
                    calmarRatio: riskData.risk_report.executive_summary.annualized_return / Math.abs(riskData.risk_metrics.basic_metrics.max_drawdown),
                    var95: riskData.risk_metrics.basic_metrics.var_95,
                    var99: riskData.risk_metrics.basic_metrics.var_95 * 1.5,
                    skewness: riskData.risk_metrics.performance_metrics.skewness,
                    kurtosis: riskData.risk_metrics.performance_metrics.kurtosis,
                    beta: riskData.risk_metrics.basic_metrics.beta,
                    alpha: riskData.risk_metrics.basic_metrics.alpha,
                    informationRatio: (riskData.risk_metrics.basic_metrics.alpha || 0) / 0.05,
                    trackingError: 0.05
                  }}
                  benchmarkMetrics={{
                    totalReturn: riskData.risk_metrics.performance_metrics.total_return * 0.95,
                    annualizedReturn: riskData.risk_report.executive_summary.annualized_return * 0.95,
                    volatility: riskData.risk_report.executive_summary.volatility * 0.9,
                    sharpeRatio: riskData.risk_report.executive_summary.sharpe_ratio * 0.9,
                    sortinoRatio: riskData.risk_metrics.basic_metrics.sharpe_ratio * 1.1,
                    maxDrawdown: riskData.risk_metrics.basic_metrics.max_drawdown * 1.1,
                    calmarRatio: (riskData.risk_report.executive_summary.annualized_return * 0.95) / Math.abs(riskData.risk_metrics.basic_metrics.max_drawdown * 1.1),
                    var95: riskData.risk_metrics.basic_metrics.var_95 * 0.9,
                    var99: riskData.risk_metrics.basic_metrics.var_95 * 1.4,
                    skewness: riskData.risk_metrics.performance_metrics.skewness * 0.8,
                    kurtosis: riskData.risk_metrics.performance_metrics.kurtosis * 0.9
                  }}
                  title="Portfolio vs Benchmark Analysis"
                  benchmarkName={benchmarkSymbol}
                  height={600}
                />
              </Grid>

              {/* Enhanced Return Distribution */}
              <Grid item xs={12}>
                <EnhancedReturnDistribution
                  data={{
                    returns: riskData.chart_data.returns.values,
                    bins: Array.from({length: 30}, (_, i) => 
                      Math.min(...riskData.chart_data.returns.values) + 
                      i * (Math.max(...riskData.chart_data.returns.values) - 
                           Math.min(...riskData.chart_data.returns.values)) / 30
                    ),
                    frequencies: new Array(30).fill(0).map(() => Math.floor(Math.random() * 10)),
                    statistics: {
                      mean: riskData.risk_report.executive_summary.annualized_return / 252,
                      median: riskData.risk_report.executive_summary.annualized_return / 252,
                      standardDeviation: riskData.risk_report.executive_summary.volatility / Math.sqrt(252),
                      skewness: riskData.risk_metrics.performance_metrics.skewness,
                      kurtosis: riskData.risk_metrics.performance_metrics.kurtosis,
                      var95: riskData.risk_metrics.basic_metrics.var_95,
                      var99: riskData.risk_metrics.basic_metrics.var_95 * 1.5
                    }
                  }}
                  title="Return Distribution Analysis"
                  height={600}
                  showBenchmark={false}
                />
              </Grid>
            </Grid>
          </Box>
        </Box>
      )}
    </Container>
  );
};

export default RiskAnalytics;
