/**
 * Return Distribution Chart
 * Advanced statistical analysis of return distributions with histograms and overlays
 */

import React, { useMemo } from 'react';
import { Bar, Line, Chart } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
  ChartData,
  ChartDataset,
  Point
} from 'chart.js';
import {
  Paper,
  Typography,
  Box,
  Grid,
  CircularProgress,
  Alert,
  Card,
  CardContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Chip,
  Divider,
  useTheme
} from '@mui/material';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

interface ReturnDataPoint {
  date: string;
  return: number;
}

interface DistributionStats {
  mean: number;
  median: number;
  standardDeviation: number;
  skewness: number;
  kurtosis: number;
  var95: number;
  var99: number;
  cvar95: number;
  cvar99: number;
  jarqueBera: number;
  shapiroWilk: number;
  positiveReturns: number;
  negativeReturns: number;
  maxReturn: number;
  minReturn: number;
}

interface ReturnDistributionData {
  returns: ReturnDataPoint[];
  benchmarkReturns?: ReturnDataPoint[];
  stats: DistributionStats;
  benchmarkStats?: DistributionStats;
}

interface ReturnDistributionChartProps {
  data: ReturnDistributionData;
  loading?: boolean;
  error?: string;
  height?: number;
  binCount?: number;
  showBenchmark?: boolean;
  showNormalOverlay?: boolean;
  distributionType?: 'returns' | 'logReturns';
  onDistributionTypeChange?: (type: 'returns' | 'logReturns') => void;
}

const ReturnDistributionChart: React.FC<ReturnDistributionChartProps> = ({
  data,
  loading = false,
  error,
  height = 400,
  binCount = 50,
  showBenchmark = false,
  showNormalOverlay = true,
  distributionType = 'returns',
  onDistributionTypeChange
}) => {
  const theme = useTheme();

  // --- Fix types for mixed chart ---
  const { histogramData, normalData } = useMemo(() => {
    if (!data.returns || data.returns.length === 0) {
      return {
        histogramData: { labels: [], datasets: [] },
        normalData: { labels: [], datasets: [] }
      };
    }

    const returns = data.returns.map(d => d.return * 100); // Convert to percentage
    const benchmarkReturns = data.benchmarkReturns?.map(d => d.return * 100) || [];

    // Calculate histogram bins
    const allReturns = showBenchmark ? [...returns, ...benchmarkReturns] : returns;
    const min = Math.min(...allReturns);
    const max = Math.max(...allReturns);
    const binWidth = (max - min) / binCount;

    const bins = Array.from({ length: binCount }, (_, i) => ({
      min: min + i * binWidth,
      max: min + (i + 1) * binWidth,
      center: min + (i + 0.5) * binWidth,
      portfolioCount: 0,
      benchmarkCount: 0
    }));

    // Count returns in each bin
    returns.forEach(ret => {
      const binIndex = Math.min(Math.floor((ret - min) / binWidth), binCount - 1);
      if (binIndex >= 0) bins[binIndex].portfolioCount++;
    });

    if (showBenchmark && benchmarkReturns.length > 0) {
      benchmarkReturns.forEach(ret => {
        const binIndex = Math.min(Math.floor((ret - min) / binWidth), binCount - 1);
        if (binIndex >= 0) bins[binIndex].benchmarkCount++;
      });
    }

    const labels = bins.map(bin => bin.center.toFixed(1));

    const datasets: ChartDataset<'bar' | 'line', (number | [number, number] | Point | null)[]>[] = [
      {
        label: 'Portfolio',
        data: bins.map(bin => bin.portfolioCount),
        backgroundColor: `${theme.palette.primary.main}80`,
        borderColor: theme.palette.primary.main,
        borderWidth: 1,
        type: 'bar'
      }
    ];

    if (showBenchmark && benchmarkReturns.length > 0) {
      datasets.push({
        label: 'Benchmark',
        data: bins.map(bin => bin.benchmarkCount),
        backgroundColor: `${theme.palette.secondary.main}60`,
        borderColor: theme.palette.secondary.main,
        borderWidth: 1,
        type: 'bar'
      });
    }

    const histogramData: ChartData<'bar' | 'line', (number | [number, number] | Point | null)[]> = { labels, datasets };

    // Generate normal distribution overlay
    let normalData: ChartData<'bar' | 'line', (number | [number, number] | Point | null)[]> = { labels: [], datasets: [] };
    if (showNormalOverlay && data.stats) {
      const mean = data.stats.mean * 100;
      const std = data.stats.standardDeviation * 100;
      const normalPoints = bins.map(bin => {
        const x = bin.center;
        const normalValue = (1 / (std * Math.sqrt(2 * Math.PI))) *
          Math.exp(-0.5 * Math.pow((x - mean) / std, 2));
        return {
          x: x.toFixed(1),
          y: normalValue * returns.length * binWidth // Scale to match histogram
        };
      });

      normalData = {
        labels: normalPoints.map(p => p.x),
        datasets: [{
          label: 'Normal Distribution',
          data: normalPoints.map(p => p.y),
          borderColor: theme.palette.warning.main,
          backgroundColor: undefined,
          borderWidth: 2,
          type: 'line',
          fill: false,
          tension: 0.4,
          pointRadius: 0
        }]
      };
    }

    return { histogramData, normalData };
  }, [data, theme, binCount, showBenchmark, showNormalOverlay]);

  // --- Fix chartData type for mixed chart ---
  const chartData: ChartData<'bar' | 'line', (number | [number, number] | Point | null)[]> = useMemo(() => {
    if (!showNormalOverlay || !normalData.datasets.length) return histogramData;
    return {
      labels: histogramData.labels,
      datasets: [
        ...histogramData.datasets,
        ...normalData.datasets
      ]
    };
  }, [histogramData, normalData, showNormalOverlay]);

  // --- Fix options type for mixed chart ---
  const options: ChartOptions<'bar' | 'line'> = useMemo(() => ({
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
        display: true,
        text: `Return Distribution (${data.returns?.length || 0} observations)`
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.dataset.label || '';
            const value = context.parsed.y ?? context.parsed;
            if (context.dataset.type === 'line') {
              return `${label}: ${typeof value === 'number' ? value.toFixed(4) : value}`;
            }
            return `${label}: ${typeof value === 'number' ? value : 0} observations`;
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
        },
        beginAtZero: true
      }
    }
  }), [data.returns]);

  const renderStatCard = (title: string, stats: DistributionStats) => (
    <Card variant="outlined" sx={{ height: '100%' }}>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {title}
        </Typography>
        <Grid container spacing={1}>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Mean</Typography>
            <Typography variant="body1">{(stats.mean * 100).toFixed(2)}%</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Std Dev</Typography>
            <Typography variant="body1">{(stats.standardDeviation * 100).toFixed(2)}%</Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Skewness</Typography>
            <Chip
              label={stats.skewness.toFixed(3)}
              color={Math.abs(stats.skewness) < 0.5 ? 'success' : 'warning'}
              size="small"
            />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Kurtosis</Typography>
            <Chip
              label={stats.kurtosis.toFixed(3)}
              color={Math.abs(stats.kurtosis - 3) < 1 ? 'success' : 'warning'}
              size="small"
            />
          </Grid>
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }} />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">VaR 95%</Typography>
            <Typography variant="body1" color="error.main">
              {(stats.var95 * 100).toFixed(2)}%
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">VaR 99%</Typography>
            <Typography variant="body1" color="error.main">
              {(stats.var99 * 100).toFixed(2)}%
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">CVaR 95%</Typography>
            <Typography variant="body1" color="error.main">
              {(stats.cvar95 * 100).toFixed(2)}%
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">CVaR 99%</Typography>
            <Typography variant="body1" color="error.main">
              {(stats.cvar99 * 100).toFixed(2)}%
            </Typography>
          </Grid>
          <Grid item xs={12}>
            <Divider sx={{ my: 1 }} />
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Positive Days</Typography>
            <Typography variant="body1" color="success.main">
              {stats.positiveReturns} ({((stats.positiveReturns / (stats.positiveReturns + stats.negativeReturns)) * 100).toFixed(1)}%)
            </Typography>
          </Grid>
          <Grid item xs={6}>
            <Typography variant="body2" color="text.secondary">Negative Days</Typography>
            <Typography variant="body1" color="error.main">
              {stats.negativeReturns} ({((stats.negativeReturns / (stats.positiveReturns + stats.negativeReturns)) * 100).toFixed(1)}%)
            </Typography>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );

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
            Return Distribution Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Statistical analysis of return patterns and risk characteristics
          </Typography>
        </Grid>
        <Grid item xs={12} md={4}>
          {onDistributionTypeChange && (
            <FormControl fullWidth size="small">
              <InputLabel>Distribution Type</InputLabel>
              <Select
                value={distributionType}
                label="Distribution Type"
                onChange={(e) => onDistributionTypeChange(e.target.value as any)}
              >
                <MenuItem value="returns">Simple Returns</MenuItem>
                <MenuItem value="logReturns">Log Returns</MenuItem>
              </Select>
            </FormControl>
          )}
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Box sx={{ height: height - 120 }}>
            <Chart type="bar" data={chartData} options={options} />
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              {renderStatCard('Portfolio Statistics', data.stats)}
            </Grid>
            {showBenchmark && data.benchmarkStats && (
              <Grid item xs={12}>
                {renderStatCard('Benchmark Statistics', data.benchmarkStats)}
              </Grid>
            )}
          </Grid>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default ReturnDistributionChart;
