import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const Optimization: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Portfolio Optimization
      </Typography>
      <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Modern Portfolio Theory & Optimization
        </Typography>
        <Typography variant="body1">
          Here you'll optimize your portfolio allocation using efficient frontier analysis and various optimization strategies.
          Implementation coming in Phase 8.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Optimization;
