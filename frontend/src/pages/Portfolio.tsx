import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const Portfolio: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Portfolio
      </Typography>
      <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Portfolio Management
        </Typography>
        <Typography variant="body1">
          Here you'll manage your portfolio holdings, import data, and view current positions.
          Implementation coming in Phase 5.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Portfolio;
