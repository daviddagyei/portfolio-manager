/**
 * Scenario Analysis Component
 * What-if analysis for portfolio optimization with stress testing scenarios
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
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Divider,
  useTheme,
  Tooltip,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction
} from '@mui/material';
import {
  ExpandMore,
  Add,
  Delete,
  PlayArrow,
  Assessment,
  TrendingUp,
  TrendingDown,
  Warning,
  Error as ErrorIcon,
  CheckCircle,
  Info,
  Edit
} from '@mui/icons-material';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip as ChartTooltip,
  Legend
} from 'chart.js';

import { 
  optimizationService, 
  ScenarioDefinition, 
  ScenarioAnalysisResponse,
  ScenarioResult 
} from '../services/optimizationService';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  ChartTooltip,
  Legend
);

interface ScenarioAnalysisProps {
  portfolioWeights?: Record<string, number>;
  assetSymbols?: string[];
  onScenarioComplete?: (result: ScenarioAnalysisResponse) => void;
}

const predefinedScenarios: ScenarioDefinition[] = [
  {
    name: "Market Crash",
    description: "30% market decline scenario",
    return_shock: { value: -0.30 }
  },
  {
    name: "Tech Sector Crash",
    description: "50% decline in tech stocks",
    return_shock: { value: -0.50, assets: ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'NVDA', 'META'] }
  },
  {
    name: "High Volatility",
    description: "Doubled market volatility",
    volatility_shock: { multiplier: 2.0 }
  },
  {
    name: "Recession",
    description: "Economic recession with -20% returns",
    return_shock: { value: -0.20 },
    volatility_shock: { multiplier: 1.5 }
  },
  {
    name: "Bull Market",
    description: "Strong bull market with +40% returns",
    return_shock: { value: 0.40 }
  },
  {
    name: "Inflation Spike",
    description: "High inflation environment",
    return_shock: { value: -0.15 },
    volatility_shock: { multiplier: 1.3 }
  }
];

const ScenarioAnalysis: React.FC<ScenarioAnalysisProps> = ({
  portfolioWeights = {},
  assetSymbols = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY'],
  onScenarioComplete
}) => {
  const theme = useTheme();
  
  // State management
  const [weights, setWeights] = useState<Record<string, number>>(portfolioWeights);
  const [symbols, setSymbols] = useState<string[]>(assetSymbols);
  const [scenarios, setScenarios] = useState<ScenarioDefinition[]>([...predefinedScenarios]);
  const [customScenarios, setCustomScenarios] = useState<ScenarioDefinition[]>([]);
  const [scenarioResults, setScenarioResults] = useState<ScenarioAnalysisResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [lookbackDays, setLookbackDays] = useState<number>(252);
  
  // UI state
  const [editingScenario, setEditingScenario] = useState<ScenarioDefinition | null>(null);
  const [showScenarioDialog, setShowScenarioDialog] = useState<boolean>(false);
  const [selectedScenarios, setSelectedScenarios] = useState<Set<string>>(
    new Set(predefinedScenarios.map(s => s.name))
  );

  useEffect(() => {
    setWeights(portfolioWeights);
  }, [portfolioWeights]);

  useEffect(() => {
    setSymbols(assetSymbols);
  }, [assetSymbols]);

  const runScenarioAnalysis = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Validate inputs
      if (Object.keys(weights).length === 0) {
        throw new Error('Please provide portfolio weights');
      }
      
      if (symbols.length === 0) {
        throw new Error('Please provide asset symbols');
      }
      
      const selectedScenarioList = [...scenarios, ...customScenarios].filter(
        scenario => selectedScenarios.has(scenario.name)
      );
      
      if (selectedScenarioList.length === 0) {
        throw new Error('Please select at least one scenario');
      }
      
      const request = {
        weights,
        asset_symbols: symbols,
        scenarios: selectedScenarioList,
        lookback_days: lookbackDays
      };
      
      const result = await optimizationService.runScenarioAnalysis(request);
      
      if (result.success && result.data) {
        setScenarioResults(result.data);
        onScenarioComplete?.(result.data);
      } else {
        setError(result.error?.message || 'Scenario analysis failed');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Scenario analysis failed');
    } finally {
      setLoading(false);
    }
  };

  const addCustomScenario = () => {
    setEditingScenario({
      name: '',
      description: '',
      return_shock: { value: 0 },
      volatility_shock: { multiplier: 1.0 }
    });
    setShowScenarioDialog(true);
  };

  const editScenario = (scenario: ScenarioDefinition) => {
    setEditingScenario({ ...scenario });
    setShowScenarioDialog(true);
  };

  const saveScenario = () => {
    if (!editingScenario || !editingScenario.name) return;
    
    const isExisting = customScenarios.some(s => s.name === editingScenario.name);
    
    if (isExisting) {
      setCustomScenarios(prev => 
        prev.map(s => s.name === editingScenario.name ? editingScenario : s)
      );
    } else {
      setCustomScenarios(prev => [...prev, editingScenario]);
      setSelectedScenarios(prev => {
        const newSet = new Set(prev);
        newSet.add(editingScenario.name);
        return newSet;
      });
    }
    
    setShowScenarioDialog(false);
    setEditingScenario(null);
  };

  const deleteCustomScenario = (scenarioName: string) => {
    setCustomScenarios(prev => prev.filter(s => s.name !== scenarioName));
    setSelectedScenarios(prev => {
      const newSet = new Set(prev);
      newSet.delete(scenarioName);
      return newSet;
    });
  };

  const toggleScenarioSelection = (scenarioName: string) => {
    setSelectedScenarios(prev => {
      const newSet = new Set(prev);
      if (newSet.has(scenarioName)) {
        newSet.delete(scenarioName);
      } else {
        newSet.add(scenarioName);
      }
      return newSet;
    });
  };

  const updateWeight = (symbol: string, weight: number) => {
    setWeights(prev => ({
      ...prev,
      [symbol]: weight / 100
    }));
  };

  const getScenarioSeverity = (result: ScenarioResult) => {
    if (result.annualized_return < -0.2 || result.max_drawdown < -0.3) {
      return { color: 'error' as const, icon: <ErrorIcon /> };
    } else if (result.annualized_return < 0 || result.max_drawdown < -0.1) {
      return { color: 'warning' as const, icon: <Warning /> };
    } else {
      return { color: 'success' as const, icon: <CheckCircle /> };
    }
  };

  const renderPortfolioWeights = () => (
    <Card variant="outlined">
      <CardContent>
        <Typography variant="h6" gutterBottom>
          Portfolio Weights
        </Typography>
        
        <Grid container spacing={2}>
          {symbols.map((symbol) => {
            const weight = (weights[symbol] || 0) * 100;
            
            return (
              <Grid item xs={12} sm={6} key={symbol}>
                <Box mb={2}>
                  <Typography variant="subtitle2" gutterBottom>
                    {symbol}
                  </Typography>
                  <TextField
                    fullWidth
                    type="number"
                    value={weight.toFixed(1)}
                    onChange={(e) => updateWeight(symbol, Number(e.target.value))}
                    inputProps={{ min: 0, max: 100, step: 0.1 }}
                    InputProps={{
                      endAdornment: '%'
                    }}
                    size="small"
                  />
                </Box>
              </Grid>
            );
          })}
        </Grid>
        
        <Box mt={2}>
          <Typography variant="caption" color="text.secondary">
            Total: {(Object.values(weights).reduce((sum, w) => sum + w, 0) * 100).toFixed(1)}%
          </Typography>
        </Box>
      </CardContent>
    </Card>
  );

  const renderScenarioSelection = () => (
    <Card variant="outlined">
      <CardContent>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6">
            Scenario Selection
          </Typography>
          <Button
            size="small"
            startIcon={<Add />}
            onClick={addCustomScenario}
          >
            Add Custom
          </Button>
        </Box>
        
        <Typography variant="subtitle2" gutterBottom>
          Predefined Scenarios
        </Typography>
        <List dense>
          {scenarios.map((scenario) => (
            <ListItem key={scenario.name}>
              <ListItemText
                primary={scenario.name}
                secondary={scenario.description}
              />
              <ListItemSecondaryAction>
                <Box display="flex" alignItems="center" gap={1}>
                  <Chip
                    size="small"
                    label={selectedScenarios.has(scenario.name) ? 'Selected' : 'Not Selected'}
                    color={selectedScenarios.has(scenario.name) ? 'primary' : 'default'}
                    onClick={() => toggleScenarioSelection(scenario.name)}
                    clickable
                  />
                </Box>
              </ListItemSecondaryAction>
            </ListItem>
          ))}
        </List>
        
        {customScenarios.length > 0 && (
          <>
            <Divider sx={{ my: 2 }} />
            <Typography variant="subtitle2" gutterBottom>
              Custom Scenarios
            </Typography>
            <List dense>
              {customScenarios.map((scenario) => (
                <ListItem key={scenario.name}>
                  <ListItemText
                    primary={scenario.name}
                    secondary={scenario.description}
                  />
                  <ListItemSecondaryAction>
                    <Box display="flex" alignItems="center" gap={1}>
                      <IconButton
                        size="small"
                        onClick={() => editScenario(scenario)}
                      >
                        <Edit />
                      </IconButton>
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => deleteCustomScenario(scenario.name)}
                      >
                        <Delete />
                      </IconButton>
                      <Chip
                        size="small"
                        label={selectedScenarios.has(scenario.name) ? 'Selected' : 'Not Selected'}
                        color={selectedScenarios.has(scenario.name) ? 'primary' : 'default'}
                        onClick={() => toggleScenarioSelection(scenario.name)}
                        clickable
                      />
                    </Box>
                  </ListItemSecondaryAction>
                </ListItem>
              ))}
            </List>
          </>
        )}
      </CardContent>
    </Card>
  );

  const renderScenarioResults = () => {
    if (!scenarioResults) return null;

    const scenarioNames = Object.keys(scenarioResults.scenarios);
    const chartData = {
      labels: scenarioNames,
      datasets: [
        {
          label: 'Annual Return (%)',
          data: scenarioNames.map(name => 
            scenarioResults.scenarios[name].annualized_return * 100
          ),
          backgroundColor: scenarioNames.map(name => {
            const result = scenarioResults.scenarios[name];
            return result.annualized_return >= 0 
              ? theme.palette.success.main 
              : theme.palette.error.main;
          }),
          borderColor: theme.palette.background.paper,
          borderWidth: 1
        }
      ]
    };

    const chartOptions = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          display: false
        },
        title: {
          display: true,
          text: 'Scenario Returns Comparison'
        }
      },
      scales: {
        x: {
          grid: {
            display: false
          }
        },
        y: {
          title: {
            display: true,
            text: 'Annual Return (%)'
          },
          grid: {
            color: theme.palette.divider
          }
        }
      }
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} lg={8}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Scenario Analysis Results
              </Typography>
              
              <Box sx={{ height: 400, mb: 3 }}>
                <Bar data={chartData} options={chartOptions} />
              </Box>
              
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Scenario</TableCell>
                      <TableCell align="right">Return</TableCell>
                      <TableCell align="right">Volatility</TableCell>
                      <TableCell align="right">Sharpe</TableCell>
                      <TableCell align="right">Max DD</TableCell>
                      <TableCell align="right">VaR 95%</TableCell>
                      <TableCell align="center">Risk Level</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {Object.entries(scenarioResults.scenarios).map(([name, result]) => {
                      const typedResult = result as ScenarioResult;
                      const severity = getScenarioSeverity(typedResult);
                      
                      return (
                        <TableRow key={name}>
                          <TableCell>
                            <Typography variant="body2" fontWeight="bold">
                              {name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {typedResult.description}
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color={typedResult.annualized_return >= 0 ? 'success.main' : 'error.main'}
                            >
                              {(typedResult.annualized_return * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            {(typedResult.volatility * 100).toFixed(1)}%
                          </TableCell>
                          <TableCell align="right">
                            <Chip
                              size="small"
                              label={typedResult.sharpe_ratio.toFixed(2)}
                              color={typedResult.sharpe_ratio > 1 ? 'success' : typedResult.sharpe_ratio > 0 ? 'warning' : 'error'}
                            />
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color="error.main"
                            >
                              {(typedResult.max_drawdown * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="right">
                            <Typography
                              variant="body2"
                              color="error.main"
                            >
                              {(typedResult.var_95 * 100).toFixed(1)}%
                            </Typography>
                          </TableCell>
                          <TableCell align="center">
                            <Chip
                              size="small"
                              icon={severity.icon}
                              label={severity.color.toUpperCase()}
                              color={severity.color}
                            />
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>
        
        <Grid item xs={12} lg={4}>
          <Card variant="outlined">
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Risk Summary
              </Typography>
              
              {Object.entries(scenarioResults.scenarios).map(([name, result]) => {
                const typedResult = result as ScenarioResult;
                const severity = getScenarioSeverity(typedResult);
                
                return (
                  <Box key={name} mb={2}>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="body2">{name}</Typography>
                      <Chip
                        size="small"
                        icon={severity.icon}
                        label={`${(typedResult.total_return * 100).toFixed(1)}%`}
                        color={severity.color}
                      />
                    </Box>
                  </Box>
                );
              })}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    );
  };

  const renderScenarioDialog = () => (
    <Dialog
      open={showScenarioDialog}
      onClose={() => setShowScenarioDialog(false)}
      maxWidth="md"
      fullWidth
    >
      <DialogTitle>
        {editingScenario && customScenarios.some(s => s.name === editingScenario.name) 
          ? 'Edit Custom Scenario' 
          : 'Add Custom Scenario'}
      </DialogTitle>
      <DialogContent>
        {editingScenario && (
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Scenario Name"
                value={editingScenario.name}
                onChange={(e) => setEditingScenario((prev: ScenarioDefinition | null) => prev ? { ...prev, name: e.target.value } : null)}
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description"
                multiline
                rows={2}
                value={editingScenario.description}
                onChange={(e) => setEditingScenario((prev: ScenarioDefinition | null) => prev ? { ...prev, description: e.target.value } : null)}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Return Shock (%)"
                type="number"
                value={editingScenario.return_shock?.value ? (editingScenario.return_shock.value * 100).toFixed(1) : '0'}
                onChange={(e) => setEditingScenario((prev: ScenarioDefinition | null) => prev ? {
                  ...prev,
                  return_shock: { ...prev.return_shock, value: Number(e.target.value) / 100 }
                } : null)}
                helperText="Positive for gains, negative for losses"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="Volatility Multiplier"
                type="number"
                value={editingScenario.volatility_shock?.multiplier || 1}
                onChange={(e) => setEditingScenario((prev: ScenarioDefinition | null) => prev ? {
                  ...prev,
                  volatility_shock: { ...prev.volatility_shock, multiplier: Number(e.target.value) }
                } : null)}
                helperText="1.0 = normal, 2.0 = double volatility"
              />
            </Grid>
          </Grid>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={() => setShowScenarioDialog(false)}>
          Cancel
        </Button>
        <Button 
          onClick={saveScenario}
          variant="contained"
          disabled={!editingScenario?.name}
        >
          Save
        </Button>
      </DialogActions>
    </Dialog>
  );

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Scenario Analysis
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Stress test your portfolio under various market conditions and economic scenarios.
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} lg={4}>
          <Grid container spacing={2}>
            <Grid item xs={12}>
              {renderPortfolioWeights()}
            </Grid>
            
            <Grid item xs={12}>
              {renderScenarioSelection()}
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Lookback Days"
                type="number"
                value={lookbackDays}
                onChange={(e) => setLookbackDays(Number(e.target.value))}
                helperText="Historical data period for analysis"
              />
            </Grid>
            
            <Grid item xs={12}>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <PlayArrow />}
                onClick={runScenarioAnalysis}
                disabled={loading || selectedScenarios.size === 0}
                fullWidth
                size="large"
              >
                Run Scenario Analysis
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
          {scenarioResults ? (
            renderScenarioResults()
          ) : (
            <Paper sx={{ p: 4, height: 500, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              <Box textAlign="center">
                <Assessment sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
                <Typography variant="h6" color="text.secondary">
                  Configure portfolio weights and select scenarios to run analysis
                </Typography>
              </Box>
            </Paper>
          )}
        </Grid>
      </Grid>

      {renderScenarioDialog()}
    </Box>
  );
};

export default ScenarioAnalysis;
