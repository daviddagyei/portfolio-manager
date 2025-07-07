/**
 * Portfolio Rebalancing Component
 * Generate and display rebalancing suggestions with trade recommendations
 */

import React, { useState, useEffect } from 'react';
import {
  Paper,
  Typography,
  Box,
  Grid,
  Card,
  CardContent,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  CircularProgress,
  Alert,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Slider,
  Switch,
  FormControlLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  useTheme,
  Tooltip,
  IconButton
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  SwapHoriz,
  Assessment,
  Refresh,
  Info,
  CheckCircle,
  Warning,
  Error as ErrorIcon
} from '@mui/icons-material';

import { optimizationService, RebalancingResponse, TradeRecommendation } from '../services/optimizationService';
import portfolioService from '../services/portfolioService';
import { Portfolio as PortfolioType } from '../types/portfolio';

interface RebalancingComponentProps {
  portfolioId?: number;
  onRebalancingComplete?: (result: RebalancingResponse) => void;
}

const PortfolioRebalancing: React.FC<RebalancingComponentProps> = ({
  portfolioId: initialPortfolioId,
  onRebalancingComplete
}) => {
  const theme = useTheme();
  
  // State management
  const [portfolios, setPortfolios] = useState<PortfolioType[]>([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState<number | null>(initialPortfolioId || null);
  const [targetWeights, setTargetWeights] = useState<Record<string, number>>({});
  const [tolerance, setTolerance] = useState<number>(0.05);
  const [rebalancingResult, setRebalancingResult] = useState<RebalancingResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [currentAllocation, setCurrentAllocation] = useState<any>(null);
  const [showTradeDialog, setShowTradeDialog] = useState<boolean>(false);
  const [selectedTrade, setSelectedTrade] = useState<TradeRecommendation | null>(null);

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      loadCurrentAllocation();
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      const response = await portfolioService.getPortfolios();
      setPortfolios(response.data);
    } catch (err) {
      console.error('Failed to load portfolios:', err);
    }
  };

  const loadCurrentAllocation = async () => {
    if (!selectedPortfolio) return;
    
    try {
      const allocation = await optimizationService.getCurrentPortfolioAllocation(selectedPortfolio);
      setCurrentAllocation(allocation);
      
      // Initialize target weights with current weights
      setTargetWeights(allocation.current_weights);
    } catch (err) {
      console.error('Failed to load current allocation:', err);
      setError('Failed to load current portfolio allocation');
    }
  };

  const generateRebalancingSuggestions = async () => {
    if (!selectedPortfolio) return;
    
    setLoading(true);
    setError(null);
    
    try {
      const request = {
        portfolio_id: selectedPortfolio,
        target_weights: targetWeights,
        tolerance: tolerance
      };
      
      const result = await optimizationService.generateRebalancingSuggestions(request);
      
      if (result.success && result.data) {
        setRebalancingResult(result.data);
        onRebalancingComplete?.(result.data);
      } else {
        setError(result.error?.message || 'Failed to generate rebalancing suggestions');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Rebalancing analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const updateTargetWeight = (symbol: string, weight: number) => {
    setTargetWeights(prev => ({
      ...prev,
      [symbol]: weight / 100 // Convert percentage to decimal
    }));
  };

  const normalizeWeights = () => {
    const totalWeight = Object.values(targetWeights).reduce((sum, weight) => sum + weight, 0);
    
    if (totalWeight > 0) {
      const normalizedWeights = Object.fromEntries(
        Object.entries(targetWeights).map(([symbol, weight]) => [
          symbol,
          weight / totalWeight
        ])
      );
      setTargetWeights(normalizedWeights);
    }
  };

  const resetToCurrentWeights = () => {
    if (currentAllocation) {
      setTargetWeights(currentAllocation.current_weights);
    }
  };

  const getTradeTypeColor = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy':
        return 'success';
      case 'sell':
        return 'error';
      default:
        return 'default';
    }
  };

  const getTradeTypeIcon = (action: string) => {
    switch (action.toLowerCase()) {
      case 'buy':
        return <TrendingUp />;
      case 'sell':
        return <TrendingDown />;
      default:
        return <SwapHoriz />;
    }
  };

  const renderPortfolioSelector = () => (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portfolio Selection
        </Typography>
        
        <FormControl fullWidth>
          <InputLabel>Select Portfolio</InputLabel>
          <Select
            value={selectedPortfolio || ''}
            label="Select Portfolio"
            onChange={(e) => setSelectedPortfolio(Number(e.target.value))}
          >
            {portfolios.map((portfolio) => (
              <MenuItem key={portfolio.id} value={portfolio.id}>
                <Box>
                  <Typography variant="body1">{portfolio.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    Value: ${portfolio.currentValue.toLocaleString()}
                  </Typography>
                </Box>
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </CardContent>
    </Card>
  );

  const renderAllocationEditor = () => {
    if (!currentAllocation) return null;

    const symbols = Object.keys(currentAllocation.current_weights);
    const totalTargetWeight = Object.values(targetWeights).reduce((sum, weight) => sum + weight, 0);

    return (
      <Card variant="outlined">
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Target Allocation
            </Typography>
            <Box display="flex" gap={1}>
              <Button
                size="small"
                onClick={resetToCurrentWeights}
                startIcon={<Refresh />}
              >
                Reset
              </Button>
              <Button
                size="small"
                onClick={normalizeWeights}
                disabled={Math.abs(totalTargetWeight - 1) < 0.001}
              >
                Normalize
              </Button>
            </Box>
          </Box>

          {Math.abs(totalTargetWeight - 1) > 0.01 && (
            <Alert severity="warning" sx={{ mb: 2 }}>
              Target weights sum to {(totalTargetWeight * 100).toFixed(1)}%. 
              Consider normalizing or adjusting weights.
            </Alert>
          )}

          <Grid container spacing={2}>
            {symbols.map((symbol) => {
              const currentWeight = currentAllocation.current_weights[symbol] * 100;
              const targetWeight = (targetWeights[symbol] || 0) * 100;
              const difference = targetWeight - currentWeight;

              return (
                <Grid item xs={12} key={symbol}>
                  <Box mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                      <Typography variant="subtitle2">{symbol}</Typography>
                      <Box display="flex" alignItems="center" gap={1}>
                        <Typography variant="caption" color="text.secondary">
                          Current: {currentWeight.toFixed(1)}%
                        </Typography>
                        {Math.abs(difference) > tolerance * 100 && (
                          <Chip
                            size="small"
                            label={`${difference > 0 ? '+' : ''}${difference.toFixed(1)}%`}
                            color={Math.abs(difference) > tolerance * 100 ? 'warning' : 'default'}
                          />
                        )}
                      </Box>
                    </Box>
                    
                    <Slider
                      value={targetWeight}
                      onChange={(_, value) => updateTargetWeight(symbol, value as number)}
                      min={0}
                      max={100}
                      step={0.1}
                      marks={[
                        { value: 0, label: '0%' },
                        { value: currentWeight, label: `${currentWeight.toFixed(1)}%` },
                        { value: 100, label: '100%' }
                      ]}
                      valueLabelDisplay="auto"
                      valueLabelFormat={(value) => `${value.toFixed(1)}%`}
                    />
                    
                    <TextField
                      size="small"
                      type="number"
                      value={targetWeight.toFixed(1)}
                      onChange={(e) => updateTargetWeight(symbol, Number(e.target.value))}
                      inputProps={{ min: 0, max: 100, step: 0.1 }}
                      sx={{ width: 80, mt: 1 }}
                      InputProps={{
                        endAdornment: '%'
                      }}
                    />
                  </Box>
                </Grid>
              );
            })}
          </Grid>

          <Divider sx={{ my: 2 }} />

          <Box>
            <Typography variant="subtitle2" gutterBottom>
              Rebalancing Tolerance
            </Typography>
            <Box display="flex" alignItems="center" gap={2}>
              <Slider
                value={tolerance * 100}
                onChange={(_, value) => setTolerance((value as number) / 100)}
                min={1}
                max={20}
                step={0.5}
                marks={[
                  { value: 1, label: '1%' },
                  { value: 5, label: '5%' },
                  { value: 10, label: '10%' },
                  { value: 20, label: '20%' }
                ]}
                valueLabelDisplay="auto"
                valueLabelFormat={(value) => `${value.toFixed(1)}%`}
                sx={{ flexGrow: 1 }}
              />
              <TextField
                size="small"
                type="number"
                value={(tolerance * 100).toFixed(1)}
                onChange={(e) => setTolerance(Number(e.target.value) / 100)}
                inputProps={{ min: 0.1, max: 20, step: 0.1 }}
                sx={{ width: 80 }}
                InputProps={{
                  endAdornment: '%'
                }}
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              Minimum weight difference to trigger rebalancing
            </Typography>
          </Box>
        </CardContent>
      </Card>
    );
  };

  const renderRebalancingResults = () => {
    if (!rebalancingResult) return null;

    return (
      <Card variant="outlined">
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Rebalancing Analysis
            </Typography>
            <Chip
              icon={rebalancingResult.rebalancing_needed ? <Warning /> : <CheckCircle />}
              label={rebalancingResult.rebalancing_needed ? 'Rebalancing Needed' : 'No Rebalancing Needed'}
              color={rebalancingResult.rebalancing_needed ? 'warning' : 'success'}
            />
          </Box>

          <Grid container spacing={2} sx={{ mb: 3 }}>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Portfolio Value
              </Typography>
              <Typography variant="h6">
                ${rebalancingResult.total_portfolio_value.toLocaleString()}
              </Typography>
            </Grid>
            <Grid item xs={12} sm={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Number of Trades
              </Typography>
              <Typography variant="h6">
                {rebalancingResult.trades.length}
              </Typography>
            </Grid>
          </Grid>

          {rebalancingResult.trades.length > 0 && (
            <>
              <Typography variant="subtitle1" gutterBottom>
                Trade Recommendations
              </Typography>
              
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Asset</TableCell>
                      <TableCell>Action</TableCell>
                      <TableCell align="right">Current %</TableCell>
                      <TableCell align="right">Target %</TableCell>
                      <TableCell align="right">Difference</TableCell>
                      <TableCell align="right">Dollar Amount</TableCell>
                      <TableCell align="right">Shares</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {rebalancingResult.trades.map((trade: TradeRecommendation, index: number) => (
                      <TableRow
                        key={index}
                        hover
                        onClick={() => {
                          setSelectedTrade(trade);
                          setShowTradeDialog(true);
                        }}
                        sx={{ cursor: 'pointer' }}
                      >
                        <TableCell>
                          <Typography variant="body2" fontWeight="bold">
                            {trade.symbol}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            icon={getTradeTypeIcon(trade.action)}
                            label={trade.action.toUpperCase()}
                            color={getTradeTypeColor(trade.action)}
                          />
                        </TableCell>
                        <TableCell align="right">
                          {(trade.current_weight * 100).toFixed(1)}%
                        </TableCell>
                        <TableCell align="right">
                          {(trade.target_weight * 100).toFixed(1)}%
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            color={trade.weight_difference > 0 ? 'success.main' : 'error.main'}
                          >
                            {trade.weight_difference > 0 ? '+' : ''}
                            {(trade.weight_difference * 100).toFixed(1)}%
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            color={trade.dollar_amount > 0 ? 'success.main' : 'error.main'}
                          >
                            ${Math.abs(trade.dollar_amount).toLocaleString()}
                          </Typography>
                        </TableCell>
                        <TableCell align="right">
                          <Typography
                            variant="body2"
                            color={trade.shares_to_trade > 0 ? 'success.main' : 'error.main'}
                          >
                            {Math.abs(trade.shares_to_trade).toFixed(0)}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </>
          )}
        </CardContent>
      </Card>
    );
  };

  const renderTradeDialog = () => (
    <Dialog
      open={showTradeDialog}
      onClose={() => setShowTradeDialog(false)}
      maxWidth="sm"
      fullWidth
    >
      <DialogTitle>
        Trade Details - {selectedTrade?.symbol}
      </DialogTitle>
      <DialogContent>
        {selectedTrade && (
          <Grid container spacing={2}>
            <Grid item xs={12}>
              <Box display="flex" justifyContent="center" mb={2}>
                <Chip
                  size="medium"
                  icon={getTradeTypeIcon(selectedTrade.action)}
                  label={`${selectedTrade.action.toUpperCase()} ${selectedTrade.symbol}`}
                  color={getTradeTypeColor(selectedTrade.action)}
                />
              </Box>
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Current Weight
              </Typography>
              <Typography variant="h6">
                {(selectedTrade.current_weight * 100).toFixed(2)}%
              </Typography>
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Target Weight
              </Typography>
              <Typography variant="h6">
                {(selectedTrade.target_weight * 100).toFixed(2)}%
              </Typography>
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Current Price
              </Typography>
              <Typography variant="h6">
                ${selectedTrade.current_price.toFixed(2)}
              </Typography>
            </Grid>
            
            <Grid item xs={6}>
              <Typography variant="subtitle2" color="text.secondary">
                Shares to Trade
              </Typography>
              <Typography variant="h6" color={selectedTrade.shares_to_trade > 0 ? 'success.main' : 'error.main'}>
                {selectedTrade.shares_to_trade.toFixed(0)}
              </Typography>
            </Grid>
            
            <Grid item xs={12}>
              <Typography variant="subtitle2" color="text.secondary">
                Total Trade Value
              </Typography>
              <Typography variant="h5" color={selectedTrade.dollar_amount > 0 ? 'success.main' : 'error.main'}>
                ${Math.abs(selectedTrade.dollar_amount).toLocaleString()}
              </Typography>
            </Grid>
          </Grid>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowTradeDialog(false)}>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Portfolio Rebalancing
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Analyze and generate trade recommendations to rebalance your portfolio allocation.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              {renderPortfolioSelector()}
            </Grid>
            
            {selectedPortfolio && currentAllocation && (
              <Grid item xs={12}>
                {renderAllocationEditor()}
              </Grid>
            )}
            
            <Grid item xs={12}>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <Assessment />}
                onClick={generateRebalancingSuggestions}
                disabled={loading || !selectedPortfolio || !currentAllocation}
                fullWidth
                size="large"
              >
                Generate Rebalancing Suggestions
              </Button>
            </Grid>
            
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
          </Grid>
        </Grid>
        
        <Grid item xs={12} lg={8}>
          {rebalancingResult ? (
            renderRebalancingResults()
          ) : (
            <Paper sx={{ p: 4, height: 400, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Box textAlign="center">
                <SwapHoriz sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Select a portfolio and set target weights to generate rebalancing suggestions
                </Typography>
              </Box>
            </Paper>
          )}
        </Grid>
      </Grid>

      {renderTradeDialog()}
    </Box>
  );
};

export default PortfolioRebalancing;
