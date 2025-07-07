import React from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  useTheme,
  useMediaQuery
} from '@mui/material';
import {
  TrendingUp,
  TrendingDown,
  Refresh,
  Edit,
  Delete
} from '@mui/icons-material';

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

interface PortfolioHoldingsTableProps {
  holdings: PortfolioHolding[];
  loading?: boolean;
  error?: string;
  onRefresh?: () => void;
  onEdit?: (holding: PortfolioHolding) => void;
  onDelete?: (holdingId: number) => void;
}

const PortfolioHoldingsTable: React.FC<PortfolioHoldingsTableProps> = ({
  holdings,
  loading = false,
  error,
  onRefresh,
  onEdit,
  onDelete
}) => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));

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
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const getAssetTypeColor = (type: string) => {
    const colors: { [key: string]: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' } = {
      'stock': 'primary',
      'bond': 'secondary',
      'etf': 'success',
      'mutual_fund': 'info',
      'cryptocurrency': 'warning',
      'commodity': 'error'
    };
    return colors[type.toLowerCase()] || 'primary';
  };

  if (loading) {
    return (
      <Paper sx={{ p: 3 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight={200}>
          <CircularProgress />
        </Box>
      </Paper>
    );
  }

  if (error) {
    return (
      <Paper sx={{ p: 3 }}>
        <Alert severity="error">{error}</Alert>
      </Paper>
    );
  }

  if (holdings.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="body1" color="text.secondary" textAlign="center">
          No holdings found in this portfolio.
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" component="h2">
          Portfolio Holdings
        </Typography>
        {onRefresh && (
          <Tooltip title="Refresh Holdings">
            <IconButton onClick={onRefresh}>
              <Refresh />
            </IconButton>
          </Tooltip>
        )}
      </Box>

      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader>
          <TableHead>
            <TableRow>
              <TableCell>Asset</TableCell>
              <TableCell>Type</TableCell>
              {!isMobile && <TableCell>Sector</TableCell>}
              <TableCell align="right">Quantity</TableCell>
              <TableCell align="right">Avg Cost</TableCell>
              <TableCell align="right">Current Price</TableCell>
              <TableCell align="right">Market Value</TableCell>
              <TableCell align="right">Gain/Loss</TableCell>
              {!isMobile && <TableCell align="right">Last Updated</TableCell>}
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {holdings.map((holding) => {
              const isPositiveReturn = holding.unrealized_gain_loss >= 0;
              const ReturnIcon = isPositiveReturn ? TrendingUp : TrendingDown;

              return (
                <TableRow
                  key={holding.holding_id}
                  hover
                  sx={{ '&:last-child td, &:last-child th': { border: 0 } }}
                >
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2" fontWeight="bold">
                        {holding.asset_symbol}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" noWrap>
                        {holding.asset_name}
                      </Typography>
                    </Box>
                  </TableCell>
                  
                  <TableCell>
                    <Chip 
                      label={holding.asset_type.toUpperCase()} 
                      color={getAssetTypeColor(holding.asset_type)}
                      size="small"
                    />
                  </TableCell>
                  
                  {!isMobile && (
                    <TableCell>
                      <Typography variant="body2">
                        {holding.sector || 'N/A'}
                      </Typography>
                    </TableCell>
                  )}
                  
                  <TableCell align="right">
                    <Typography variant="body2">
                      {holding.quantity.toLocaleString()}
                    </Typography>
                  </TableCell>
                  
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatCurrency(holding.average_cost)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell align="right">
                    <Typography variant="body2">
                      {formatCurrency(holding.current_price)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell align="right">
                    <Typography variant="body2" fontWeight="bold">
                      {formatCurrency(holding.market_value)}
                    </Typography>
                  </TableCell>
                  
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', gap: 0.5 }}>
                      <ReturnIcon 
                        color={isPositiveReturn ? 'success' : 'error'}
                        sx={{ fontSize: 16 }}
                      />
                      <Box>
                        <Typography 
                          variant="body2" 
                          sx={{ 
                            color: isPositiveReturn ? 'success.main' : 'error.main',
                            fontWeight: 'medium'
                          }}
                        >
                          {formatCurrency(holding.unrealized_gain_loss)}
                        </Typography>
                        <Typography 
                          variant="caption" 
                          sx={{ 
                            color: isPositiveReturn ? 'success.main' : 'error.main'
                          }}
                        >
                          {formatPercentage(holding.unrealized_gain_loss_percentage)}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  
                  {!isMobile && (
                    <TableCell align="right">
                      <Typography variant="caption" color="text.secondary">
                        {formatDate(holding.last_updated)}
                      </Typography>
                    </TableCell>
                  )}
                  
                  <TableCell align="right">
                    <Box sx={{ display: 'flex', gap: 0.5 }}>
                      {onEdit && (
                        <Tooltip title="Edit Holding">
                          <IconButton 
                            size="small" 
                            onClick={() => onEdit(holding)}
                          >
                            <Edit fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      {onDelete && (
                        <Tooltip title="Delete Holding">
                          <IconButton 
                            size="small" 
                            color="error"
                            onClick={() => onDelete(holding.holding_id)}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

export default PortfolioHoldingsTable;
