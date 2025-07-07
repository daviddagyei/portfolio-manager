/**
 * Efficient Frontier Chart
 * Visualization of the efficient frontier with key portfolios and interactive features
 */

import React, { useMemo, useState, useEffect } from 'react';
import { Scatter } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Title,
  ChartOptions,
  ChartData,
  TooltipItem
} from 'chart.js';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Divider,
  useTheme,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import { TrendingUp, TrendingDown, ShowChart, PieChart } from '@mui/icons-material';

ChartJS.register(
  LinearScale,
  PointElement,
  LineElement,
  Tooltip,
  Legend,
  Title
);

interface FrontierPoint {
  expected_return: number;
  volatility: number;
  weights: Record<string, number>;
  sharpe_ratio: number;
}

interface KeyPortfolio {
  name: string;
  weights: Record<string, number>;
  expected_return: number;
  volatility: number;
  sharpe_ratio: number;
}

interface EfficientFrontierData {
  frontier_points: FrontierPoint[];
  key_portfolios: KeyPortfolio[];
  assets: string[];
  optimization_date: string;
  risk_free_rate: number;
}

interface EfficientFrontierChartProps {
  data: EfficientFrontierData;
  loading?: boolean;
  error?: string;
  height?: number;
  showKeyPortfolios?: boolean;
  showAssetComposition?: boolean;
  selectedPortfolio?: KeyPortfolio | null;
  onPortfolioSelect?: (portfolio: KeyPortfolio | null) => void;
  onFrontierPointSelect?: (point: FrontierPoint) => void;
}

const EfficientFrontierChart: React.FC<EfficientFrontierChartProps> = ({
  data,
  loading = false,
  error,
  height = 500,
  showKeyPortfolios = true,
  showAssetComposition = true,
  selectedPortfolio,
  onPortfolioSelect,
  onFrontierPointSelect
}) => {
  const theme = useTheme();
  const [highlightedPortfolio, setHighlightedPortfolio] = useState<string | null>(null);
  const [showLabels, setShowLabels] = useState(true);
  const [chartType, setChartType] = useState<'frontier' | 'weights'>('frontier');
  const [localShowAssetComposition, setLocalShowAssetComposition] = useState(showAssetComposition);
  const [localShowKeyPortfolios, setLocalShowKeyPortfolios] = useState(showKeyPortfolios);

  // Sync local state with props
  useEffect(() => {
    setLocalShowAssetComposition(showAssetComposition);
  }, [showAssetComposition]);

  useEffect(() => {
    setLocalShowKeyPortfolios(showKeyPortfolios);
  }, [showKeyPortfolios]);

  const chartData: ChartData<'scatter'> = useMemo(() => {
    if (!data.frontier_points || data.frontier_points.length === 0) {
      return { datasets: [] };
    }

    const datasets = [];

    // Efficient frontier line
    const frontierPoints = data.frontier_points.map(point => ({
      x: point.volatility * 100, // Convert to percentage
      y: point.expected_return * 100, // Convert to percentage
      point: point
    }));

    datasets.push({
      label: 'Efficient Frontier',
      data: frontierPoints,
      backgroundColor: 'transparent',
      borderColor: theme.palette.primary.main,
      borderWidth: 3,
      pointRadius: 0,
      pointHoverRadius: 5,
      showLine: true,
      tension: 0.1
    });

    // Key portfolios
    if (localShowKeyPortfolios && data.key_portfolios) {
      const portfolioColors = {
        'Maximum Sharpe Ratio': theme.palette.success.main,
        'Minimum Volatility': theme.palette.info.main,
        'Maximum Return': theme.palette.warning.main,
        'Equal Weight': theme.palette.secondary.main
      };

      data.key_portfolios.forEach(portfolio => {
        const color = portfolioColors[portfolio.name as keyof typeof portfolioColors] || theme.palette.error.main;
        const isHighlighted = highlightedPortfolio === portfolio.name || selectedPortfolio?.name === portfolio.name;
        
        datasets.push({
          label: portfolio.name,
          data: [{
            x: portfolio.volatility * 100,
            y: portfolio.expected_return * 100,
            portfolio: portfolio
          }],
          backgroundColor: color,
          borderColor: theme.palette.background.paper,
          borderWidth: isHighlighted ? 3 : 2,
          pointRadius: isHighlighted ? 12 : 8,
          pointHoverRadius: 14,
          showLine: false
        });
      });
    }

    return { datasets };
  }, [data, theme, localShowKeyPortfolios, highlightedPortfolio, selectedPortfolio]);

  const options: ChartOptions<'scatter'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          filter: (legendItem) => legendItem.text !== 'Efficient Frontier' || showLabels
        }
      },
      title: {
        display: true,
        text: 'Efficient Frontier Analysis'
      },
      tooltip: {
        callbacks: {
          title: (context) => {
            const dataPoint = context[0].raw as any;
            if (dataPoint.portfolio) {
              return dataPoint.portfolio.name;
            }
            return 'Efficient Frontier Point';
          },
          label: (context: TooltipItem<'scatter'>) => {
            const dataPoint = context.raw as any;
            const labels = [
              `Return: ${context.parsed.y.toFixed(2)}%`,
              `Risk: ${context.parsed.x.toFixed(2)}%`
            ];
            
            if (dataPoint.portfolio) {
              labels.push(`Sharpe: ${dataPoint.portfolio.sharpe_ratio.toFixed(3)}`);
            } else if (dataPoint.point) {
              labels.push(`Sharpe: ${dataPoint.point.sharpe_ratio.toFixed(3)}`);
            }
            
            return labels;
          },
          afterLabel: (context: TooltipItem<'scatter'>) => {
            const dataPoint = context.raw as any;
            const weights = dataPoint.portfolio?.weights || dataPoint.point?.weights;
            
            if (weights && localShowAssetComposition) {
              const topWeights = Object.entries(weights)
                .sort(([, a], [, b]) => (b as number) - (a as number))
                .slice(0, 5)
                .map(([asset, weight]) => `${asset}: ${((weight as number) * 100).toFixed(1)}%`);
              
              return ['', 'Top Holdings:', ...topWeights];
            }
            return [];
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Volatility (%)'
        },
        grid: {
          color: theme.palette.divider
        }
      },
      y: {
        title: {
          display: true,
          text: 'Expected Return (%)'
        },
        grid: {
          color: theme.palette.divider
        }
      }
    },
    onClick: (event, elements) => {
      if (elements.length > 0) {
        const element = elements[0];
        const dataPoint = chartData.datasets[element.datasetIndex].data[element.index] as any;
        
        if (dataPoint.portfolio && onPortfolioSelect) {
          onPortfolioSelect(dataPoint.portfolio);
        } else if (dataPoint.point && onFrontierPointSelect) {
          onFrontierPointSelect(dataPoint.point);
        }
      }
    }
  }), [theme, showLabels, localShowAssetComposition, chartData, onPortfolioSelect, onFrontierPointSelect]);

  const renderPortfolioMetrics = () => {
    if (!data.key_portfolios || !localShowKeyPortfolios) return null;

    return (
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Key Portfolios
          </Typography>
          <TableContainer>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Portfolio</TableCell>
                  <TableCell align="right">Return</TableCell>
                  <TableCell align="right">Risk</TableCell>
                  <TableCell align="right">Sharpe</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {data.key_portfolios.map((portfolio, index) => (
                  <TableRow
                    key={index}
                    hover
                    onClick={() => onPortfolioSelect?.(portfolio)}
                    onMouseEnter={() => setHighlightedPortfolio(portfolio.name)}
                    onMouseLeave={() => setHighlightedPortfolio(null)}
                    sx={{ 
                      cursor: 'pointer',
                      backgroundColor: selectedPortfolio?.name === portfolio.name 
                        ? theme.palette.action.selected 
                        : 'transparent'
                    }}
                  >
                    <TableCell>
                      <Box display="flex" alignItems="center">
                        <Chip
                          size="small"
                          label={portfolio.name.split(' ')[0]}
                          color={
                            portfolio.name.includes('Sharpe') ? 'success' :
                            portfolio.name.includes('Volatility') ? 'info' :
                            portfolio.name.includes('Return') ? 'warning' : 'secondary'
                          }
                          sx={{ mr: 1 }}
                        />
                        {portfolio.name}
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      <Box display="flex" alignItems="center" justifyContent="flex-end">
                        {portfolio.expected_return > 0 ? (
                          <TrendingUp color="success" fontSize="small" />
                        ) : (
                          <TrendingDown color="error" fontSize="small" />
                        )}
                        {(portfolio.expected_return * 100).toFixed(2)}%
                      </Box>
                    </TableCell>
                    <TableCell align="right">
                      {(portfolio.volatility * 100).toFixed(2)}%
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        size="small"
                        label={portfolio.sharpe_ratio.toFixed(3)}
                        color={portfolio.sharpe_ratio > 1 ? 'success' : portfolio.sharpe_ratio > 0.5 ? 'warning' : 'error'}
                      />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
    );
  };

  const renderAssetComposition = () => {
    if (!selectedPortfolio || !localShowAssetComposition) return null;

    const weightEntries = Object.entries(selectedPortfolio.weights)
      .sort(([, a], [, b]) => b - a)
      .filter(([, weight]) => weight > 0.001); // Filter out tiny positions

    return (
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Asset Composition - {selectedPortfolio.name}
          </Typography>
          <Box sx={{ mt: 2 }}>
            {weightEntries.map(([asset, weight], index) => (
              <Box key={asset} sx={{ mb: 1 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center">
                  <Typography variant="body2">{asset}</Typography>
                  <Typography variant="body2" fontWeight="bold">
                    {(weight * 100).toFixed(1)}%
                  </Typography>
                </Box>
                <Box
                  sx={{
                    height: 8,
                    backgroundColor: theme.palette.grey[200],
                    borderRadius: 4,
                    overflow: 'hidden'
                  }}
                >
                  <Box
                    sx={{
                      height: '100%',
                      width: `${weight * 100}%`,
                      backgroundColor: theme.palette.primary.main,
                      transition: 'width 0.3s ease'
                    }}
                  />
                </Box>
              </Box>
            ))}
          </Box>
        </CardContent>
      </Card>
    );
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
        <Grid item xs={12} md={6}>
          <Typography variant="h6">
            Efficient Frontier Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Risk-return optimization with {data.assets?.length || 0} assets
          </Typography>
        </Grid>
        <Grid item xs={12} md={6}>
          <Box display="flex" gap={2} justifyContent="flex-end" alignItems="center">
            <FormControlLabel
              control={
                <Switch
                  checked={showLabels}
                  onChange={(e) => setShowLabels(e.target.checked)}
                  size="small"
                />
              }
              label="Labels"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={localShowKeyPortfolios}
                  onChange={(e) => setLocalShowKeyPortfolios(e.target.checked)}
                  size="small"
                />
              }
              label="Key Portfolios"
            />
            <FormControlLabel
              control={
                <Switch
                  checked={localShowAssetComposition}
                  onChange={(e) => setLocalShowAssetComposition(e.target.checked)}
                  size="small"
                />
              }
              label="Composition"
            />
            <FormControl size="small" sx={{ minWidth: 120 }}>
              <InputLabel>View</InputLabel>
              <Select
                value={chartType}
                label="View"
                onChange={(e) => setChartType(e.target.value as 'frontier' | 'weights')}
              >
                <MenuItem value="frontier">
                  <ShowChart fontSize="small" sx={{ mr: 1 }} />
                  Frontier
                </MenuItem>
                <MenuItem value="weights">
                  <PieChart fontSize="small" sx={{ mr: 1 }} />
                  Weights
                </MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Box sx={{ height: height - 120 }}>
            <Scatter data={chartData} options={options} />
          </Box>
        </Grid>
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              {renderPortfolioMetrics()}
            </Grid>
            {selectedPortfolio && (
              <Grid item xs={12}>
                {renderAssetComposition()}
              </Grid>
            )}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Analysis Parameters
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Risk-free rate: {(data.risk_free_rate * 100).toFixed(2)}%
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Assets: {data.assets?.join(', ')}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Analysis date: {new Date(data.optimization_date).toLocaleDateString()}
                    </Typography>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default EfficientFrontierChart;
