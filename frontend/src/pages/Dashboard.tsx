import React from 'react';
import { Typography, Paper, Box } from '@mui/material';

const Dashboard: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Dashboard
      </Typography>
      <Paper elevation={3} sx={{ p: 3, mt: 2 }}>
        <Typography variant="h6" gutterBottom>
          Welcome to Portfolio Manager
        </Typography>
        <Typography variant="body1">
          This is the main dashboard where you'll see an overview of your portfolio performance.
          Implementation coming in Phase 5.
        </Typography>
      </Paper>
    </Box>
  );
};

export default Dashboard;
