/**
 * Rolling Metrics Chart Component
 * Interactive charts for rolling Sharpe ratio, beta, alpha, and correlation
 */

import React, { useMemo, useState } from 'react';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
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
  CardContent
} from '@mui/material';
import { RollingMetrics, TimeFrame } from '../../types/charts';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  TimeScale
);

interface RollingMetricsChartProps {
  data: RollingMetrics;
  loading?: boolean;
  error?: string;
  title?: string;
  height?: number;
  showBenchmarkMetrics?: boolean;
  onTimeFrameChange?: (timeFrame: TimeFrame) => void;
}

type MetricType = 'sharpe' | 'volatility' | 'beta' | 'alpha' | 'correlation';

const RollingMetricsChart: React.FC<RollingMetricsChartProps> = ({
  data,
  loading = false,
  error,
  title = 'Rolling Performance Metrics',
  height = 400,
  showBenchmarkMetrics = true,
  onTimeFrameChange
}) => {
  const theme = useTheme();
  const [selectedMetrics, setSelectedMetrics] = useState<MetricType[]>(['sharpe', 'volatility']);
  const [rollingWindow, setRollingWindow] = useState<number>(30);
  const [timeFrame, setTimeFrame] = useState<TimeFrame>('1Y');

  const metricConfigs = useMemo(() => ({
    sharpe: {
      label: 'Sharpe Ratio',
      color: theme.palette.primary.main,
      data: data.sharpeRatio,
      yAxisTitle: 'Sharpe Ratio',
      formatter: (value: number) => value.toFixed(3)
    },
    volatility: {
      label: 'Volatility',
      color: theme.palette.secondary.main,
      data: data.volatility,
      yAxisTitle: 'Volatility (%)',
      formatter: (value: number) => `${(value * 100).toFixed(2)}%`
    },
    beta: {
      label: 'Beta',
      color: theme.palette.success.main,
      data: data.beta || [],
      yAxisTitle: 'Beta',
      formatter: (value: number) => value.toFixed(3)
    },
    alpha: {
      label: 'Alpha',
      color: theme.palette.warning.main,
      data: data.alpha || [],
      yAxisTitle: 'Alpha (%)',
      formatter: (value: number) => `${(value * 100).toFixed(2)}%`
    },
    correlation: {
      label: 'Correlation',
      color: theme.palette.info.main,
      data: data.correlation || [],
      yAxisTitle: 'Correlation',
      formatter: (value: number) => value.toFixed(3)
    }
  }), [data, theme]);

  const chartData = useMemo(() => {
    const datasets = selectedMetrics
      .filter(metric => metricConfigs[metric].data.length > 0)
      .map((metric, index) => ({
        label: metricConfigs[metric].label,
        data: data.dates.map((date, i) => ({
          x: date,
          y: metricConfigs[metric].data[i] || 0
        })),
        borderColor: metricConfigs[metric].color,
        backgroundColor: `${metricConfigs[metric].color}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 5,
        yAxisID: selectedMetrics.length > 1 ? `y${index}` : 'y'
      }));

    return { datasets };
  }, [data, selectedMetrics, metricConfigs]);

  const chartOptions: ChartOptions<'line'> = useMemo(() => {
    const scales: any = {
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
      }
    };

    // Configure Y-axes based on selected metrics
    if (selectedMetrics.length === 1) {
      scales.y = {
        title: {
          display: true,
          text: metricConfigs[selectedMetrics[0]].yAxisTitle
        },
        ticks: {
          callback: function(value: any) {
            return metricConfigs[selectedMetrics[0]].formatter(Number(value));
          }
        }
      };
    } else {
      // Multiple Y-axes for different metrics
      selectedMetrics.forEach((metric, index) => {
        scales[`y${index}`] = {
          type: 'linear',
          display: true,
          position: index % 2 === 0 ? 'left' : 'right',
          title: {
            display: true,
            text: metricConfigs[metric].yAxisTitle
          },
          ticks: {
            callback: function(value: any) {
              return metricConfigs[metric].formatter(Number(value));
            }
          },
          ...(index > 0 && { grid: { drawOnChartArea: false } })
        };
      });
    }

    return {
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
              const metric = selectedMetrics[context.datasetIndex];
              const value = context.parsed.y;
              return `${context.dataset.label}: ${metricConfigs[metric].formatter(value)}`;
            }
          }
        }
      },
      scales,
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false
      }
    };
  }, [selectedMetrics, metricConfigs]);

  const handleMetricToggle = (
    event: React.MouseEvent<HTMLElement>,
    newMetrics: MetricType[]
  ) => {
    if (newMetrics.length > 0) {
      setSelectedMetrics(newMetrics);
    }
  };

  const handleTimeFrameChange = (newTimeFrame: TimeFrame) => {
    setTimeFrame(newTimeFrame);
    onTimeFrameChange?.(newTimeFrame);
  };

  // Calculate current metric values for display
  const getCurrentMetricValues = () => {
    const latest = data.dates.length - 1;
    if (latest < 0) return {};

    return {
      sharpe: data.sharpeRatio[latest],
      volatility: data.volatility[latest],
      beta: data.beta?.[latest],
      alpha: data.alpha?.[latest],
      correlation: data.correlation?.[latest]
    };
  };

  const currentValues = getCurrentMetricValues();

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
          </Grid>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Window</InputLabel>
              <Select
                value={rollingWindow}
                label="Window"
                onChange={(e) => setRollingWindow(Number(e.target.value))}
              >
                <MenuItem value={15}>15 Days</MenuItem>
                <MenuItem value={30}>30 Days</MenuItem>
                <MenuItem value={60}>60 Days</MenuItem>
                <MenuItem value={90}>90 Days</MenuItem>
                <MenuItem value={252}>1 Year</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>Period</InputLabel>
              <Select
                value={timeFrame}
                label="Period"
                onChange={(e) => handleTimeFrameChange(e.target.value as TimeFrame)}
              >
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

      {/* Current Values Summary */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {Object.entries(currentValues).map(([key, value]) => {
          if (value === undefined) return null;
          const config = metricConfigs[key as MetricType];
          return (
            <Grid item xs={6} sm={4} md={2.4} key={key}>
              <Card variant="outlined">
                <CardContent sx={{ p: 2, '&:last-child': { pb: 2 } }}>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    Current {config.label}
                  </Typography>
                  <Typography variant="h6" sx={{ color: config.color }}>
                    {config.formatter(value)}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {/* Metric Selection */}
      <Box sx={{ mb: 3 }}>
        <Typography variant="subtitle2" gutterBottom>
          Select Metrics to Display:
        </Typography>
        <ToggleButtonGroup
          value={selectedMetrics}
          onChange={handleMetricToggle}
          aria-label="metric selection"
          size="small"
        >
          <ToggleButton value="sharpe">Sharpe Ratio</ToggleButton>
          <ToggleButton value="volatility">Volatility</ToggleButton>
          {showBenchmarkMetrics && (
            <>
              <ToggleButton value="beta" disabled={!data.beta?.length}>
                Beta
              </ToggleButton>
              <ToggleButton value="alpha" disabled={!data.alpha?.length}>
                Alpha
              </ToggleButton>
              <ToggleButton value="correlation" disabled={!data.correlation?.length}>
                Correlation
              </ToggleButton>
            </>
          )}
        </ToggleButtonGroup>
      </Box>

      {/* Chart */}
      <Box sx={{ height: height - 250 }}>
        <Line data={chartData} options={chartOptions} />
      </Box>

      {/* Chart Description */}
      <Box sx={{ mt: 2 }}>
        <Typography variant="caption" color="text.secondary">
          Rolling {rollingWindow}-day metrics calculated over the selected time period. 
          Multiple metrics can be displayed simultaneously with individual Y-axes.
        </Typography>
      </Box>
    </Paper>
  );
};

export default RollingMetricsChart;
