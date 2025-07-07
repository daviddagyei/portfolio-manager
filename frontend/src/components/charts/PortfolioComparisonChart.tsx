/**
 * Portfolio Comparison Chart
 * Side-by-side comparison of portfolio vs benchmark performance
 */

import React, { useMemo } from 'react';
import { Line, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import {
  Paper,
  Typography,
  Box,
  Grid,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Card,
  CardContent,
  Divider,
  Chip,
  useTheme
} from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface PerformanceDataPoint {
  date: string;
  portfolio: number;
  benchmark: number;
}

interface ComparisonMetrics {
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

interface PortfolioComparisonData {
  performanceData: PerformanceDataPoint[];
  metrics: ComparisonMetrics;
  benchmarkName: string;
  portfolioName: string;
}

interface PortfolioComparisonChartProps {
  data: PortfolioComparisonData;
  loading?: boolean;
  error?: string;
  height?: number;
  chartType?: 'performance' | 'metrics' | 'scatter' | 'returns';
  onChartTypeChange?: (type: string) => void;
}

const PortfolioComparisonChart: React.FC<PortfolioComparisonChartProps> = ({
  data,
  loading = false,
  error,
  height = 400,
  chartType = 'performance',
  onChartTypeChange
}) => {
  const theme = useTheme();

  const performanceChartData = useMemo(() => {
    if (!data?.performanceData || data.performanceData.length === 0) {
      return { datasets: [] };
    }

    return {
      datasets: [
        {
          label: data.portfolioName || 'Portfolio',
          data: data.performanceData.map(point => ({
            x: point.date,
            y: point.portfolio
          })),
          borderColor: theme.palette.primary.main,
          backgroundColor: `${theme.palette.primary.main}20`,
          borderWidth: 2,
          fill: false,
          tension: 0.1,
          pointRadius: 1,
          pointHoverRadius: 5
        },
        {
          label: data.benchmarkName || 'Benchmark',
          data: data.performanceData.map(point => ({
            x: point.date,
            y: point.benchmark
          })),
          borderColor: theme.palette.secondary.main,
          backgroundColor: `${theme.palette.secondary.main}20`,
          borderWidth: 2,
          fill: false,
          tension: 0.1,
          pointRadius: 1,
          pointHoverRadius: 5,
          borderDash: [5, 5]
        }
      ]
    };
  }, [data, theme]);

  const metricsComparisonData = useMemo(() => {
    if (!data?.metrics) return { labels: [], datasets: [] };

    const metrics = data.metrics;
    const labels = ['Total Return', 'Volatility', 'Sharpe Ratio', 'Max Drawdown'];
    
    return {
      labels,
      datasets: [
        {
          label: data.portfolioName || 'Portfolio',
          data: [
            metrics.totalReturn.portfolio * 100,
            metrics.volatility.portfolio * 100,
            metrics.sharpeRatio.portfolio,
            Math.abs(metrics.maxDrawdown.portfolio) * 100
          ],
          backgroundColor: theme.palette.primary.main,
          borderColor: theme.palette.primary.main,
          borderWidth: 1
        },
        {
          label: data.benchmarkName || 'Benchmark',
          data: [
            metrics.totalReturn.benchmark * 100,
            metrics.volatility.benchmark * 100,
            metrics.sharpeRatio.benchmark,
            Math.abs(metrics.maxDrawdown.benchmark) * 100
          ],
          backgroundColor: theme.palette.secondary.main,
          borderColor: theme.palette.secondary.main,
          borderWidth: 1
        }
      ]
    };
  }, [data, theme]);

  const excessReturnsData = useMemo(() => {
    if (!data?.performanceData || data.performanceData.length === 0) {
      return { datasets: [] };
    }

    const excessReturns = data.performanceData.map(point => ({
      x: point.date,
      y: (point.portfolio - point.benchmark) * 100
    }));

    return {
      datasets: [{
        label: 'Excess Returns',
        data: excessReturns,
        borderColor: theme.palette.success.main,
        backgroundColor: excessReturns.map(point => 
          point.y >= 0 ? `${theme.palette.success.main}40` : `${theme.palette.error.main}40`
        ),
        borderWidth: 2,
        fill: 'origin',
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 4
      }]
    };
  }, [data, theme]);

  const lineChartOptions: ChartOptions<'line'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20
        }
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            if (chartType === 'returns') {
              return `${label}: ${value.toFixed(2)}%`;
            }
            return `${label}: ${(value * 100).toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      x: {
        type: 'time',
        time: {
          displayFormats: {
            day: 'MMM dd',
            month: 'MMM yyyy',
            year: 'yyyy'
          }
        },
        title: {
          display: true,
          text: 'Date'
        }
      },
      y: {
        title: {
          display: true,
          text: chartType === 'returns' ? 'Excess Returns (%)' : 'Cumulative Returns (%)'
        },
        ticks: {
          callback: function(value) {
            return `${Number(value).toFixed(1)}%`;
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  }), [chartType]);

  const barChartOptions: ChartOptions<'bar'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            const metricIndex = context.dataIndex;
            
            if (metricIndex === 2) { // Sharpe Ratio
              return `${label}: ${value.toFixed(3)}`;
            }
            return `${label}: ${value.toFixed(2)}%`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Metrics'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value'
        }
      }
    }
  }), []);

  const renderChart = () => {
    switch (chartType) {
      case 'performance':
        return <Line data={performanceChartData} options={lineChartOptions} />;
      case 'metrics':
        return <Bar data={metricsComparisonData} options={barChartOptions} />;
      case 'returns':
        return <Line data={excessReturnsData} options={lineChartOptions} />;
      default:
        return <Line data={performanceChartData} options={lineChartOptions} />;
    }
  };

  const getMetricColor = (portfolioValue: number, benchmarkValue: number, higherIsBetter: boolean = true) => {
    const isPortfolioBetter = higherIsBetter ? 
      portfolioValue > benchmarkValue : 
      portfolioValue < benchmarkValue;
    return isPortfolioBetter ? 'success' : 'error';
  };

  if (loading) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Box display="flex" justifyContent="center" alignItems="center" height="100%">
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={8}>
          <Typography variant="h6">
            Portfolio vs Benchmark Comparison
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {data.portfolioName} vs {data.benchmarkName}
          </Typography>
        </Grid>
        <Grid item xs={12} md={4}>
          {onChartTypeChange && (
            <FormControl fullWidth size="small">
              <InputLabel>Chart Type</InputLabel>
              <Select
                value={chartType}
                label="Chart Type"
                onChange={(e) => onChartTypeChange(e.target.value)}
              >
                <MenuItem value="performance">Performance</MenuItem>
                <MenuItem value="metrics">Metrics Comparison</MenuItem>
                <MenuItem value="returns">Excess Returns</MenuItem>
              </Select>
            </FormControl>
          )}
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Box sx={{ height: height - 120 }}>
            {renderChart()}
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metrics
              </Typography>
              
              {data.metrics && (
                <>
                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Beta</Typography>
                    <Chip
                      label={data.metrics.beta.toFixed(3)}
                      color={getMetricColor(data.metrics.beta, 1, false)}
                      size="small"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Alpha (annualized)</Typography>
                    <Chip
                      label={`${(data.metrics.alpha * 100).toFixed(2)}%`}
                      color={data.metrics.alpha > 0 ? 'success' : 'error'}
                      size="small"
                      sx={{ mt: 0.5 }}
                    />
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Correlation</Typography>
                    <Typography variant="body1">{data.metrics.correlation.toFixed(3)}</Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Information Ratio</Typography>
                    <Typography variant="body1">{data.metrics.informationRatio.toFixed(3)}</Typography>
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Tracking Error</Typography>
                    <Typography variant="body1">{(data.metrics.trackingError * 100).toFixed(2)}%</Typography>
                  </Box>

                  <Divider sx={{ my: 2 }} />

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Up Capture</Typography>
                    <Chip
                      label={`${(data.metrics.upCapture * 100).toFixed(1)}%`}
                      color={data.metrics.upCapture > 1 ? 'success' : 'warning'}
                      size="small"
                    />
                  </Box>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">Down Capture</Typography>
                    <Chip
                      label={`${(data.metrics.downCapture * 100).toFixed(1)}%`}
                      color={data.metrics.downCapture < 1 ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default PortfolioComparisonChart;
