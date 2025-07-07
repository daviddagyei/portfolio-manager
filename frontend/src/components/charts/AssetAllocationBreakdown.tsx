/**
 * Asset Allocation Breakdown Chart
 * Multiple visualization types for portfolio allocation analysis
 */

import React, { useMemo } from 'react';
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
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  Card,
  CardContent,
  useTheme
} from '@mui/material';
import { Circle } from '@mui/icons-material';

ChartJS.register(
  ArcElement,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

interface AllocationItem {
  label: string;
  value: number;
  percentage: number;
  color?: string;
  category?: string;
  subItems?: AllocationItem[];
}

interface AssetAllocationData {
  byAsset: AllocationItem[];
  bySector: AllocationItem[];
  byAssetClass: AllocationItem[];
  byGeography?: AllocationItem[];
  byMarketCap?: AllocationItem[];
}

interface AssetAllocationBreakdownProps {
  data: AssetAllocationData;
  loading?: boolean;
  error?: string;
  height?: number;
  chartType?: 'pie' | 'doughnut' | 'bar';
  viewType?: 'byAsset' | 'bySector' | 'byAssetClass' | 'byGeography' | 'byMarketCap';
  showLegend?: boolean;
  showLabels?: boolean;
  onViewChange?: (view: string) => void;
  onChartTypeChange?: (type: 'pie' | 'doughnut' | 'bar') => void;
}

const generateColors = (count: number): string[] => {
  const baseColors = [
    '#1976d2', '#d32f2f', '#388e3c', '#f57c00', '#7b1fa2',
    '#303f9f', '#c2185b', '#00796b', '#455a64', '#512da8',
    '#5d4037', '#616161', '#e64a19', '#00acc1', '#689f38'
  ];
  
  const colors = [];
  for (let i = 0; i < count; i++) {
    if (i < baseColors.length) {
      colors.push(baseColors[i]);
    } else {
      // Generate additional colors
      const hue = (i * 137.508) % 360; // Golden angle approximation
      colors.push(`hsl(${hue}, 70%, 50%)`);
    }
  }
  return colors;
};

const AssetAllocationBreakdown: React.FC<AssetAllocationBreakdownProps> = ({
  data,
  loading = false,
  error,
  height = 400,
  chartType = 'doughnut',
  viewType = 'byAsset',
  showLegend = true,
  showLabels = true,
  onViewChange,
  onChartTypeChange
}) => {
  const theme = useTheme();

  const currentData = useMemo(() => {
    return data[viewType] || [];
  }, [data, viewType]);

  const chartData = useMemo(() => {
    if (!currentData || currentData.length === 0) {
      return { labels: [], datasets: [] };
    }

    // Always generate colors if not present
    const colors = currentData.map((item, idx) => item.color || generateColors(currentData.length)[idx]);
    
    return {
      labels: currentData.map(item => item.label),
      datasets: [{
        data: currentData.map(item => item.value),
        backgroundColor: colors,
        borderColor: colors,
        borderWidth: chartType === 'bar' ? 0 : 2,
        hoverBorderWidth: chartType === 'bar' ? 0 : 3
      }]
    };
  }, [currentData, chartType]);

  const pieOptions: ChartOptions<'pie' | 'doughnut'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: showLegend,
        position: 'right' as const,
        labels: {
          usePointStyle: true,
          padding: 20,
          generateLabels: (chart) => {
            const data = chart.data;
            if (data.labels?.length && data.datasets.length) {
              return data.labels.map((label, i) => {
                // Defensive: fallback to 0 if data missing
                const value = data.datasets[0].data?.[i] ?? 0;
                const percentage = currentData[i]?.percentage ?? 0;
                // Type guards for color arrays
                const bg = data.datasets[0].backgroundColor;
                const border = data.datasets[0].borderColor;
                const fillStyle = Array.isArray(bg) ? bg[i] : (typeof bg === 'string' ? bg : undefined);
                const strokeStyle = Array.isArray(border) ? border[i] : (typeof border === 'string' ? border : undefined);
                return {
                  text: `${label}: ${percentage.toFixed(1)}%`,
                  fillStyle,
                  strokeStyle,
                  lineWidth: 2,
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
            const item = currentData[context.dataIndex] || { value: 0, percentage: 0 };
            return `${context.label}: $${item.value?.toLocaleString?.() ?? 0} (${item.percentage?.toFixed?.(1) ?? '0.0'}%)`;
          }
        }
      }
    }
  }), [showLegend, currentData]);

  const barOptions: ChartOptions<'bar'> = useMemo(() => ({
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false
      },
      tooltip: {
        callbacks: {
          label: (context) => {
            const item = currentData[context.dataIndex];
            return `${context.label}: $${item.value.toLocaleString()} (${item.percentage.toFixed(1)}%)`;
          }
        }
      }
    },
    scales: {
      x: {
        title: {
          display: true,
          text: viewType.replace('by', '').replace(/([A-Z])/g, ' $1').trim()
        }
      },
      y: {
        title: {
          display: true,
          text: 'Value ($)'
        },
        ticks: {
          callback: function(value) {
            return `$${Number(value).toLocaleString()}`;
          }
        }
      }
    }
  }), [currentData, viewType]);

  const viewOptions = [
    { value: 'byAsset', label: 'By Asset' },
    { value: 'bySector', label: 'By Sector' },
    { value: 'byAssetClass', label: 'By Asset Class' },
    { value: 'byGeography', label: 'By Geography' },
    { value: 'byMarketCap', label: 'By Market Cap' }
  ].filter(option => data[option.value as keyof AssetAllocationData]);

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

  const renderChart = () => {
    switch (chartType) {
      case 'pie':
        return <Pie data={chartData} options={pieOptions} />;
      case 'doughnut':
        return <Doughnut data={chartData} options={pieOptions} />;
      case 'bar':
        return <Bar data={chartData} options={barOptions} />;
      default:
        return <Doughnut data={chartData} options={pieOptions} />;
    }
  };

  return (
    <Paper sx={{ p: 3 }}>
      <Grid container spacing={2} sx={{ mb: 2 }}>
        <Grid item xs={12} md={6}>
          <Typography variant="h6">
            Portfolio Allocation Analysis
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Total Value: ${totalValue.toLocaleString()}
          </Typography>
        </Grid>
        <Grid item xs={12} md={3}>
          {onViewChange && (
            <FormControl fullWidth size="small">
              <InputLabel>View</InputLabel>
              <Select
                value={viewType}
                label="View"
                onChange={(e) => onViewChange(e.target.value)}
              >
                {viewOptions.map(option => (
                  <MenuItem key={option.value} value={option.value}>
                    {option.label}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
        </Grid>
        <Grid item xs={12} md={3}>
          {onChartTypeChange && (
            <FormControl fullWidth size="small">
              <InputLabel>Chart Type</InputLabel>
              <Select
                value={chartType}
                label="Chart Type"
                onChange={(e) => onChartTypeChange(e.target.value as any)}
              >
                <MenuItem value="doughnut">Doughnut</MenuItem>
                <MenuItem value="pie">Pie</MenuItem>
                <MenuItem value="bar">Bar</MenuItem>
              </Select>
            </FormControl>
          )}
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Box sx={{ height: height - 120 }}>
            {renderChart()}
          </Box>
        </Grid>
        <Grid item xs={12} md={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Breakdown
              </Typography>
              <List dense>
                {currentData.slice(0, 10).map((item, index) => (
                  <ListItem key={index} sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 24 }}>
                      <Circle 
                        sx={{ 
                          fontSize: 12, 
                          color: item.color || generateColors(currentData.length)[index] 
                        }} 
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                          <Typography variant="body2" noWrap sx={{ maxWidth: '60%' }}>
                            {item.label}
                          </Typography>
                          <Chip
                            label={`${item.percentage.toFixed(1)}%`}
                            size="small"
                            variant="outlined"
                          />
                        </Box>
                      }
                      secondary={`$${item.value.toLocaleString()}`}
                    />
                  </ListItem>
                ))}
                {currentData.length > 10 && (
                  <ListItem sx={{ px: 0 }}>
                    <Typography variant="body2" color="text.secondary">
                      ... and {currentData.length - 10} more
                    </Typography>
                  </ListItem>
                )}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default AssetAllocationBreakdown;
