/**
 * Portfolio Performance Time Series Chart
 * Interactive multi-line chart for portfolio vs benchmark performance
 */

import React, { useMemo } from 'react';
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
  Filler,
  TimeScale
} from 'chart.js';
import 'chartjs-adapter-date-fns';
import {
  Paper,
  Typography,
  Box,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  useTheme
} from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  Filler,
  TimeScale
);

interface TimeSeriesDataPoint {
  date: string;
  value: number;
}

interface PerformanceTimeSeriesData {
  portfolio: TimeSeriesDataPoint[];
  benchmark?: TimeSeriesDataPoint[];
  riskFreeRate?: TimeSeriesDataPoint[];
}

interface PerformanceTimeSeriesChartProps {
  data: PerformanceTimeSeriesData;
  loading?: boolean;
  error?: string;
  title?: string;
  height?: number;
  showBenchmark?: boolean;
  showRiskFreeRate?: boolean;
  chartType?: 'cumulative' | 'returns' | 'normalized';
  onChartTypeChange?: (type: 'cumulative' | 'returns' | 'normalized') => void;
}

const PerformanceTimeSeriesChart: React.FC<PerformanceTimeSeriesChartProps> = ({
  data,
  loading = false,
  error,
  title = 'Portfolio Performance',
  height = 400,
  showBenchmark = true,
  showRiskFreeRate = false,
  chartType = 'cumulative',
  onChartTypeChange
}) => {
  const theme = useTheme();

  const chartData = useMemo(() => {
    const datasets = [];

    // Portfolio data
    if (data.portfolio && data.portfolio.length > 0) {
      datasets.push({
        label: 'Portfolio',
        data: data.portfolio.map(point => ({
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
      });
    }

    // Benchmark data
    if (showBenchmark && data.benchmark && data.benchmark.length > 0) {
      datasets.push({
        label: 'Benchmark',
        data: data.benchmark.map(point => ({
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
      });
    }

    // Risk-free rate data
    if (showRiskFreeRate && data.riskFreeRate && data.riskFreeRate.length > 0) {
      datasets.push({
        label: 'Risk-Free Rate',
        data: data.riskFreeRate.map(point => ({
          x: point.date,
          y: point.value
        })),
        borderColor: theme.palette.grey[500],
        backgroundColor: `${theme.palette.grey[500]}20`,
        borderWidth: 1,
        fill: false,
        pointRadius: 0,
        pointHoverRadius: 3,
        borderDash: [2, 2]
      });
    }

    return { datasets };
  }, [data, theme, showBenchmark, showRiskFreeRate]);

  const options: ChartOptions<'line'> = useMemo(() => ({
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
      title: {
        display: false
      },
      tooltip: {
        mode: 'index',
        intersect: false,
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y;
            if (chartType === 'returns') {
              return `${label}: ${(value * 100).toFixed(2)}%`;
            }
            return `${label}: ${value.toFixed(4)}`;
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
          text: chartType === 'returns' ? 'Daily Returns (%)' : 
                chartType === 'normalized' ? 'Normalized Value' : 'Cumulative Value'
        },
        ticks: {
          callback: function(value) {
            if (chartType === 'returns') {
              return `${(Number(value) * 100).toFixed(1)}%`;
            }
            return Number(value).toFixed(2);
          }
        }
      }
    },
    interaction: {
      mode: 'nearest',
      axis: 'x',
      intersect: false
    },
    elements: {
      point: {
        hoverBackgroundColor: theme.palette.background.paper
      }
    }
  }), [theme, chartType]);

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
      <Box sx={{ mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <Typography variant="h6">{title}</Typography>
          </Grid>
          {onChartTypeChange && (
            <Grid item>
              <FormControl size="small" sx={{ minWidth: 150 }}>
                <InputLabel>Chart Type</InputLabel>
                <Select
                  value={chartType}
                  label="Chart Type"
                  onChange={(e) => onChartTypeChange(e.target.value as any)}
                >
                  <MenuItem value="cumulative">Cumulative</MenuItem>
                  <MenuItem value="returns">Daily Returns</MenuItem>
                  <MenuItem value="normalized">Normalized</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          )}
        </Grid>
      </Box>
      
      <Box sx={{ height: height - 80 }}>
        <Line data={chartData} options={options} />
      </Box>
    </Paper>
  );
};

export default PerformanceTimeSeriesChart;
