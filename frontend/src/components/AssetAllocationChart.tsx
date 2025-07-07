import React from 'react';
import { Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  Title
} from 'chart.js';
import {
  Paper,
  Typography,
  Box,
  Grid,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  CircularProgress,
  Alert,
  useTheme
} from '@mui/material';
import { Circle } from '@mui/icons-material';

ChartJS.register(ArcElement, Tooltip, Legend, Title);

interface AllocationData {
  label: string;
  value: number;
  percentage: number;
  color: string;
}

interface AssetAllocationChartProps {
  data: AllocationData[];
  loading?: boolean;
  error?: string;
  title?: string;
  height?: number;
}

const AssetAllocationChart: React.FC<AssetAllocationChartProps> = ({
  data,
  loading = false,
  error,
  title = 'Asset Allocation',
  height = 400
}) => {
  const theme = useTheme();

  // Generate colors for the chart
  const generateColors = (count: number) => {
    const colors = [
      theme.palette.primary.main,
      theme.palette.secondary.main,
      theme.palette.success.main,
      theme.palette.warning.main,
      theme.palette.error.main,
      theme.palette.info.main,
      '#FF6384',
      '#36A2EB',
      '#FFCE56',
      '#4BC0C0',
      '#9966FF',
      '#FF9F40'
    ];
    
    // If we need more colors, generate them
    while (colors.length < count) {
      colors.push(`hsl(${Math.random() * 360}, 70%, 50%)`);
    }
    
    return colors.slice(0, count);
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  if (loading) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Typography variant="h6" component="h2" gutterBottom>
          {title}
        </Typography>
        <Box display="flex" justifyContent="center" alignItems="center" height="80%">
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Typography variant="h6" component="h2" gutterBottom>
          {title}
        </Typography>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (!data || data.length === 0) {
    return (
      <Paper sx={{ p: 3, height }}>
        <Typography variant="h6" component="h2" gutterBottom>
          {title}
        </Typography>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          No allocation data available.
        </Typography>
      </Paper>
    );
  }

  // Assign colors to data if not provided
  const colors = generateColors(data.length);
  const dataWithColors = data.map((item, index) => ({
    ...item,
    color: item.color || colors[index]
  }));

  const chartData = {
    labels: dataWithColors.map(item => item.label),
    datasets: [
      {
        data: dataWithColors.map(item => item.value),
        backgroundColor: dataWithColors.map(item => item.color),
        borderColor: dataWithColors.map(item => item.color),
        borderWidth: 2,
        hoverBorderWidth: 3,
        hoverBorderColor: theme.palette.common.white
      }
    ]
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        display: false // We'll create our own legend
      },
      tooltip: {
        callbacks: {
          label: (context: any) => {
            const value = context.parsed;
            const percentage = ((value / dataWithColors.reduce((sum, item) => sum + item.value, 0)) * 100).toFixed(1);
            return `${context.label}: ${formatCurrency(value)} (${percentage}%)`;
          }
        }
      }
    },
    animation: {
      animateScale: true,
      animateRotate: true
    }
  };

  return (
    <Paper sx={{ p: 3, height }}>
      <Typography variant="h6" component="h2" gutterBottom>
        {title}
      </Typography>
      
      <Grid container spacing={2} sx={{ height: 'calc(100% - 40px)' }}>
        <Grid item xs={12} md={8}>
          <Box sx={{ height: '100%', minHeight: 250 }}>
            <Pie data={chartData} options={options} />
          </Box>
        </Grid>
        
        <Grid item xs={12} md={4}>
          <Box sx={{ height: '100%', overflow: 'auto' }}>
            <Typography variant="subtitle2" gutterBottom>
              Allocation Breakdown
            </Typography>
            <List dense>
              {dataWithColors.map((item, index) => (
                <ListItem key={index} sx={{ py: 0.5 }}>
                  <ListItemIcon sx={{ minWidth: 24 }}>
                    <Circle sx={{ color: item.color, fontSize: 12 }} />
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Typography variant="body2" noWrap>
                        {item.label}
                      </Typography>
                    }
                    secondary={
                      <Box>
                        <Typography variant="caption" color="text.secondary">
                          {formatCurrency(item.value)}
                        </Typography>
                        <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                          ({item.percentage.toFixed(1)}%)
                        </Typography>
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          </Box>
        </Grid>
      </Grid>
    </Paper>
  );
};

export default AssetAllocationChart;
