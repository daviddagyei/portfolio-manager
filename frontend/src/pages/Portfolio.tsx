import React, { useState, useEffect } from 'react';
import {
  Typography,
  Grid,
  Box,
  Button,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Add as AddIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import {
  PortfolioSummary,
  PortfolioHoldingsTable,
  AssetAllocationChart,
  LoadingState,
  ErrorState,
  EmptyState
} from '../components';
import { portfolioService } from '../services';

interface PortfolioHolding {
  holding_id: number;
  asset_id: number;
  asset_symbol: string;
  asset_name: string;
  asset_type: string;
  sector: string;
  quantity: number;
  average_cost: number;
  current_price: number;
  market_value: number;
  unrealized_gain_loss: number;
  unrealized_gain_loss_percentage: number;
  last_updated: string;
}

const Portfolio: React.FC = () => {
  const [portfolios, setPortfolios] = useState<any[]>([]);
  const [selectedPortfolioId, setSelectedPortfolioId] = useState<number | ''>('');
  const [selectedPortfolio, setSelectedPortfolio] = useState<any>(null);
  const [holdings, setHoldings] = useState<PortfolioHolding[]>([]);
  const [allocationData, setAllocationData] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [holdingsLoading, setHoldingsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingHolding, setEditingHolding] = useState<PortfolioHolding | null>(null);
  const [portfolioToDelete, setPortfolioToDelete] = useState<number | null>(null);

  const fetchPortfolios = async () => {
    try {
      setError(null);
      const response = await portfolioService.getPortfolios({ userId: 1 });
      
      if (response.success && response.data) {
        setPortfolios(response.data);
        
        // Auto-select first portfolio if none selected
        if (response.data.length > 0 && !selectedPortfolioId) {
          setSelectedPortfolioId(response.data[0].id);
        }
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolios');
    } finally {
      setLoading(false);
    }
  };

  const fetchPortfolioDetails = async (portfolioId: number) => {
    try {
      setHoldingsLoading(true);
      
      // Get portfolio summary
      const summaryResponse = await portfolioService.getPortfolioSummary(portfolioId);
      if (summaryResponse.success) {
        setSelectedPortfolio(summaryResponse.data);
      }
      
      // Get holdings (mock data for now since API endpoint needs to be implemented)
      const mockHoldings: PortfolioHolding[] = [
        {
          holding_id: 1,
          asset_id: 1,
          asset_symbol: 'AAPL',
          asset_name: 'Apple Inc.',
          asset_type: 'stock',
          sector: 'Technology',
          quantity: 100,
          average_cost: 150.00,
          current_price: 175.00,
          market_value: 17500.00,
          unrealized_gain_loss: 2500.00,
          unrealized_gain_loss_percentage: 16.67,
          last_updated: new Date().toISOString()
        },
        {
          holding_id: 2,
          asset_id: 2,
          asset_symbol: 'GOOGL',
          asset_name: 'Alphabet Inc.',
          asset_type: 'stock',
          sector: 'Technology',
          quantity: 25,
          average_cost: 2800.00,
          current_price: 2900.00,
          market_value: 72500.00,
          unrealized_gain_loss: 2500.00,
          unrealized_gain_loss_percentage: 3.57,
          last_updated: new Date().toISOString()
        },
        {
          holding_id: 3,
          asset_id: 3,
          asset_symbol: 'SPY',
          asset_name: 'SPDR S&P 500 ETF',
          asset_type: 'etf',
          sector: 'Diversified',
          quantity: 200,
          average_cost: 400.00,
          current_price: 420.00,
          market_value: 84000.00,
          unrealized_gain_loss: 4000.00,
          unrealized_gain_loss_percentage: 5.00,
          last_updated: new Date().toISOString()
        }
      ];
      
      setHoldings(mockHoldings);
      
      // Generate allocation data by asset type
      const allocationMap = new Map<string, number>();
      mockHoldings.forEach(holding => {
        const type = holding.asset_type;
        allocationMap.set(type, (allocationMap.get(type) || 0) + holding.market_value);
      });
      
      const colors = ['#1976d2', '#dc004e', '#2e7d32', '#ed6c02', '#9c27b0'];
      const totalValue = mockHoldings.reduce((sum, h) => sum + h.market_value, 0);
      const allocation = Array.from(allocationMap.entries()).map(([type, value], index) => ({
        label: type.charAt(0).toUpperCase() + type.slice(1),
        value,
        percentage: totalValue > 0 ? (value / totalValue) * 100 : 0,
        color: colors[index % colors.length]
      }));
      
      setAllocationData(allocation);
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load portfolio details');
    } finally {
      setHoldingsLoading(false);
    }
  };

  useEffect(() => {
    fetchPortfolios();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedPortfolioId) {
      fetchPortfolioDetails(selectedPortfolioId as number);
    }
  }, [selectedPortfolioId]);

  const handleRefresh = () => {
    if (selectedPortfolioId) {
      fetchPortfolioDetails(selectedPortfolioId as number);
    }
  };

  const handleEditHolding = (holding: PortfolioHolding) => {
    setEditingHolding(holding);
    setEditDialogOpen(true);
  };

  const handleDeleteHolding = (holdingId: number) => {
    // Mock implementation
    setHoldings(holdings.filter(h => h.holding_id !== holdingId));
  };

  const handleDeletePortfolio = async () => {
    if (portfolioToDelete) {
      try {
        await portfolioService.deletePortfolio(portfolioToDelete);
        setPortfolios(portfolios.filter(p => p.id !== portfolioToDelete));
        
        if (selectedPortfolioId === portfolioToDelete) {
          setSelectedPortfolioId('');
          setSelectedPortfolio(null);
          setHoldings([]);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to delete portfolio');
      }
    }
    setDeleteDialogOpen(false);
    setPortfolioToDelete(null);
  };

  if (loading) {
    return <LoadingState message="Loading portfolios..." />;
  }

  if (error) {
    return (
      <ErrorState 
        message={error} 
        onRetry={() => {
          setLoading(true);
          fetchPortfolios();
        }}
      />
    );
  }

  if (portfolios.length === 0) {
    return (
      <EmptyState 
        message="No portfolios found"
        action={
          <Button variant="contained" startIcon={<AddIcon />}>
            Create Portfolio
          </Button>
        }
      />
    );
  }

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Portfolio Details
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Select Portfolio</InputLabel>
            <Select
              value={selectedPortfolioId}
              label="Select Portfolio"
              onChange={(e) => setSelectedPortfolioId(e.target.value as number)}
            >
              {portfolios.map((portfolio) => (
                <MenuItem key={portfolio.id} value={portfolio.id}>
                  {portfolio.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh Data">
            <IconButton onClick={handleRefresh} disabled={holdingsLoading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          
          {selectedPortfolioId && (
            <Tooltip title="Delete Portfolio">
              <IconButton 
                color="error"
                onClick={() => {
                  setPortfolioToDelete(selectedPortfolioId as number);
                  setDeleteDialogOpen(true);
                }}
              >
                <DeleteIcon />
              </IconButton>
            </Tooltip>
          )}
        </Box>
      </Box>

      {selectedPortfolio && (
        <Grid container spacing={3}>
          {/* Portfolio Summary */}
          <Grid item xs={12} md={8}>
            <PortfolioSummary
              id={selectedPortfolio.id}
              name={selectedPortfolio.name}
              portfolioType={selectedPortfolio.portfolioType}
              currentValue={selectedPortfolio.currentValue}
              totalReturn={selectedPortfolio.totalReturn}
              totalReturnPercentage={selectedPortfolio.totalReturnPercentage}
              assetCount={selectedPortfolio.assetCount}
              lastUpdated={selectedPortfolio.lastUpdated}
            />
          </Grid>

          {/* Asset Allocation */}
          <Grid item xs={12} md={4}>
            <AssetAllocationChart
              data={allocationData}
              title="Asset Allocation"
              height={300}
            />
          </Grid>

          {/* Holdings Table */}
          <Grid item xs={12}>
            <PortfolioHoldingsTable
              holdings={holdings}
              loading={holdingsLoading}
              error={error || undefined}
              onRefresh={handleRefresh}
              onEdit={handleEditHolding}
              onDelete={handleDeleteHolding}
            />
          </Grid>
        </Grid>
      )}

      {/* Edit Holding Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Edit Holding</DialogTitle>
        <DialogContent>
          {editingHolding && (
            <Box sx={{ pt: 2 }}>
              <TextField
                fullWidth
                label="Asset Symbol"
                value={editingHolding.asset_symbol}
                disabled
                margin="normal"
              />
              <TextField
                fullWidth
                label="Quantity"
                type="number"
                value={editingHolding.quantity}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Average Cost"
                type="number"
                value={editingHolding.average_cost}
                margin="normal"
              />
              <TextField
                fullWidth
                label="Current Price"
                type="number"
                value={editingHolding.current_price}
                margin="normal"
              />
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button variant="contained" onClick={() => setEditDialogOpen(false)}>
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>Delete Portfolio</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            This action cannot be undone. All holdings and transaction history will be permanently deleted.
          </Alert>
          <Typography>
            Are you sure you want to delete this portfolio?
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Cancel</Button>
          <Button color="error" variant="contained" onClick={handleDeletePortfolio}>
            Delete Portfolio
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Portfolio;
