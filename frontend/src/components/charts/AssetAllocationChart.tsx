/**
 * Asset Allocation Chart Component
 * Interactive pie/doughnut charts for portfolio allocation by sector, asset class, and individual holdings
 */

import React, { useMemo, useState } from 'react';
import { Pie, Doughnut, Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
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
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip
} from '@mui/material';
import { AllocationData } from '../../types/charts';

ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface AssetAllocationChartProps {
  holdings: AllocationData[];
  sectorAllocations?: AllocationData[];
  assetClassAllocations?: AllocationData[];
  loading?: boolean;
  error?: string;
  title?: string;
  height?: number;
  showTable?: boolean;
}

type AllocationView = 'holdings' | 'sector' | 'assetClass';
type ChartType = 'pie' | 'doughnut' | 'bar';

const AssetAllocationChart: React.FC<AssetAllocationChartProps> = ({
  holdings,
  sectorAllocations = [],
  assetClassAllocations = [],
  loading = false,
  error,
  title = 'Portfolio Allocation',
  height = 400,
  showTable = true
}) => {
  const theme = useTheme();
  const [allocationView, setAllocationView] = useState<AllocationView>('holdings');
  const [chartType, setChartType] = useState<ChartType>('doughnut');
  const [showTopN, setShowTopN] = useState<number>(10);

  // Color palette for allocations
  const colorPalette = [
    theme.palette.primary.main,
    theme.palette.secondary.main,
    theme.palette.success.main,
    theme.palette.warning.main,
    theme.palette.error.main,
    theme.palette.info.main,
    '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4',
    '#FECA57', '#FF9FF3', '#54A0FF', '#5F27CD',
    '#00D2D3', '#FF9F43', '#54A0FF', '#5F27CD',
    '#10AC84', '#EE5A24', '#0984E3', '#6C5CE7'
  ];

  const getCurrentData = (): AllocationData[] => {
    switch (allocationView) {
      case 'sector':
        return sectorAllocations;
      case 'assetClass':
        return assetClassAllocations;
      default:
        return holdings;
    }
  };

  const currentData = getCurrentData();
  const topData = currentData
    .sort((a, b) => b.weight - a.weight)
    .slice(0, showTopN);

  const chartData = useMemo(() => {
    const data = topData.length > 0 ? topData : currentData.slice(0, 10);
    
    return {
      labels: data.map(item => 
        allocationView === 'holdings' ? item.symbol : item.name
      ),
      datasets: [
        {
          data: data.map(item => item.weight * 100),
          backgroundColor: data.map((item, index) => 
            item.color || colorPalette[index % colorPalette.length]
          ),
          borderColor: data.map((item, index) => 
            item.color || colorPalette[index % colorPalette.length]
          ),
          borderWidth: 1,
          hoverBackgroundColor: data.map((item, index) => 
            `${item.color || colorPalette[index % colorPalette.length]}CC`
          ),
          hoverBorderWidth: 2
        }
      ]
    };
  }, [topData, currentData, allocationView, colorPalette]);

  const pieChartOptions: ChartOptions<'pie' | 'doughnut'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'right',
        labels: {
          usePointStyle: true,
          padding: 15,
          generateLabels: (chart) => {
            const data = chart.data;
            if (data.labels?.length && data.datasets?.length) {
              return data.labels.map((label, i) => {
                // Type guards for color arrays
                const bg = data.datasets[0].backgroundColor;
                const border = data.datasets[0].borderColor;
                const fillStyle = Array.isArray(bg) ? bg[i] : (typeof bg === 'string' ? bg : undefined);
                const strokeStyle = Array.isArray(border) ? border[i] : (typeof border === 'string' ? border : undefined);
                return {
                  text: `${label} (${data.datasets[0].data[i]}%)`,
                  fillStyle,
                  strokeStyle,
                  lineWidth: 1,
                  hidden: false,
                  index: i
                };
              });
            }
            return [];
          }
        }
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const label = context.label || '';
            const value = context.parsed;
            const total = context.dataset.data.reduce((sum: number, val: any) => sum + val, 0);
            const percentage = ((value / total) * 100).toFixed(2);
            return `${label}: ${percentage}% ($${(topData[context.dataIndex]?.value || 0).toLocaleString()})`;
          }
        }
      }
    },
    cutout: chartType === 'doughnut' ? '50%' : 0
  }), [chartType, topData]);

  const barChartOptions: ChartOptions<'bar'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    indexAxis: 'y',
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const value = context.parsed.x;
            const itemValue = topData[context.dataIndex]?.value || 0;
            return `${context.label}: ${value.toFixed(2)}% ($${itemValue.toLocaleString()})`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: 'Allocation (%)'
        },
        ticks: {
          callback: function(value) {
            return `${value}%`;
          }
        }
      },
      y: {
        title: {
          display: true,
          text: allocationView === 'holdings' ? 'Holdings' : 
                allocationView === 'sector' ? 'Sectors' : 'Asset Classes'
        }
      }
    }
  }), [allocationView, topData]);

  const totalValue = currentData.reduce((sum, item) => sum + item.value, 0);

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

  const ChartComponent = chartType === 'bar' ? Bar : 
                        chartType === 'pie' ? Pie : Doughnut;
  const chartOptions = chartType === 'bar' ? barChartOptions : pieChartOptions;

  return (
    <Paper sx={{ p: 3 }}>
      {/* Header and Controls */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs>
            <Typography variant="h6">{title}</Typography>
            <Typography variant="subtitle2" color="text.secondary">
              Total Portfolio Value: ${totalValue.toLocaleString()}
            </Typography>
          </Grid>
          <Grid item>
            <FormControl size="small" sx={{ minWidth: 100 }}>
              <InputLabel>Show Top</InputLabel>
              <Select
                value={showTopN}
                label="Show Top"
                onChange={(e) => setShowTopN(Number(e.target.value))}
              >
                <MenuItem value={5}>Top 5</MenuItem>
                <MenuItem value={10}>Top 10</MenuItem>
                <MenuItem value={15}>Top 15</MenuItem>
                <MenuItem value={20}>Top 20</MenuItem>
              </Select>
            </FormControl>
          </Grid>
        </Grid>
      </Box>

      {/* View Selection */}
      <Box sx={{ mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item>
            <Typography variant="subtitle2">View:</Typography>
            <ToggleButtonGroup
              value={allocationView}
              exclusive
              onChange={(_, newView) => newView && setAllocationView(newView)}
              size="small"
              sx={{ ml: 1 }}
            >
              <ToggleButton value="holdings">Holdings</ToggleButton>
              <ToggleButton value="sector" disabled={sectorAllocations.length === 0}>
                Sectors
              </ToggleButton>
              <ToggleButton value="assetClass" disabled={assetClassAllocations.length === 0}>
                Asset Classes
              </ToggleButton>
            </ToggleButtonGroup>
          </Grid>
          <Grid item>
            <Typography variant="subtitle2">Chart:</Typography>
            <ToggleButtonGroup
              value={chartType}
              exclusive
              onChange={(_, newType) => newType && setChartType(newType)}
              size="small"
              sx={{ ml: 1 }}
            >
              <ToggleButton value="pie">Pie</ToggleButton>
              <ToggleButton value="doughnut">Doughnut</ToggleButton>
              <ToggleButton value="bar">Bar</ToggleButton>
            </ToggleButtonGroup>
          </Grid>
        </Grid>
      </Box>

      {/* Chart and Table */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={showTable ? 8 : 12}>
          <Box sx={{ height: height - 150 }}>
            <ChartComponent data={chartData} options={chartOptions as any} />
          </Box>
        </Grid>

        {showTable && (
          <Grid item xs={12} md={4}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  {allocationView === 'holdings' ? 'Top Holdings' :
                   allocationView === 'sector' ? 'Sector Breakdown' : 'Asset Class Breakdown'}
                </Typography>
                <TableContainer sx={{ maxHeight: height - 200 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>
                          {allocationView === 'holdings' ? 'Symbol' : 'Name'}
                        </TableCell>
                        <TableCell align="right">Weight</TableCell>
                        <TableCell align="right">Value</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {topData.map((item, index) => (
                        <TableRow key={item.symbol || item.name}>
                          <TableCell>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                              <Box
                                sx={{
                                  width: 12,
                                  height: 12,
                                  borderRadius: '50%',
                                  backgroundColor: item.color || colorPalette[index % colorPalette.length]
                                }}
                              />
                              <Typography variant="body2">
                                {allocationView === 'holdings' ? item.symbol : item.name}
                              </Typography>
                            </Box>
                            {allocationView === 'holdings' && (
                              <Typography variant="caption" color="text.secondary">
                                {item.name}
                              </Typography>
                            )}
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              {(item.weight * 100).toFixed(2)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography variant="body2">
                              ${item.value.toLocaleString()}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>

                {currentData.length > showTopN && (
                  <Box sx={{ mt: 2, textAlign: 'center' }}>
                    <Typography variant="caption" color="text.secondary">
                      Showing top {showTopN} of {currentData.length} items
                    </Typography>
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>

      {/* Summary Cards */}
      <Grid container spacing={2} sx={{ mt: 2 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Number of {allocationView === 'holdings' ? 'Holdings' : 
                          allocationView === 'sector' ? 'Sectors' : 'Asset Classes'}
              </Typography>
              <Typography variant="h6">
                {currentData.length}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Largest Position
              </Typography>
              <Typography variant="h6">
                {currentData.length > 0 ? (currentData[0].weight * 100).toFixed(2) : '0.00'}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Top 5 Concentration
              </Typography>
              <Typography variant="h6">
                {currentData.slice(0, 5).reduce((sum, item) => sum + item.weight, 0) * 100}%
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="body2" color="text.secondary">
                Diversification
              </Typography>
              <Chip
                label={currentData.length > 20 ? 'High' : currentData.length > 10 ? 'Medium' : 'Low'}
                color={currentData.length > 20 ? 'success' : currentData.length > 10 ? 'warning' : 'error'}
                size="small"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default AssetAllocationChart;
