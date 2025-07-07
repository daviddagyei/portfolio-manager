/**
 * Portfolio Optimization Component
 * Main component for portfolio optimization with various strategies and constraints
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
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Chip,
  CircularProgress,
  Alert,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Switch,
  FormControlLabel,
  Slider,
  IconButton,
  useTheme,
  Autocomplete
} from '@mui/material';
import {
  ExpandMore,
  PlayArrow,
  Add,
  Delete,
  Assessment,
  ShowChart
} from '@mui/icons-material';

import EfficientFrontierChart from './charts/EfficientFrontierChart';
import { optimizationService } from '../services/optimizationService';

interface OptimizationMethod {
  method: string;
  name: string;
  description: string;
  requires_target: boolean;
  target_type?: string;
}

interface AssetConstraint {
  symbol: string;
  min_weight?: number;
  max_weight?: number;
}

interface SectorConstraint {
  sector: string;
  min_allocation?: number;
  max_allocation?: number;
}

interface OptimizationConstraints {
  min_weight: number;
  max_weight: number;
  asset_constraints: AssetConstraint[];
  sector_constraints: SectorConstraint[];
  max_turnover?: number;
}

interface OptimizationRequest {
  asset_symbols: string[];
  optimization_method: string;
  lookback_days: number;
  risk_free_rate: number;
  target_return?: number;
  target_volatility?: number;
  constraints?: OptimizationConstraints;
  risk_aversion: number;
}

const PortfolioOptimization: React.FC = () => {
  const theme = useTheme();
  
  // State management
  const [optimizationMethods, setOptimizationMethods] = useState<OptimizationMethod[]>([]);
  const [selectedMethod, setSelectedMethod] = useState<string>('max_sharpe');
  const [assetSymbols, setAssetSymbols] = useState<string[]>(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']);
  const [lookbackDays, setLookbackDays] = useState<number>(252);
  const [riskFreeRate, setRiskFreeRate] = useState<number>(0.02);
  const [targetReturn, setTargetReturn] = useState<number>(0.12);
  const [targetVolatility, setTargetVolatility] = useState<number>(0.15);
  const [riskAversion, setRiskAversion] = useState<number>(1.0);
  
  // Constraints
  const [enableConstraints, setEnableConstraints] = useState<boolean>(false);
  const [minWeight, setMinWeight] = useState<number>(0.0);
  const [maxWeight, setMaxWeight] = useState<number>(1.0);
  const [assetConstraints, setAssetConstraints] = useState<AssetConstraint[]>([]);
  const [sectorConstraints, setSectorConstraints] = useState<SectorConstraint[]>([]);
  const [maxTurnover, setMaxTurnover] = useState<number | undefined>(undefined);
  
  // Results
  const [optimizationResult, setOptimizationResult] = useState<any>(null);
  const [efficientFrontier, setEfficientFrontier] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  
  // UI state
  const [showAdvancedSettings, setShowAdvancedSettings] = useState<boolean>(false);
  const [constraintDialogOpen, setConstraintDialogOpen] = useState<boolean>(false);
  const [selectedTab, setSelectedTab] = useState<string>('optimization');

  // Available assets for autocomplete
  const availableAssets = [
    'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX',
    'SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'BND', 'TLT', 'GLD', 'DBC'
  ];

  useEffect(() => {
    loadOptimizationMethods();
  }, []);

  const loadOptimizationMethods = async () => {
    try {
      const methods = await optimizationService.getOptimizationMethods();
      setOptimizationMethods(methods);
    } catch (err) {
      console.error('Failed to load optimization methods:', err);
    }
  };

  const runOptimization = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const request: OptimizationRequest = {
        asset_symbols: assetSymbols,
        optimization_method: selectedMethod,
        lookback_days: lookbackDays,
        risk_free_rate: riskFreeRate,
        risk_aversion: riskAversion
      };

      // Add target values if required
      const method = optimizationMethods.find(m => m.method === selectedMethod);
      if (method?.requires_target) {
        if (method.target_type === 'return') {
          request.target_return = targetReturn;
        } else if (method.target_type === 'volatility') {
          request.target_volatility = targetVolatility;
        }
      }

      // Add constraints if enabled
      if (enableConstraints) {
        request.constraints = {
          min_weight: minWeight,
          max_weight: maxWeight,
          asset_constraints: assetConstraints,
          sector_constraints: sectorConstraints,
          max_turnover: maxTurnover
        };
      }

      const result = await optimizationService.optimizePortfolio(request);
      setOptimizationResult(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Optimization failed');
    } finally {
      setLoading(false);
    }
  };

  const calculateEfficientFrontier = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const frontierRequest = {
        asset_symbols: assetSymbols,
        lookback_days: lookbackDays,
        risk_free_rate: riskFreeRate,
        n_points: 100,
        constraints: enableConstraints ? {
          min_weight: minWeight,
          max_weight: maxWeight,
          asset_constraints: assetConstraints,
          sector_constraints: sectorConstraints
        } : undefined
      };

      const result = await optimizationService.calculateEfficientFrontier(frontierRequest);
      setEfficientFrontier(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Efficient frontier calculation failed');
    } finally {
      setLoading(false);
    }
  };

  const addAssetConstraint = () => {
    setAssetConstraints([...assetConstraints, { symbol: '', min_weight: 0, max_weight: 1 }]);
  };

  const removeAssetConstraint = (index: number) => {
    setAssetConstraints(assetConstraints.filter((_, i) => i !== index));
  };

  const updateAssetConstraint = (index: number, field: string, value: any) => {
    const updated = [...assetConstraints];
    updated[index] = { ...updated[index], [field]: value };
    setAssetConstraints(updated);
  };

  const renderOptimizationSettings = () => (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Optimization Settings
        </Typography>
        
        <Grid container spacing={3}>
          <Grid item xs={12}>
            <Autocomplete
              multiple
              value={assetSymbols}
              onChange={(_, newValue) => setAssetSymbols(newValue)}
              options={availableAssets}
              freeSolo
              renderTags={(value, getTagProps) =>
                value.map((option, index) => (
                  <Chip variant="outlined" label={option} {...getTagProps({ index })} />
                ))
              }
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Asset Symbols"
                  placeholder="Add assets"
                  helperText="Select or type asset symbols for optimization"
                />
              )}
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <FormControl fullWidth>
              <InputLabel>Optimization Method</InputLabel>
              <Select
                value={selectedMethod}
                label="Optimization Method"
                onChange={(e) => setSelectedMethod(e.target.value)}
              >
                {optimizationMethods.map((method) => (
                  <MenuItem key={method.method} value={method.method}>
                    <Box>
                      <Typography variant="body1">{method.name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {method.description}
                      </Typography>
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Lookback Days"
              type="number"
              value={lookbackDays}
              onChange={(e) => setLookbackDays(Number(e.target.value))}
              helperText="Days of historical data"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Risk-Free Rate"
              type="number"
              inputProps={{ step: 0.001 }}
              value={riskFreeRate}
              onChange={(e) => setRiskFreeRate(Number(e.target.value))}
              helperText="Annual risk-free rate (decimal)"
            />
          </Grid>

          {/* Target values for specific methods */}
          {optimizationMethods.find(m => m.method === selectedMethod)?.requires_target && (
            <>
              {optimizationMethods.find(m => m.method === selectedMethod)?.target_type === 'return' && (
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Target Return"
                    type="number"
                    inputProps={{ step: 0.01 }}
                    value={targetReturn}
                    onChange={(e) => setTargetReturn(Number(e.target.value))}
                    helperText="Target annual return (decimal)"
                  />
                </Grid>
              )}
              
              {optimizationMethods.find(m => m.method === selectedMethod)?.target_type === 'volatility' && (
                <Grid item xs={12} md={6}>
                  <TextField
                    fullWidth
                    label="Target Volatility"
                    type="number"
                    inputProps={{ step: 0.01 }}
                    value={targetVolatility}
                    onChange={(e) => setTargetVolatility(Number(e.target.value))}
                    helperText="Target annual volatility (decimal)"
                  />
                </Grid>
              )}
            </>
          )}
          
          {selectedMethod === 'max_quadratic_utility' && (
            <Grid item xs={12} md={6}>
              <Box>
                <Typography gutterBottom>Risk Aversion: {riskAversion}</Typography>
                <Slider
                  value={riskAversion}
                  onChange={(_, value) => setRiskAversion(value as number)}
                  min={0.1}
                  max={5.0}
                  step={0.1}
                  marks={[
                    { value: 0.5, label: 'Low' },
                    { value: 1.0, label: 'Medium' },
                    { value: 2.0, label: 'High' }
                  ]}
                />
              </Box>
            </Grid>
          )}
        </Grid>
      </CardContent>
    </Card>
  );

  const renderConstraints = () => (
    <Accordion expanded={enableConstraints}>
      <AccordionSummary expandIcon={<ExpandMore />}>
        <FormControlLabel
          control={
            <Switch
              checked={enableConstraints}
              onChange={(e) => setEnableConstraints(e.target.checked)}
              onClick={(e) => e.stopPropagation()}
            />
          }
          label="Advanced Constraints"
        />
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Minimum Weight"
              type="number"
              inputProps={{ step: 0.01 }}
              value={minWeight}
              onChange={(e) => setMinWeight(Number(e.target.value))}
              helperText="Minimum weight per asset"
            />
          </Grid>
          
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              label="Maximum Weight"
              type="number"
              inputProps={{ step: 0.01 }}
              value={maxWeight}
              onChange={(e) => setMaxWeight(Number(e.target.value))}
              helperText="Maximum weight per asset"
            />
          </Grid>
          
          <Grid item xs={12}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="subtitle1">Asset Constraints</Typography>
              <Button
                size="small"
                startIcon={<Add />}
                onClick={addAssetConstraint}
              >
                Add Asset Constraint
              </Button>
            </Box>
            
            {assetConstraints.map((constraint, index) => (
              <Box key={index} display="flex" gap={2} mb={2} alignItems="center">
                <FormControl sx={{ minWidth: 120 }}>
                  <InputLabel>Asset</InputLabel>
                  <Select
                    value={constraint.symbol}
                    label="Asset"
                    onChange={(e) => updateAssetConstraint(index, 'symbol', e.target.value)}
                  >
                    {assetSymbols.map((symbol) => (
                      <MenuItem key={symbol} value={symbol}>{symbol}</MenuItem>
                    ))}
                  </Select>
                </FormControl>
                
                <TextField
                  label="Min Weight"
                  type="number"
                  inputProps={{ step: 0.01 }}
                  value={constraint.min_weight || ''}
                  onChange={(e) => updateAssetConstraint(index, 'min_weight', Number(e.target.value))}
                  sx={{ width: 120 }}
                />
                
                <TextField
                  label="Max Weight"
                  type="number"
                  inputProps={{ step: 0.01 }}
                  value={constraint.max_weight || ''}
                  onChange={(e) => updateAssetConstraint(index, 'max_weight', Number(e.target.value))}
                  sx={{ width: 120 }}
                />
                
                <IconButton
                  color="error"
                  onClick={() => removeAssetConstraint(index)}
                >
                  <Delete />
                </IconButton>
              </Box>
            ))}
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );

  const renderOptimizationResult = () => {
    if (!optimizationResult) return null;

    const { data } = optimizationResult;
    const weights = Object.entries(data.weights).sort(([, a], [, b]) => (b as number) - (a as number));

    return (
      <Card variant="outlined">
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Optimization Result - {data.optimization_method.replace('_', ' ').toUpperCase()}
          </Typography>
          
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Box mb={2}>
                <Typography variant="subtitle2" color="text.secondary">Performance Metrics</Typography>
                <Box display="flex" justifyContent="space-between" mt={1}>
                  <Typography>Expected Return:</Typography>
                  <Chip 
                    label={`${(data.metrics.expected_return * 100).toFixed(2)}%`}
                    color="success"
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" mt={1}>
                  <Typography>Volatility:</Typography>
                  <Chip 
                    label={`${(data.metrics.volatility * 100).toFixed(2)}%`}
                    color="warning"
                    size="small"
                  />
                </Box>
                <Box display="flex" justifyContent="space-between" mt={1}>
                  <Typography>Sharpe Ratio:</Typography>
                  <Chip 
                    label={data.metrics.sharpe_ratio.toFixed(3)}
                    color={data.metrics.sharpe_ratio > 1 ? 'success' : 'error'}
                    size="small"
                  />
                </Box>
              </Box>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" color="text.secondary">Asset Allocation</Typography>
              <Box mt={1}>
                {weights.map(([asset, weight]) => (
                  <Box key={asset} mb={1}>
                    <Box display="flex" justifyContent="space-between">
                      <Typography variant="body2">{asset}</Typography>
                      <Typography variant="body2" fontWeight="bold">
                        {((weight as number) * 100).toFixed(1)}%
                      </Typography>
                    </Box>
                    <Box
                      sx={{
                        height: 6,
                        backgroundColor: theme.palette.grey[200],
                        borderRadius: 3,
                        overflow: 'hidden'
                      }}
                    >
                      <Box
                        sx={{
                          height: '100%',
                          width: `${(weight as number) * 100}%`,
                          backgroundColor: theme.palette.primary.main
                        }}
                      />
                    </Box>
                  </Box>
                ))}
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
    );
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Portfolio Optimization
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Modern Portfolio Theory implementation with advanced optimization strategies and constraints.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              {renderOptimizationSettings()}
            </Grid>
            
            <Grid item xs={12}>
              {renderConstraints()}
            </Grid>
            
            <Grid item xs={12}>
              <Box display="flex" gap={2}>
                <Button
                  variant="contained"
                  startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                  onClick={runOptimization}
                  disabled={loading || assetSymbols.length < 2}
                  fullWidth
                >
                  Optimize Portfolio
                </Button>
                
                <Button
                  variant="outlined"
                  startIcon={<ShowChart />}
                  onClick={calculateEfficientFrontier}
                  disabled={loading || assetSymbols.length < 2}
                >
                  Frontier
                </Button>
              </Box>
            </Grid>
            
            {error && (
              <Grid item xs={12}>
                <Alert severity="error">{error}</Alert>
              </Grid>
            )}
            
            {optimizationResult && (
              <Grid item xs={12}>
                {renderOptimizationResult()}
              </Grid>
            )}
          </Grid>
        </Grid>
        
        <Grid item xs={12} lg={8}>
          {efficientFrontier ? (
            <EfficientFrontierChart
              data={efficientFrontier.data}
              loading={loading}
              error={error || undefined}
              height={600}
              showKeyPortfolios={true}
              showAssetComposition={true}
            />
          ) : (
            <Paper sx={{ p: 4, height: 600, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Box textAlign="center">
                <Assessment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Run optimization or calculate efficient frontier to see results
                </Typography>
              </Box>
            </Paper>
          )}
        </Grid>
      </Grid>
    </Box>
  );
};

export default PortfolioOptimization;
