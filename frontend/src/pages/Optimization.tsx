import React, { useState } from 'react';
import { 
  Typography, 
  Paper, 
  Box, 
  Tabs, 
  Tab,
  Container,
  Grid,
  Card,
  CardContent,
  TextField,
  Button,
  Chip,
  Autocomplete,
  Alert
} from '@mui/material';
import {
  TrendingUp as OptimizationIcon,
  ShowChart as FrontierIcon,
  SwapHoriz as RebalanceIcon,
  Assessment as ScenarioIcon
} from '@mui/icons-material';
import { 
  PortfolioOptimization, 
  PortfolioRebalancing, 
  ScenarioAnalysis,
  EfficientFrontierChart 
} from '../components';
import { optimizationService } from '../services/optimizationService';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`optimization-tabpanel-${index}`}
      aria-labelledby={`optimization-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `optimization-tab-${index}`,
    'aria-controls': `optimization-tabpanel-${index}`,
  };
}

const Optimization: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  
  // Efficient Frontier state
  const [frontierAssets, setFrontierAssets] = useState<string[]>(['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'SPY']);
  const [frontierData, setFrontierData] = useState<any>(null);
  const [frontierLoading, setFrontierLoading] = useState(false);
  const [frontierError, setFrontierError] = useState<string | null>(null);
  const [lookbackDays, setLookbackDays] = useState(252);
  const [riskFreeRate, setRiskFreeRate] = useState(0.02);

  const availableAssets = [
    'AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN', 'META', 'NVDA', 'NFLX',
    'SPY', 'QQQ', 'IWM', 'VTI', 'VEA', 'VWO', 'BND', 'TLT', 'GLD', 'DBC'
  ];

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const calculateEfficientFrontier = async () => {
    if (frontierAssets.length < 2) {
      setFrontierError('Please select at least 2 assets');
      return;
    }

    setFrontierLoading(true);
    setFrontierError(null);
    
    try {
      const request = {
        asset_symbols: frontierAssets,
        lookback_days: lookbackDays,
        risk_free_rate: riskFreeRate,
        n_points: 100
      };

      const result = await optimizationService.calculateEfficientFrontier(request);
      
      if (result.success && result.data) {
        setFrontierData(result.data);
      } else {
        setFrontierError(result.error?.message || 'Failed to calculate efficient frontier');
      }
    } catch (err) {
      setFrontierError(err instanceof Error ? err.message : 'Efficient frontier calculation failed');
    } finally {
      setFrontierLoading(false);
    }
  };

  const renderEfficientFrontierTab = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} lg={4}>
        <Card variant="outlined">
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Efficient Frontier Settings
            </Typography>
            
            <Box mb={3}>
              <Autocomplete
                multiple
                value={frontierAssets}
                onChange={(_, newValue) => setFrontierAssets(newValue)}
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
                    helperText="Select or type asset symbols"
                  />
                )}
              />
            </Box>
            
            <Box mb={3}>
              <TextField
                fullWidth
                label="Lookback Days"
                type="number"
                value={lookbackDays}
                onChange={(e) => setLookbackDays(Number(e.target.value))}
                helperText="Days of historical data"
              />
            </Box>
            
            <Box mb={3}>
              <TextField
                fullWidth
                label="Risk-Free Rate"
                type="number"
                inputProps={{ step: 0.001 }}
                value={riskFreeRate}
                onChange={(e) => setRiskFreeRate(Number(e.target.value))}
                helperText="Annual risk-free rate (decimal)"
              />
            </Box>
            
            <Button
              variant="contained"
              onClick={calculateEfficientFrontier}
              disabled={frontierLoading || frontierAssets.length < 2}
              fullWidth
              size="large"
            >
              {frontierLoading ? 'Calculating...' : 'Calculate Efficient Frontier'}
            </Button>
            
            {frontierError && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {frontierError}
              </Alert>
            )}
          </CardContent>
        </Card>
      </Grid>
      
      <Grid item xs={12} lg={8}>
        <EfficientFrontierChart 
          data={frontierData || {
            frontier_points: [],
            key_portfolios: [],
            assets: [],
            optimization_date: new Date().toISOString(),
            risk_free_rate: riskFreeRate
          }}
          loading={frontierLoading}
          error={frontierError || undefined}
          height={600}
        />
      </Grid>
    </Grid>
  );

  return (
    <Container maxWidth="xl">
      <Box>
        <Typography variant="h4" component="h1" gutterBottom>
          Portfolio Optimization
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" gutterBottom>
          Optimize your portfolio using modern portfolio theory and efficient frontier analysis
        </Typography>

        <Paper elevation={3} sx={{ mt: 3 }}>
          <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
            <Tabs 
              value={tabValue} 
              onChange={handleTabChange} 
              aria-label="optimization tabs"
              variant="fullWidth"
            >
              <Tab 
                icon={<OptimizationIcon />} 
                label="Portfolio Optimization" 
                {...a11yProps(0)} 
              />
              <Tab 
                icon={<FrontierIcon />} 
                label="Efficient Frontier" 
                {...a11yProps(1)} 
              />
              <Tab 
                icon={<RebalanceIcon />} 
                label="Rebalancing" 
                {...a11yProps(2)} 
              />
              <Tab 
                icon={<ScenarioIcon />} 
                label="Scenario Analysis" 
                {...a11yProps(3)} 
              />
            </Tabs>
          </Box>

          <TabPanel value={tabValue} index={0}>
            <PortfolioOptimization />
          </TabPanel>

          <TabPanel value={tabValue} index={1}>
            {renderEfficientFrontierTab()}
          </TabPanel>

          <TabPanel value={tabValue} index={2}>
            <PortfolioRebalancing />
          </TabPanel>

          <TabPanel value={tabValue} index={3}>
            <ScenarioAnalysis />
          </TabPanel>
        </Paper>
      </Box>
    </Container>
  );
};

export default Optimization;
