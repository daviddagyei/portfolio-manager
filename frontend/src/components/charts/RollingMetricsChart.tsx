/**
 * Rolling Metrics Chart
 * Interactive charts for rolling Sharpe ratio, beta, correlation, and other rolling metrics
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
  TimeScale
);

interface RollingDataPoint {
  date: string;
  value: number;
}

interface RollingMetricsData {
  sharpe: RollingDataPoint[];
  beta: RollingDataPoint[];
  alpha: RollingDataPoint[];
  correlation: RollingDataPoint[];
  informationRatio: RollingDataPoint[];
  treynorRatio: RollingDataPoint[];
}

interface RollingMetricsChartProps {
  data: RollingMetricsData;
  loading?: boolean;
  error?: string;
  height?: number;
  selectedMetric?: keyof RollingMetricsData;
  onMetricChange?: (metric: keyof RollingMetricsData) => void;
  window?: number;
}

const metricConfigs = {
  sharpe: {
    label: 'Rolling Sharpe Ratio',
    color: '#1976d2',
    yAxisLabel: 'Sharpe Ratio',
    formatValue: (value: number) => value.toFixed(3),
    description: 'Risk-adjusted return metric'
  },
  beta: {
    label: 'Rolling Beta',
    color: '#d32f2f',
    yAxisLabel: 'Beta',
    formatValue: (value: number) => value.toFixed(3),
    description: 'Market sensitivity measure'
  },
  alpha: {
    label: 'Rolling Alpha',
    color: '#388e3c',
    yAxisLabel: 'Alpha (%)',
    formatValue: (value: number) => `${(value * 100).toFixed(2)}%`,
    description: 'Excess return vs benchmark'
  },
  correlation: {
    label: 'Rolling Correlation',
    color: '#f57c00',
    yAxisLabel: 'Correlation',
    formatValue: (value: number) => value.toFixed(3),
    description: 'Correlation with benchmark'
  },
  informationRatio: {
    label: 'Rolling Information Ratio',
    color: '#7b1fa2',
    yAxisLabel: 'Information Ratio',
    formatValue: (value: number) => value.toFixed(3),
    description: 'Active return per unit of tracking error'
  },
  treynorRatio: {
    label: 'Rolling Treynor Ratio',
    color: '#303f9f',
    yAxisLabel: 'Treynor Ratio',
    formatValue: (value: number) => value.toFixed(3),
    description: 'Return per unit of systematic risk'
  }
};

const RollingMetricsChart: React.FC<RollingMetricsChartProps> = ({
  data,
  loading = false,
  error,
  height = 400,
  selectedMetric = 'sharpe',
  onMetricChange,
  window = 30
}) => {
  const theme = useTheme();

  const chartData = useMemo(() => {
    const metricData = data[selectedMetric];
    const config = metricConfigs[selectedMetric];

    if (!metricData || metricData.length === 0) {
      return { datasets: [] };
    }

    return {
      datasets: [{
        label: config.label,
        data: metricData.map(point => ({
          x: point.date,
          y: point.value
        })),
        borderColor: config.color,
        backgroundColor: `${config.color}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 5
      }]
    };
  }, [data, selectedMetric]);

  const options: ChartOptions<'line'> = useMemo(() => {
    const config = metricConfigs[selectedMetric];
    
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
        title: {
          display: false
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          callbacks: {
            label: (context) => {
              const value = context.parsed.y;
              return `${config.label}: ${config.formatValue(value)}`;
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
            text: config.yAxisLabel
          },
          ticks: {
            callback: function(value) {
              return config.formatValue(Number(value));
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
    };
  }, [selectedMetric, theme]);

  const currentMetricData = data[selectedMetric];
  const latestValue = currentMetricData && currentMetricData.length > 0 
    ? currentMetricData[currentMetricData.length - 1].value 
    : null;

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
        <Grid item xs={12} md={6}>
          <Typography variant="h6">
            Rolling Metrics Analysis ({window}-day window)
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {metricConfigs[selectedMetric].description}
          </Typography>
        </Grid>
        <Grid item xs={12} md={3}>
          {onMetricChange && (
            <FormControl fullWidth size="small">
              <InputLabel>Metric</InputLabel>
              <Select
                value={selectedMetric}
                label="Metric"
                onChange={(e) => onMetricChange(e.target.value as keyof RollingMetricsData)}
              >
                {Object.entries(metricConfigs).map(([key, config]) => (
                  <MenuItem key={key} value={key}>
                    {config.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Grid>
        <Grid item xs={12} md={3}>
          {latestValue !== null && (
            <Card variant="outlined">
              <CardContent sx={{ py: 1 }}>
                <Typography variant="body2" color="text.secondary">
                  Current Value
                </Typography>
                <Typography variant="h6">
                  {metricConfigs[selectedMetric].formatValue(latestValue)}
                </Typography>
              </CardContent>
            </Card>
          )}
        </Grid>
      </Grid>
      
      <Box sx={{ height: height - 120 }}>
        <Line data={chartData} options={options} />
      </Box>
    </Paper>
  );
};

export default RollingMetricsChart;
