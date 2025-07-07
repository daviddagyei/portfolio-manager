/**
 * Risk Metrics Visualization
 * Comprehensive risk analytics charts including drawdown, volatility, and VaR
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
  Filler,
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
  Tabs,
  Tab,
  Card,
  CardContent,
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
  Filler,
  TimeScale
);

interface RiskDataPoint {
  date: string;
  value: number;
}

interface RiskMetricsData {
  drawdown: RiskDataPoint[];
  volatility: RiskDataPoint[];
  var95: RiskDataPoint[];
  var99: RiskDataPoint[];
  returns: RiskDataPoint[];
}

interface RiskMetricsChartProps {
  data: RiskMetricsData;
  loading?: boolean;
  error?: string;
  height?: number;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => (
  <div role="tabpanel" hidden={value !== index}>
    {value === index && <Box>{children}</Box>}
  </div>
);

const RiskMetricsChart: React.FC<RiskMetricsChartProps> = ({
  data,
  loading = false,
  error,
  height = 400
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = React.useState(0);

  const drawdownChartData = useMemo(() => ({
    datasets: [{
      label: 'Drawdown',
      data: data.drawdown?.map(point => ({
        x: point.date,
        y: point.value * 100 // Convert to percentage
      })) || [],
      borderColor: theme.palette.error.main,
      backgroundColor: `${theme.palette.error.main}30`,
      borderWidth: 2,
      fill: 'origin',
      tension: 0.1,
      pointRadius: 1,
      pointHoverRadius: 4
    }]
  }), [data.drawdown, theme]);

  const volatilityChartData = useMemo(() => ({
    datasets: [{
      label: 'Rolling Volatility (30d)',
      data: data.volatility?.map(point => ({
        x: point.date,
        y: point.value * 100 // Convert to percentage
      })) || [],
      borderColor: theme.palette.warning.main,
      backgroundColor: `${theme.palette.warning.main}20`,
      borderWidth: 2,
      fill: false,
      tension: 0.1,
      pointRadius: 1,
      pointHoverRadius: 4
    }]
  }), [data.volatility, theme]);

  const varChartData = useMemo(() => ({
    datasets: [
      {
        label: 'VaR 95%',
        data: data.var95?.map(point => ({
          x: point.date,
          y: point.value * 100
        })) || [],
        borderColor: theme.palette.info.main,
        backgroundColor: `${theme.palette.info.main}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 4
      },
      {
        label: 'VaR 99%',
        data: data.var99?.map(point => ({
          x: point.date,
          y: point.value * 100
        })) || [],
        borderColor: theme.palette.error.main,
        backgroundColor: `${theme.palette.error.main}20`,
        borderWidth: 2,
        fill: false,
        tension: 0.1,
        pointRadius: 1,
        pointHoverRadius: 4,
        borderDash: [5, 5]
      }
    ]
  }), [data.var95, data.var99, theme]);

  const returnsHistogramData = useMemo(() => {
    if (!data.returns || data.returns.length === 0) return { labels: [], datasets: [] };

    // Create histogram bins
    const returns = data.returns.map(d => d.value * 100); // Convert to percentage
    const min = Math.min(...returns);
    const max = Math.max(...returns);
    const binCount = Math.min(50, Math.ceil(Math.sqrt(returns.length)));
    const binWidth = (max - min) / binCount;
    
    const bins = Array.from({ length: binCount }, (_, i) => ({
      min: min + i * binWidth,
      max: min + (i + 1) * binWidth,
      count: 0
    }));

    // Count returns in each bin
    returns.forEach(ret => {
      const binIndex = Math.min(Math.floor((ret - min) / binWidth), binCount - 1);
      bins[binIndex].count++;
    });

    return {
      labels: bins.map(bin => `${bin.min.toFixed(1)}%`),
      datasets: [{
        label: 'Frequency',
        data: bins.map(bin => bin.count),
        backgroundColor: `${theme.palette.primary.main}80`,
        borderColor: theme.palette.primary.main,
        borderWidth: 1
      }]
    };
  }, [data.returns, theme]);

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
            month: 'MMM yyyy'
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
          text: 'Percentage (%)'
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
  }), []);

  const histogramOptions: ChartOptions<'bar'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      title: {
        display: true,
        text: 'Return Distribution'
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const value = context.parsed.y;
            return `Frequency: ${value}`;
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
      <Typography variant="h6" gutterBottom>
        Risk Metrics Analysis
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={(e, newValue) => setTabValue(newValue)}>
          <Tab label="Drawdown" />
          <Tab label="Volatility" />
          <Tab label="Value at Risk" />
          <Tab label="Return Distribution" />
        </Tabs>
      </Box>

      <TabPanel value={tabValue} index={0}>
        <Box sx={{ height: height - 120 }}>
          <Line data={drawdownChartData} options={lineChartOptions} />
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <Box sx={{ height: height - 120 }}>
          <Line data={volatilityChartData} options={lineChartOptions} />
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Box sx={{ height: height - 120 }}>
          <Line data={varChartData} options={lineChartOptions} />
        </Box>
      </TabPanel>

      <TabPanel value={tabValue} index={3}>
        <Box sx={{ height: height - 120 }}>
          <Bar data={returnsHistogramData} options={histogramOptions} />
        </Box>
      </TabPanel>
    </Paper>
  );
};

export default RiskMetricsChart;
