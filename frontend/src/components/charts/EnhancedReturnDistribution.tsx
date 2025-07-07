/**
 * Enhanced Return Distribution Chart
 * Comprehensive histogram with statistical analysis and risk metrics
 */

import React, { useMemo, useState } from 'react';
import { Bar, Line } from 'react-chartjs-2';
import Plot from 'react-plotly.js';
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
  ChartOptions
} from 'chart.js';
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import { ReturnDistribution, TimeFrame } from '../../types/charts';

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

interface EnhancedReturnDistributionProps {
  data: ReturnDistribution;
  benchmarkData?: ReturnDistribution;
  loading?: boolean;
  error?: string;
  title?: string;
  height?: number;
  showBenchmark?: boolean;
  onTimeFrameChange?: (timeFrame: TimeFrame) => void;
}

type DistributionView = 'histogram' | 'density' | 'qq' | 'statistics';
type ChartLibrary = 'chartjs' | 'plotly';

const EnhancedReturnDistribution: React.FC<EnhancedReturnDistributionProps> = ({
  data,
  benchmarkData,
  loading = false,
  error,
  title = 'Return Distribution Analysis',
  height = 500,
  showBenchmark = false,
  onTimeFrameChange
}) => {
  const theme = useTheme();
  const [tabValue, setTabValue] = useState(0);
  const [chartLibrary, setChartLibrary] = useState<ChartLibrary>('chartjs');
  const [timeFrame, setTimeFrame] = useState<TimeFrame>('1Y');
  const [bins, setBins] = useState(30);

  // Calculate additional statistics
  const extendedStats = useMemo(() => {
    const portfolio = {
      ...data.statistics,
      positiveReturns: data.returns.filter(r => r > 0).length,
      negativeReturns: data.returns.filter(r => r < 0).length,
      zeroReturns: data.returns.filter(r => r === 0).length,
      winRate: data.returns.filter(r => r > 0).length / data.returns.length,
      lossRate: data.returns.filter(r => r < 0).length / data.returns.length,
      averageWin: data.returns.filter(r => r > 0).reduce((sum, r) => sum + r, 0) / 
                  data.returns.filter(r => r > 0).length || 0,
      averageLoss: data.returns.filter(r => r < 0).reduce((sum, r) => sum + r, 0) / 
                   data.returns.filter(r => r < 0).length || 0,
      maxReturn: Math.max(...data.returns),
      minReturn: Math.min(...data.returns),
      sharpeEstimate: data.statistics.mean / data.statistics.standardDeviation
    };

    const benchmark = benchmarkData ? {
      ...benchmarkData.statistics,
      positiveReturns: benchmarkData.returns.filter(r => r > 0).length,
      negativeReturns: benchmarkData.returns.filter(r => r < 0).length,
      winRate: benchmarkData.returns.filter(r => r > 0).length / benchmarkData.returns.length,
      maxReturn: Math.max(...benchmarkData.returns),
      minReturn: Math.min(...benchmarkData.returns)
    } : null;

    return { portfolio, benchmark };
  }, [data, benchmarkData]);

  // Chart.js histogram data
  const histogramData = useMemo(() => ({
    labels: data.bins.map(bin => `${(bin * 100).toFixed(1)}%`),
    datasets: [
      {
        label: 'Portfolio Returns',
        data: data.frequencies,
        backgroundColor: `${theme.palette.primary.main}80`,
        borderColor: theme.palette.primary.main,
        borderWidth: 1
      },
      ...(showBenchmark && benchmarkData ? [{
        label: 'Benchmark Returns',
        data: benchmarkData.frequencies,
        backgroundColor: `${theme.palette.secondary.main}60`,
        borderColor: theme.palette.secondary.main,
        borderWidth: 1
      }] : [])
    ]
  }), [data, benchmarkData, theme, showBenchmark]);

  // Plotly histogram data
  const plotlyHistogramData = useMemo(() => {
    const traces: any[] = [
      {
        x: data.returns.map(r => r * 100),
        type: 'histogram',
        name: 'Portfolio Returns',
        nbinsx: bins,
        marker: {
          color: theme.palette.primary.main,
          opacity: 0.7
        },
        histnorm: 'probability density'
      }
    ];

    if (showBenchmark && benchmarkData) {
      traces.push({
        x: benchmarkData.returns.map(r => r * 100),
        type: 'histogram',
        name: 'Benchmark Returns',
        nbinsx: bins,
        marker: {
          color: theme.palette.secondary.main,
          opacity: 0.5
        },
        histnorm: 'probability density'
      });
    }

    // Add normal distribution overlay
    const normalDist = generateNormalDistribution(
      data.statistics.mean * 100,
      data.statistics.standardDeviation * 100,
      Math.min(...data.returns) * 100,
      Math.max(...data.returns) * 100
    );

    traces.push({
      x: normalDist.x,
      y: normalDist.y,
      type: 'scatter',
      mode: 'lines',
      name: 'Normal Distribution',
      line: {
        color: theme.palette.warning.main,
        dash: 'dash'
      }
    });

    return traces;
  }, [data, benchmarkData, theme, showBenchmark, bins]);

  // Q-Q plot data for normality testing
  const qqPlotData = useMemo(() => {
    const sortedReturns = [...data.returns].sort((a, b) => a - b);
    const n = sortedReturns.length;
    const theoreticalQuantiles = [];
    const sampleQuantiles = [];

    for (let i = 1; i <= n; i++) {
      const p = (i - 0.5) / n;
      theoreticalQuantiles.push(normalInverse(p) * data.statistics.standardDeviation + data.statistics.mean);
      sampleQuantiles.push(sortedReturns[i - 1]);
    }

    return [{
      x: theoreticalQuantiles.map(q => q * 100),
      y: sampleQuantiles.map(q => q * 100),
      type: 'scatter',
      mode: 'markers',
      name: 'Q-Q Plot',
      marker: {
        color: theme.palette.primary.main
      }
    }];
  }, [data, theme]);

  const chartOptions: ChartOptions<'bar'> = useMemo(() => ({
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
            return `${label}: ${value} occurrences`;
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

  const plotlyLayout = useMemo(() => ({
    title: tabValue === 2 ? 'Q-Q Plot: Sample vs Normal Distribution' : 'Return Distribution',
    xaxis: {
      title: tabValue === 2 ? 'Theoretical Quantiles (%)' : 'Daily Returns (%)'
    },
    yaxis: {
      title: tabValue === 2 ? 'Sample Quantiles (%)' : 'Density'
    },
    showlegend: true,
    height: height - 150,
    paper_bgcolor: 'transparent',
    plot_bgcolor: 'transparent',
    font: {
      color: theme.palette.text.primary
    }
  }), [tabValue, height, theme]);

  // Helper functions
  function generateNormalDistribution(mean: number, std: number, min: number, max: number) {
    const x = [];
    const y = [];
    const step = (max - min) / 100;
    
    for (let i = min; i <= max; i += step) {
      x.push(i);
      y.push((1 / (std * Math.sqrt(2 * Math.PI))) * 
             Math.exp(-0.5 * Math.pow((i - mean) / std, 2)));
    }
    
    return { x, y };
  }

  function normalInverse(p: number): number {
    // Approximation of the inverse normal distribution
    const a1 = -3.969683028665376e+01;
    const a2 = 2.209460984245205e+02;
    const a3 = -2.759285104469687e+02;
    const a4 = 1.383577518672690e+02;
    const a5 = -3.066479806614716e+01;
    const a6 = 2.506628277459239e+00;

    const b1 = -5.447609879822406e+01;
    const b2 = 1.615858368580409e+02;
    const b3 = -1.556989798598866e+02;
    const b4 = 6.680131188771972e+01;
    const b5 = -1.328068155288572e+01;

    if (p <= 0 || p >= 1) return 0;
    if (p === 0.5) return 0;

    const q = p < 0.5 ? p : 1 - p;
    const t = Math.sqrt(-2 * Math.log(q));
    
    const x = (((((a6 * t + a5) * t + a4) * t + a3) * t + a2) * t + a1) /
              ((((b5 * t + b4) * t + b3) * t + b2) * t + b1);
    
    return p < 0.5 ? -x : x;
  }

  const getRiskLevel = (): { level: string; color: 'success' | 'warning' | 'error' } => {
    const skew = Math.abs(data.statistics.skewness);
    const kurt = data.statistics.kurtosis;
    
    if (skew < 0.5 && kurt < 3.5) return { level: 'Normal-like', color: 'success' };
    if (skew < 1 && kurt < 5) return { level: 'Moderate Risk', color: 'warning' };
    return { level: 'High Risk', color: 'error' };
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

  const riskLevel = getRiskLevel();

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <Typography variant="h6">{title}</Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mt: 1 }}>
              <Chip
                label={riskLevel.level}
                color={riskLevel.color}
                size="small"
              />
              <Typography variant="body2" color="text.secondary">
                {data.returns.length} observations
              </Typography>
            </Box>
          </Grid>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Bins</InputLabel>
              <Select
                value={bins}
                label="Bins"
                onChange={(e) => setBins(Number(e.target.value))}
              >
                <MenuItem value={20}>20</MenuItem>
                <MenuItem value={30}>30</MenuItem>
                <MenuItem value={40}>40</MenuItem>
                <MenuItem value={50}>50</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid item>
            <ToggleButtonGroup
              value={chartLibrary}
              exclusive
              onChange={(_, value) => value && setChartLibrary(value)}
              size="small"
            >
              <ToggleButton value="chartjs">Chart.js</ToggleButton>
              <ToggleButton value="plotly">Plotly</ToggleButton>
            </ToggleButtonGroup>
          </Grid>
        </Grid>
      </Box>

      {/* Summary Statistics */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Mean Return
              </Typography>
              <Typography variant="h6">
                {(data.statistics.mean * 100).toFixed(3)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Volatility
              </Typography>
              <Typography variant="h6">
                {(data.statistics.standardDeviation * 100).toFixed(3)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Skewness
              </Typography>
              <Typography variant="h6" color={data.statistics.skewness < 0 ? 'error' : 'success'}>
                {data.statistics.skewness.toFixed(3)}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={6} sm={3}>
          <Card variant="outlined">
            <CardContent sx={{ p: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Win Rate
              </Typography>
              <Typography variant="h6" color="primary">
                {(extendedStats.portfolio.winRate * 100).toFixed(1)}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 2 }}>
        <Tabs value={tabValue} onChange={(_, newValue) => setTabValue(newValue)}>
          <Tab label="Distribution" />
          <Tab label="Density Plot" />
          <Tab label="Q-Q Plot" />
          <Tab label="Statistics" />
        </Tabs>
      </Box>

      {/* Distribution Histogram */}
      <TabPanel value={tabValue} index={0}>
        <Box sx={{ height: height - 250 }}>
          {chartLibrary === 'chartjs' ? (
            <Bar data={histogramData} options={chartOptions} />
          ) : (
            <Plot
              data={plotlyHistogramData as any}
              layout={plotlyLayout as any}
              config={{ responsive: true }}
              style={{ width: '100%', height: '100%' }}
            />
          )}
        </Box>
      </TabPanel>

      {/* Density Plot */}
      <TabPanel value={tabValue} index={1}>
        <Box sx={{ height: height - 250 }}>
          <Plot
            data={plotlyHistogramData as any}
            layout={plotlyLayout as any}
            config={{ responsive: true }}
            style={{ width: '100%', height: '100%' }}
          />
        </Box>
      </TabPanel>

      {/* Q-Q Plot */}
      <TabPanel value={tabValue} index={2}>
        <Box sx={{ height: height - 250 }}>
          <Plot
            data={qqPlotData as any}
            layout={plotlyLayout as any}
            config={{ responsive: true }}
            style={{ width: '100%', height: '100%' }}
          />
        </Box>
        <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
          Points along the diagonal line indicate normal distribution. Deviations suggest non-normal behavior.
        </Typography>
      </TabPanel>

      {/* Detailed Statistics */}
      <TabPanel value={tabValue} index={3}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Portfolio Statistics
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Total Observations</TableCell>
                        <TableCell align="right">{data.returns.length}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Mean Daily Return</TableCell>
                        <TableCell align="right">{(data.statistics.mean * 100).toFixed(4)}%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Median Daily Return</TableCell>
                        <TableCell align="right">{(data.statistics.median * 100).toFixed(4)}%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Standard Deviation</TableCell>
                        <TableCell align="right">{(data.statistics.standardDeviation * 100).toFixed(4)}%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Skewness</TableCell>
                        <TableCell align="right">{data.statistics.skewness.toFixed(4)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Kurtosis</TableCell>
                        <TableCell align="right">{data.statistics.kurtosis.toFixed(4)}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Minimum Return</TableCell>
                        <TableCell align="right" sx={{ color: 'error.main' }}>
                          {(extendedStats.portfolio.minReturn * 100).toFixed(4)}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Maximum Return</TableCell>
                        <TableCell align="right" sx={{ color: 'success.main' }}>
                          {(extendedStats.portfolio.maxReturn * 100).toFixed(4)}%
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} md={6}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Risk Metrics
                </Typography>
                <TableContainer>
                  <Table size="small">
                    <TableBody>
                      <TableRow>
                        <TableCell>Positive Returns</TableCell>
                        <TableCell align="right">{extendedStats.portfolio.positiveReturns}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Negative Returns</TableCell>
                        <TableCell align="right">{extendedStats.portfolio.negativeReturns}</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Win Rate</TableCell>
                        <TableCell align="right">{(extendedStats.portfolio.winRate * 100).toFixed(2)}%</TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Average Win</TableCell>
                        <TableCell align="right" sx={{ color: 'success.main' }}>
                          {(extendedStats.portfolio.averageWin * 100).toFixed(4)}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Average Loss</TableCell>
                        <TableCell align="right" sx={{ color: 'error.main' }}>
                          {(extendedStats.portfolio.averageLoss * 100).toFixed(4)}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>VaR (95%)</TableCell>
                        <TableCell align="right" sx={{ color: 'warning.main' }}>
                          {(data.statistics.var95 * 100).toFixed(4)}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>VaR (99%)</TableCell>
                        <TableCell align="right" sx={{ color: 'error.main' }}>
                          {(data.statistics.var99 * 100).toFixed(4)}%
                        </TableCell>
                      </TableRow>
                      <TableRow>
                        <TableCell>Sharpe Estimate</TableCell>
                        <TableCell align="right">{extendedStats.portfolio.sharpeEstimate.toFixed(4)}</TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>
                </TableContainer>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </TabPanel>
    </Paper>
  );
};

export default EnhancedReturnDistribution;
