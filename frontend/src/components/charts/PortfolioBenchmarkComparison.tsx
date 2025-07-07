/**
 * Portfolio vs Benchmark Comparison Chart
 * Comprehensive comparison charts for portfolio performance against benchmark
 */

import React, { useMemo, useState } from 'react';
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
  TimeScale,
  Filler
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import {
  Paper,
  Typography,
  Box,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  Alert,
  CircularProgress,
  useTheme,
  Card,
  CardContent,
  Tabs,
  Tab,
  Chip
} from '@mui/material';
import { ComparisonData, PerformanceMetrics, TimeFrame } from '../../types/charts';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  TimeScale,
  Filler
);

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

interface PortfolioBenchmarkComparisonProps {
  data: ComparisonData;
  portfolioMetrics: PerformanceMetrics;
  benchmarkMetrics: PerformanceMetrics;
  loading?: boolean;
  error?: string;
  title?: string;
  benchmarkName?: string;
  height?: number;
  onTimeFrameChange?: (timeFrame: TimeFrame) => void;
}

type ComparisonView = 'cumulative' | 'relative' | 'rolling' | 'metrics';

const PortfolioBenchmarkComparison: React.FC<PortfolioBenchmarkComparisonProps> = ({
  data,
  portfolioMetrics,
  benchmarkMetrics,
  loading = false,
  error,
  title = 'Portfolio vs Benchmark Analysis',
  benchmarkName = 'Benchmark',
  height = 500,
  onTimeFrameChange
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [timeFrame, setTimeFrame] = useState<TimeFrame>('1Y');
  const [normalizeToBase, setNormalizeToBase] = useState(true);

  // Calculate normalized cumulative returns (base 100)
  const normalizedData = useMemo(() => {
    if (!normalizeToBase || data.portfolio.length === 0) return data;

    const portfolioBase = data.portfolio[0]?.value || 1;
    const benchmarkBase = data.benchmark[0]?.value || 1;

    return {
      ...data,
      portfolio: data.portfolio.map(point => ({
        ...point,
        value: (point.value / portfolioBase) * 100
      })),
      benchmark: data.benchmark.map(point => ({
        ...point,
        value: (point.value / benchmarkBase) * 100
      }))
    };
  }, [data, normalizeToBase]);

  // Chart data for cumulative performance
  const cumulativeChartData = useMemo(() => ({
    datasets: [
      {
        label: 'Portfolio',
        data: normalizedData.portfolio.map(point => ({
          x: point.date,
          y: point.value
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
        label: benchmarkName,
        data: normalizedData.benchmark.map(point => ({
          x: point.date,
          y: point.value
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
  }), [normalizedData, theme, benchmarkName]);

  // Chart data for relative performance (outperformance)
  const relativeChartData = useMemo(() => {
    if (!data.outperformance || data.outperformance.length === 0) {
      return { datasets: [] };
    }

    return {
      datasets: [
        {
          label: 'Relative Performance',
          data: data.outperformance.map(point => ({
            x: point.date,
            y: point.value * 100
          })),
          borderColor: theme.palette.success.main,
          backgroundColor: data.outperformance.map(point => 
            point.value >= 0 ? `${theme.palette.success.main}40` : `${theme.palette.error.main}40`
          ),
          borderWidth: 2,
          fill: 'origin',
          tension: 0.1,
          pointRadius: 1,
          pointHoverRadius: 5
        }
      ]
    };
  }, [data.outperformance, theme]);

  // Metrics comparison data
  const metricsComparisonData = useMemo(() => {
    const metrics = [
      { name: 'Total Return', portfolio: portfolioMetrics.totalReturn * 100, benchmark: benchmarkMetrics.totalReturn * 100, unit: '%' },
      { name: 'Annual Return', portfolio: portfolioMetrics.annualizedReturn * 100, benchmark: benchmarkMetrics.annualizedReturn * 100, unit: '%' },
      { name: 'Volatility', portfolio: portfolioMetrics.volatility * 100, benchmark: benchmarkMetrics.volatility * 100, unit: '%' },
      { name: 'Sharpe Ratio', portfolio: portfolioMetrics.sharpeRatio, benchmark: benchmarkMetrics.sharpeRatio, unit: '' },
      { name: 'Max Drawdown', portfolio: Math.abs(portfolioMetrics.maxDrawdown * 100), benchmark: Math.abs(benchmarkMetrics.maxDrawdown * 100), unit: '%' },
      { name: 'VaR (95%)', portfolio: Math.abs(portfolioMetrics.var95 * 100), benchmark: Math.abs(benchmarkMetrics.var95 * 100), unit: '%' }
    ];

    return {
      labels: metrics.map(m => m.name),
      datasets: [
        {
          label: 'Portfolio',
          data: metrics.map(m => m.portfolio),
          backgroundColor: theme.palette.primary.main,
          borderColor: theme.palette.primary.main,
          borderWidth: 1
        },
        {
          label: benchmarkName,
          data: metrics.map(m => m.benchmark),
          backgroundColor: theme.palette.secondary.main,
          borderColor: theme.palette.secondary.main,
          borderWidth: 1
        }
      ]
    };
  }, [portfolioMetrics, benchmarkMetrics, theme, benchmarkName]);

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
            if (tabValue === 1) { // Relative performance
              return `${label}: ${value.toFixed(2)}%`;
            }
            return normalizeToBase ? 
              `${label}: ${value.toFixed(2)}` : 
              `${label}: ${(value * 100).toFixed(2)}%`;
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
          text: tabValue === 1 ? 'Relative Performance (%)' : 
                normalizeToBase ? 'Normalized Value (Base 100)' : 'Cumulative Return (%)'
        },
        ticks: {
          callback: function(value) {
            if (tabValue === 1) {
              return `${Number(value).toFixed(1)}%`;
            }
            return normalizeToBase ? 
              Number(value).toFixed(0) : 
              `${Number(value).toFixed(1)}%`;
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    }
  }), [tabValue, normalizeToBase]);

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
            const value = context.parsed.y;
            const metric = context.label;
            const unit = metric === 'Sharpe Ratio' ? '' : '%';
            return `${context.dataset.label}: ${value.toFixed(2)}${unit}`;
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

  const getOutperformanceColor = () => {
    const totalOutperformance = (portfolioMetrics.totalReturn - benchmarkMetrics.totalReturn) * 100;
    return totalOutperformance >= 0 ? 'success' : 'error';
  };

  const getOutperformanceText = () => {
    const totalOutperformance = (portfolioMetrics.totalReturn - benchmarkMetrics.totalReturn) * 100;
    return totalOutperformance >= 0 ? 'Outperforming' : 'Underperforming';
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
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <Typography variant="h6">{title}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
              <Chip
                label={getOutperformanceText()}
                color={getOutperformanceColor() as any}
                size="small"
              />
              <Typography variant="body2" color="text.secondary">
                Outperformance: {((portfolioMetrics.totalReturn - benchmarkMetrics.totalReturn) * 100).toFixed(2)}%
              </Typography>
            </Box>
          </Grid>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={timeFrame}
                label="Period"
                onChange={(e) => {
                  const newTimeFrame = e.target.value as TimeFrame;
                  setTimeFrame(newTimeFrame);
                  onTimeFrameChange?.(newTimeFrame);
                }}
              >
                <MenuItem value="1M">1 Month</MenuItem>
                <MenuItem value="3M">3 Months</MenuItem>
                <MenuItem value="6M">6 Months</MenuItem>
                <MenuItem value="1Y">1 Year</MenuItem>
                <MenuItem value="2Y">2 Years</MenuItem>
                <MenuItem value="3Y">3 Years</MenuItem>
                <MenuItem value="MAX">All Time</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Box>

      {/* Performance Summary Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Portfolio Return
              </Typography>
              <Typography variant="h6" color="primary">
                {(portfolioMetrics.totalReturn * 100).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                {benchmarkName} Return
              </Typography>
              <Typography variant="h6" color="secondary">
                {(benchmarkMetrics.totalReturn * 100).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Information Ratio
              </Typography>
              <Typography variant="h6">
                {portfolioMetrics.informationRatio?.toFixed(3) || 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Tracking Error
              </Typography>
              <Typography variant="h6">
                {portfolioMetrics.trackingError ? 
                  `${(portfolioMetrics.trackingError * 100).toFixed(2)}%` : 'N/A'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Cumulative Performance" />
          <Tab label="Relative Performance" />
          <Tab label="Metrics Comparison" />
        </Tabs>
      </Box>

      {/* Cumulative Performance */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ mb: 2 }}>
          <ToggleButtonGroup
            value={normalizeToBase}
            exclusive
            onChange={(_, value) => value !== null && setNormalizeToBase(value)}
            size="small"
          >
            <ToggleButton value={true}>Normalized (Base 100)</ToggleButton>
            <ToggleButton value={false}>Cumulative Returns</ToggleButton>
          </ToggleButtonGroup>
        </Box>
        <Box sx={{ height: height - 250 }}>
          <Line data={cumulativeChartData} options={lineChartOptions} />
        </Box>
      </TabPanel>

      {/* Relative Performance */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ height: height - 200 }}>
          <Line data={relativeChartData} options={lineChartOptions} />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Positive values indicate portfolio outperformance vs {benchmarkName}
        </Typography>
      </TabPanel>

      {/* Metrics Comparison */}
      <TabPanel value={tabValue} index={2}>
        <Box sx={{ height: height - 200 }}>
          <Bar data={metricsComparisonData} options={barChartOptions} />
        </Box>
      </TabPanel>
    </Paper>
  );
};

export default PortfolioBenchmarkComparison;
