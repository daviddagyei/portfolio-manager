/**
 * Risk Metrics Visualization Component
 * Comprehensive risk analysis with drawdown charts, volatility plots, and VaR visualization
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
  Filler,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  useTheme,
  Chip
} from '@mui/material';
import {
  DrawdownData,
  TimeSeriesDataPoint,
  PerformanceMetrics,
  ReturnDistribution
} from '../../types/charts';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
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

interface RiskMetricsVisualizationProps {
  drawdownData: DrawdownData;
  volatilityData: TimeSeriesDataPoint[];
  varData: TimeSeriesDataPoint[];
  returnDistribution: ReturnDistribution;
  performanceMetrics: PerformanceMetrics;
  loading?: boolean;
  error?: string;
  title?: string;
  height?: number;
}

const RiskMetricsVisualization: React.FC<RiskMetricsVisualizationProps> = ({
  drawdownData,
  volatilityData,
  varData,
  returnDistribution,
  performanceMetrics,
  loading = false,
  error,
  title = 'Risk Analytics',
  height = 400
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [timeframe, setTimeframe] = useState('1Y');

  const drawdownChartData = useMemo(() => ({
    datasets: [
      {
        label: 'Drawdown',
        data: drawdownData.dates.map((date, index) => ({
          x: date,
          y: drawdownData.drawdowns[index] * 100
        })),
        borderColor: theme.palette.error.main,
        backgroundColor: `${theme.palette.error.main}20`,
        fill: 'origin',
        tension: 0.1,
        pointRadius: 1
      },
      {
        label: 'Underwater Periods',
        data: drawdownData.dates
          .map((date, index) => ({
            x: date,
            y: drawdownData.underwater[index] ? -0.5 : null
          }))
          .filter(point => point.y !== null),
        borderColor: theme.palette.warning.main,
        backgroundColor: theme.palette.warning.main,
        pointRadius: 2,
        showLine: false
      }
    ]
  }), [drawdownData, theme]);

  const volatilityChartData = useMemo(() => ({
    datasets: [
      {
        label: 'Rolling Volatility (30d)',
        data: volatilityData.map(point => ({
          x: point.date,
          y: point.value * 100
        })),
        borderColor: theme.palette.secondary.main,
        backgroundColor: `${theme.palette.secondary.main}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 1
      }
    ]
  }), [volatilityData, theme]);

  const varChartData = useMemo(() => ({
    datasets: [
      {
        label: 'Value at Risk (95%)',
        data: varData.map(point => ({
          x: point.date,
          y: point.value * 100
        })),
        borderColor: theme.palette.warning.main,
        backgroundColor: `${theme.palette.warning.main}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 1
      }
    ]
  }), [varData, theme]);

  const histogramData = useMemo(() => ({
    labels: returnDistribution.bins.map(bin => `${(bin * 100).toFixed(1)}%`),
    datasets: [
      {
        label: 'Return Frequency',
        data: returnDistribution.frequencies,
        backgroundColor: `${theme.palette.primary.main}80`,
        borderColor: theme.palette.primary.main,
        borderWidth: 1
      }
    ]
  }), [returnDistribution, theme]);

  const chartOptions: ChartOptions<'line'> = useMemo(() => ({
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
            return `${label}: ${value.toFixed(2)}%`;
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
        }
      },
      y: {
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
  }), []);

  const barChartOptions: ChartOptions<'bar'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            return `Frequency: ${context.parsed.y}`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Daily Returns (%)'
        }
      },
      y: {
        title: {
          display: true,
          text: 'Frequency'
        }
      }
    }
  }), []);

  const getRiskLevel = (sharpe: number): { level: string; color: 'success' | 'warning' | 'error' } => {
    if (sharpe > 1.5) return { level: 'LOW', color: 'success' };
    if (sharpe > 0.5) return { level: 'MEDIUM', color: 'warning' };
    return { level: 'HIGH', color: 'error' };
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

  const riskLevel = getRiskLevel(performanceMetrics.sharpeRatio);

  return (
    <Paper sx={{ p: 3 }}>
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <Typography variant="h6">{title}</Typography>
          </Grid>
          <Grid item>
            <Chip
              label={`Risk Level: ${riskLevel.level}`}
              color={riskLevel.color}
              variant="outlined"
            />
          </Grid>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Timeframe</InputLabel>
              <Select
                value={timeframe}
                label="Timeframe"
                onChange={(e) => setTimeframe(e.target.value)}
              >
                <MenuItem value="1M">1 Month</MenuItem>
                <MenuItem value="3M">3 Months</MenuItem>
                <MenuItem value="6M">6 Months</MenuItem>
                <MenuItem value="1Y">1 Year</MenuItem>
                <MenuItem value="2Y">2 Years</MenuItem>
                <MenuItem value="MAX">All Time</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Box>

      {/* Risk Metrics Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Max Drawdown
              </Typography>
              <Typography variant="h5" color="error">
                {(performanceMetrics.maxDrawdown * 100).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Volatility
              </Typography>
              <Typography variant="h5" color="warning.main">
                {(performanceMetrics.volatility * 100).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                VaR (95%)
              </Typography>
              <Typography variant="h5" color="error">
                {(performanceMetrics.var95 * 100).toFixed(2)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="text.secondary" gutterBottom>
                Sharpe Ratio
              </Typography>
              <Typography variant="h5" color={riskLevel.color}>
                {performanceMetrics.sharpeRatio.toFixed(3)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs for different risk visualizations */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Drawdown Analysis" />
          <Tab label="Volatility" />
          <Tab label="Value at Risk" />
          <Tab label="Return Distribution" />
        </Tabs>
      </Box>

      {/* Drawdown Chart */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ height: height - 200 }}>
          <Typography variant="subtitle1" gutterBottom>
            Portfolio Drawdown Analysis
          </Typography>
          <Line data={drawdownChartData} options={chartOptions} />
        </Box>
      </TabPanel>

      {/* Volatility Chart */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ height: height - 200 }}>
          <Typography variant="subtitle1" gutterBottom>
            Rolling Volatility (30-day)
          </Typography>
          <Line data={volatilityChartData} options={chartOptions} />
        </Box>
      </TabPanel>

      {/* VaR Chart */}
      <TabPanel value={tabValue} index={2}>
        <Box sx={{ height: height - 200 }}>
          <Typography variant="subtitle1" gutterBottom>
            Value at Risk (95% Confidence)
          </Typography>
          <Line data={varChartData} options={chartOptions} />
        </Box>
      </TabPanel>

      {/* Return Distribution */}
      <TabPanel value={tabValue} index={3}>
        <Box sx={{ height: height - 200 }}>
          <Typography variant="subtitle1" gutterBottom>
            Daily Return Distribution
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={8}>
              <Box sx={{ height: height - 280 }}>
                <Bar data={histogramData} options={barChartOptions} />
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Distribution Statistics
                  </Typography>
                  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Mean:</Typography>
                      <Typography variant="body2">
                        {(returnDistribution.statistics.mean * 100).toFixed(3)}%
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Median:</Typography>
                      <Typography variant="body2">
                        {(returnDistribution.statistics.median * 100).toFixed(3)}%
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Std Dev:</Typography>
                      <Typography variant="body2">
                        {(returnDistribution.statistics.standardDeviation * 100).toFixed(3)}%
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Skewness:</Typography>
                      <Typography variant="body2">
                        {returnDistribution.statistics.skewness.toFixed(3)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">Kurtosis:</Typography>
                      <Typography variant="body2">
                        {returnDistribution.statistics.kurtosis.toFixed(3)}
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">VaR 95%:</Typography>
                      <Typography variant="body2" color="error">
                        {(returnDistribution.statistics.var95 * 100).toFixed(3)}%
                      </Typography>
                    </Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Typography variant="body2">VaR 99%:</Typography>
                      <Typography variant="body2" color="error">
                        {(returnDistribution.statistics.var99 * 100).toFixed(3)}%
                      </Typography>
                    </Box>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Box>
      </TabPanel>
    </Paper>
  );
};

export default RiskMetricsVisualization;
