import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const Analytics: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Analytics
      </Typography>
      <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Risk & Performance Analytics
        </Typography>
        <Typography variant="body1">
          Here you'll see comprehensive risk metrics, performance analysis, and portfolio insights.
          Implementation coming in Phase 6-7.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Analytics;
