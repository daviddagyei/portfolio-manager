import React, { useState, useEffect } from 'react';
import {
  Typography,
  Grid,
  Box,
  Button,
  Card,
  CardContent,
  IconButton,
  Tooltip,
  Fab
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  Upload as UploadIcon,
  TrendingUp,
  AccountBalanceWallet,
  ShowChart,
  PieChart
} from '@mui/icons-material';
import {
  PortfolioSummary,
  AssetAllocationChart,
  PortfolioImportDialog,
  LoadingState,
  ErrorState,
  EmptyState
} from '../components';
import { portfolioService } from '../services';

interface DashboardMetrics {
  totalPortfolios: number;
  totalValue: number;
  totalReturn: number;
  totalReturnPercentage: number;
  portfolios: any[];
}

interface AllocationData {
  label: string;
  value: number;
  percentage: number;
  color: string;
}

const Dashboard: React.FC = () => {
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [allocationData, setAllocationData] = useState<AllocationData[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [importDialogOpen, setImportDialogOpen] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchDashboardData = async () => {
    try {
      setError(null);
      
      // Fetch all portfolios (using user_id = 1 for now)
      const portfoliosResponse = await portfolioService.getPortfolios({ userId: 1 });
      
      if (portfoliosResponse.success && portfoliosResponse.data) {
        const portfolios = portfoliosResponse.data;
        
        // Calculate metrics
        const totalValue = portfolios.reduce((sum, p) => sum + p.currentValue, 0);
        const totalReturn = portfolios.reduce((sum, p) => sum + p.totalReturn, 0);
        const totalInitialValue = portfolios.reduce((sum, p) => sum + p.initialValue, 0);
        const totalReturnPercentage = totalInitialValue > 0 ? (totalReturn / totalInitialValue) * 100 : 0;
        
        const dashboardMetrics: DashboardMetrics = {
          totalPortfolios: portfolios.length,
          totalValue,
          totalReturn,
          totalReturnPercentage,
          portfolios
        };
        
        setMetrics(dashboardMetrics);
        
        // Generate allocation data by portfolio type
        const allocationMap = new Map<string, number>();
        portfolios.forEach(portfolio => {
          const type = portfolio.portfolioType || 'other';
          allocationMap.set(type, (allocationMap.get(type) || 0) + portfolio.currentValue);
        });
        
        const colors = ['#1976d2', '#dc004e', '#2e7d32', '#ed6c02', '#9c27b0', '#00acc1'];
        const allocation = Array.from(allocationMap.entries()).map(([type, value], index) => ({
          label: type.charAt(0).toUpperCase() + type.slice(1),
          value,
          percentage: totalValue > 0 ? (value / totalValue) * 100 : 0,
          color: colors[index % colors.length]
        }));
        
        setAllocationData(allocation);
      } else {
        throw new Error('Failed to fetch portfolios');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchDashboardData();
  };

  const handleImportPortfolio = async (importData: any) => {
    try {
      // Create portfolio first
      const portfolioResponse = await portfolioService.createPortfolio(importData.portfolio);
      
      if (portfolioResponse.success) {
        // Here you would typically add the holdings to the portfolio
        // For now, we'll just refresh the dashboard
        await fetchDashboardData();
        setImportDialogOpen(false);
      } else {
        throw new Error('Failed to create portfolio');
      }
    } catch (err) {
      throw err; // Re-throw to be handled by the import dialog
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const formatPercentage = (percentage: number) => {
    return `${percentage >= 0 ? '+' : ''}${percentage.toFixed(2)}%`;
  };

  if (loading) {
    return <LoadingState message="Loading dashboard..." />;
  }

  if (error) {
    return (
      <ErrorState 
        message={error} 
        onRetry={() => {
          setLoading(true);
          fetchDashboardData();
        }}
      />
    );
  }

  if (!metrics) {
    return (
      <EmptyState 
        message="No data available"
        action={
          <Button 
            variant="contained" 
            startIcon={<AddIcon />}
            onClick={() => setImportDialogOpen(true)}
          >
            Import Portfolio
          </Button>
        }
      />
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={refreshing}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="outlined"
            startIcon={<UploadIcon />}
            onClick={() => setImportDialogOpen(true)}
          >
            Import Portfolio
          </Button>
        </Box>
      </Box>

      {/* Summary Cards */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <AccountBalanceWallet color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h6" component="div">
                    {metrics.totalPortfolios}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Portfolios
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <ShowChart color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography variant="h6" component="div">
                    {formatCurrency(metrics.totalValue)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Value
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <TrendingUp 
                  color={metrics.totalReturn >= 0 ? 'success' : 'error'} 
                  sx={{ fontSize: 40 }} 
                />
                <Box>
                  <Typography 
                    variant="h6" 
                    component="div"
                    sx={{ 
                      color: metrics.totalReturn >= 0 ? 'success.main' : 'error.main'
                    }}
                  >
                    {formatCurrency(metrics.totalReturn)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Return
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                <PieChart color="primary" sx={{ fontSize: 40 }} />
                <Box>
                  <Typography 
                    variant="h6" 
                    component="div"
                    sx={{ 
                      color: metrics.totalReturnPercentage >= 0 ? 'success.main' : 'error.main'
                    }}
                  >
                    {formatPercentage(metrics.totalReturnPercentage)}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Return %
                  </Typography>
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        {/* Portfolio Summaries */}
        <Grid item xs={12} lg={8}>
          <Typography variant="h6" component="h2" gutterBottom>
            Portfolio Overview
          </Typography>
          
          {metrics.portfolios.length === 0 ? (
            <EmptyState 
              message="No portfolios found"
              action={
                <Button 
                  variant="contained" 
                  startIcon={<AddIcon />}
                  onClick={() => setImportDialogOpen(true)}
                >
                  Import Your First Portfolio
                </Button>
              }
            />
          ) : (
            <Grid container spacing={2}>
              {metrics.portfolios.map((portfolio) => (
                <Grid item xs={12} md={6} key={portfolio.id}>
                  <PortfolioSummary
                    id={portfolio.id}
                    name={portfolio.name}
                    portfolioType={portfolio.portfolioType}
                    currentValue={portfolio.currentValue}
                    totalReturn={portfolio.totalReturn}
                    totalReturnPercentage={portfolio.totalReturnPercentage}
                    assetCount={0} // Will be populated when we have holdings
                    lastUpdated={portfolio.updatedAt || portfolio.createdAt}
                  />
                </Grid>
              ))}
            </Grid>
          )}
        </Grid>

        {/* Asset Allocation */}
        <Grid item xs={12} lg={4}>
          <AssetAllocationChart
            data={allocationData}
            title="Portfolio Allocation"
            height={400}
          />
        </Grid>
      </Grid>

      {/* Import Dialog */}
      <PortfolioImportDialog
        open={importDialogOpen}
        onClose={() => setImportDialogOpen(false)}
        onImport={handleImportPortfolio}
      />

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add"
        sx={{
          position: 'fixed',
          bottom: 16,
          right: 16,
        }}
        onClick={() => setImportDialogOpen(true)}
      >
        <AddIcon />
      </Fab>
    </Box>
  );
};

export default Dashboard;
