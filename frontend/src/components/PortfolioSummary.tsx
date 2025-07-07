import React from 'react';
import { 
  Card, 
  CardContent, 
  Typography, 
  Box, 
  Chip,
  CircularProgress,
  Alert,
  Grid
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  AccountBalanceWallet,
  Assessment
} from '@mui/icons-material';

interface PortfolioSummaryProps {
  id: number;
  name: string;
  portfolioType: string;
  currentValue: number;
  totalReturn: number;
  totalReturnPercentage: number;
  assetCount: number;
  lastUpdated: string;
  loading?: boolean;
  error?: string;
}

const PortfolioSummary: React.FC<PortfolioSummaryProps> = ({
  id,
  name,
  portfolioType,
  currentValue,
  totalReturn,
  totalReturnPercentage,
  assetCount,
  lastUpdated,
  loading = false,
  error
}) => {
  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getPortfolioTypeColor = (type: string) => {
    const colors: { [key: string]: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' } = {
      'personal': 'primary',
      'retirement': 'secondary',
      'education': 'info',
      'investment': 'success',
      'trading': 'warning',
      'other': 'error'
    };
    return colors[type.toLowerCase()] || 'primary';
  };

  const isPositiveReturn = totalReturn >= 0;
  const ReturnIcon = isPositiveReturn ? TrendingUp : TrendingDown;

  if (loading) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card sx={{ height: '100%' }}>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%', transition: 'transform 0.2s', '&:hover': { transform: 'translateY(-2px)' } }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box>
            <Typography variant="h6" component="h2" gutterBottom>
              {name}
            </Typography>
            <Chip 
              label={portfolioType.toUpperCase()} 
              color={getPortfolioTypeColor(portfolioType)}
              size="small"
            />
          </Box>
          <AccountBalanceWallet color="action" />
        </Box>

        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Current Value
              </Typography>
              <Typography variant="h4" component="div" sx={{ fontWeight: 'bold' }}>
                {formatCurrency(currentValue)}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ mb: 2 }}>
              <Typography variant="body2" color="text.secondary">
                Total Return
              </Typography>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <ReturnIcon 
                  color={isPositiveReturn ? 'success' : 'error'}
                  sx={{ fontSize: 20 }}
                />
                <Typography 
                  variant="h6" 
                  component="div" 
                  sx={{ 
                    fontWeight: 'bold',
                    color: isPositiveReturn ? 'success.main' : 'error.main'
                  }}
                >
                  {formatCurrency(totalReturn)}
                </Typography>
              </Box>
              <Typography 
                variant="body2" 
                sx={{ 
                  color: isPositiveReturn ? 'success.main' : 'error.main',
                  fontWeight: 'medium'
                }}
              >
                {formatPercentage(totalReturnPercentage)}
              </Typography>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Assessment color="action" sx={{ fontSize: 20 }} />
              <Box>
                <Typography variant="body2" color="text.secondary">
                  Assets
                </Typography>
                <Typography variant="h6" component="div">
                  {assetCount}
                </Typography>
              </Box>
            </Box>
          </Grid>

          <Grid item xs={12} sm={6}>
            <Box>
              <Typography variant="body2" color="text.secondary">
                Last Updated
              </Typography>
              <Typography variant="body2" component="div">
                {formatDate(lastUpdated)}
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </CardContent>
    </Card>
  );
};

export default PortfolioSummary;
