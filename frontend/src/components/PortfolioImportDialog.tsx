import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  LinearProgress,
  Paper,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Tabs,
  Tab,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  CloudUpload,
  Description,
  CheckCircle,
  Error,
  Warning
} from '@mui/icons-material';

interface PortfolioImportDialogProps {
  open: boolean;
  onClose: () => void;
  onImport: (data: any) => Promise<void>;
}

interface ImportResult {
  success: boolean;
  message: string;
  data?: any;
  errors?: string[];
}

const PortfolioImportDialog: React.FC<PortfolioImportDialogProps> = ({
  open,
  onClose,
  onImport
}) => {
  const [tabValue, setTabValue] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [csvData, setCsvData] = useState('');
  const [portfolioName, setPortfolioName] = useState('');
  const [portfolioType, setPortfolioType] = useState('investment');

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
    resetForm();
  };

  const resetForm = () => {
    setFile(null);
    setCsvData('');
    setPortfolioName('');
    setPortfolioType('investment');
    setImportResult(null);
  };

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile) {
      setFile(selectedFile);
      setImportResult(null);
    }
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const parseCSV = (csvText: string) => {
    const lines = csvText.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    
    const data = lines.slice(1).map(line => {
      const values = line.split(',').map(v => v.trim());
      const row: any = {};
      headers.forEach((header, index) => {
        row[header] = values[index];
      });
      return row;
    });

    return { headers, data };
  };

  const validateData = (data: any[]) => {
    const errors: string[] = [];
    const requiredFields = ['symbol', 'quantity', 'price'];
    
    data.forEach((row, index) => {
      requiredFields.forEach(field => {
        if (!row[field]) {
          errors.push(`Row ${index + 1}: Missing ${field}`);
        }
      });
      
      if (row.quantity && isNaN(Number(row.quantity))) {
        errors.push(`Row ${index + 1}: Invalid quantity value`);
      }
      
      if (row.price && isNaN(Number(row.price))) {
        errors.push(`Row ${index + 1}: Invalid price value`);
      }
    });

    return errors;
  };

  const handleImport = async () => {
    if (!portfolioName.trim()) {
      setImportResult({
        success: false,
        message: 'Portfolio name is required'
      });
      return;
    }

    setImporting(true);
    setImportResult(null);

    try {
      let data: any[] = [];
      
      if (tabValue === 0 && file) {
        // File upload
        const text = await file.text();
        const { data: parsedData } = parseCSV(text);
        data = parsedData;
      } else if (tabValue === 1 && csvData.trim()) {
        // Manual CSV input
        const { data: parsedData } = parseCSV(csvData);
        data = parsedData;
      } else {
        setImportResult({
          success: false,
          message: 'Please provide data to import'
        });
        setImporting(false);
        return;
      }

      // Validate data
      const errors = validateData(data);
      if (errors.length > 0) {
        setImportResult({
          success: false,
          message: 'Data validation failed',
          errors: errors.slice(0, 10) // Show first 10 errors
        });
        setImporting(false);
        return;
      }

      // Prepare import data
      const importData = {
        portfolio: {
          name: portfolioName,
          portfolioType: portfolioType,
          description: `Imported portfolio from ${file?.name || 'CSV data'}`
        },
        holdings: data.map(row => ({
          symbol: row.symbol,
          quantity: Number(row.quantity),
          averageCost: Number(row.price),
          assetType: row.asset_type || 'stock',
          sector: row.sector || null
        }))
      };

      await onImport(importData);
      
      setImportResult({
        success: true,
        message: `Successfully imported ${data.length} holdings`,
        data: importData
      });

      // Close dialog after successful import
      setTimeout(() => {
        handleClose();
      }, 2000);

    } catch (error) {
      let errorMessage = 'Import failed';
      if (error && typeof error === 'object' && 'message' in error) {
        errorMessage = String(error.message);
      } else if (typeof error === 'string') {
        errorMessage = error;
      }
      
      setImportResult({
        success: false,
        message: errorMessage
      });
    } finally {
      setImporting(false);
    }
  };

  const csvTemplate = `symbol,quantity,price,asset_type,sector
AAPL,100,150.00,stock,Technology
GOOGL,50,2800.00,stock,Technology
MSFT,75,300.00,stock,Technology
TSLA,25,800.00,stock,Consumer Discretionary
SPY,200,400.00,etf,Diversified`;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Import Portfolio</DialogTitle>
      
      <DialogContent>
        <Box sx={{ mb: 3 }}>
          <TextField
            fullWidth
            label="Portfolio Name"
            value={portfolioName}
            onChange={(e) => setPortfolioName(e.target.value)}
            margin="normal"
            required
          />
          
          <FormControl fullWidth margin="normal">
            <InputLabel>Portfolio Type</InputLabel>
            <Select
              value={portfolioType}
              label="Portfolio Type"
              onChange={(e) => setPortfolioType(e.target.value)}
            >
              <MenuItem value="personal">Personal</MenuItem>
              <MenuItem value="retirement">Retirement</MenuItem>
              <MenuItem value="education">Education</MenuItem>
              <MenuItem value="investment">Investment</MenuItem>
              <MenuItem value="trading">Trading</MenuItem>
              <MenuItem value="other">Other</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Tabs value={tabValue} onChange={handleTabChange} sx={{ mb: 2 }}>
          <Tab label="Upload File" />
          <Tab label="Paste CSV Data" />
        </Tabs>

        {tabValue === 0 && (
          <Box>
            <Paper
              sx={{
                p: 3,
                border: '2px dashed',
                borderColor: file ? 'primary.main' : 'grey.300',
                textAlign: 'center',
                cursor: 'pointer',
                '&:hover': {
                  borderColor: 'primary.main',
                  backgroundColor: 'action.hover'
                }
              }}
              onClick={() => document.getElementById('file-input')?.click()}
            >
              <input
                id="file-input"
                type="file"
                accept=".csv,.txt"
                onChange={handleFileChange}
                style={{ display: 'none' }}
              />
              <CloudUpload sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                {file ? file.name : 'Click to upload CSV file'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Supported formats: .csv, .txt
              </Typography>
            </Paper>
          </Box>
        )}

        {tabValue === 1 && (
          <Box>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="CSV Data"
              value={csvData}
              onChange={(e) => setCsvData(e.target.value)}
              placeholder="Paste your CSV data here..."
              sx={{ mb: 2 }}
            />
            
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                CSV Template:
              </Typography>
              <Paper sx={{ p: 2, backgroundColor: 'grey.50' }}>
                <Typography variant="body2" component="pre" sx={{ fontSize: '0.8rem' }}>
                  {csvTemplate}
                </Typography>
              </Paper>
            </Box>
          </Box>
        )}

        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Required Columns:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <Description fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="symbol" 
                secondary="Stock symbol or ticker (e.g., AAPL, GOOGL)"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <Description fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="quantity" 
                secondary="Number of shares or units"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <Description fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="price" 
                secondary="Average cost per share"
              />
            </ListItem>
          </List>
          
          <Typography variant="subtitle2" gutterBottom sx={{ mt: 2 }}>
            Optional Columns:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemIcon>
                <Description fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="asset_type" 
                secondary="Type of asset (stock, etf, bond, etc.)"
              />
            </ListItem>
            <ListItem>
              <ListItemIcon>
                <Description fontSize="small" />
              </ListItemIcon>
              <ListItemText 
                primary="sector" 
                secondary="Industry sector"
              />
            </ListItem>
          </List>
        </Box>

        {importing && (
          <Box sx={{ mt: 2 }}>
            <LinearProgress />
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              Importing portfolio data...
            </Typography>
          </Box>
        )}

        {importResult && (
          <Box sx={{ mt: 2 }}>
            <Alert 
              severity={importResult.success ? 'success' : 'error'}
              icon={importResult.success ? <CheckCircle /> : <Error />}
            >
              {importResult.message}
            </Alert>
            
            {importResult.errors && importResult.errors.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Alert severity="warning" icon={<Warning />}>
                  <Typography variant="subtitle2" gutterBottom>
                    Validation Errors:
                  </Typography>
                  <List dense>
                    {importResult.errors.map((error, index) => (
                      <ListItem key={index} sx={{ py: 0 }}>
                        <ListItemText 
                          primary={<Typography variant="body2">{error}</Typography>}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Alert>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        <Button onClick={handleClose} disabled={importing}>
          Cancel
        </Button>
        <Button 
          onClick={handleImport} 
          variant="contained" 
          disabled={importing || (!file && !csvData.trim()) || !portfolioName.trim()}
        >
          {importing ? 'Importing...' : 'Import Portfolio'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default PortfolioImportDialog;
