import React from 'react';
import { 
  Box, 
  CircularProgress, 
  Typography, 
  Alert, 
  Backdrop,
  Paper
} from '@mui/material';

interface LoadingStateProps {
  message?: string;
  backdrop?: boolean;
}

export const LoadingState: React.FC<LoadingStateProps> = ({ 
  message = 'Loading...', 
  backdrop = false 
}) => {
  const content = (
    <Box 
      display="flex" 
      flexDirection="column" 
      alignItems="center" 
      justifyContent="center"
      gap={2}
      p={3}
    >
      <CircularProgress size={40} />
      <Typography variant="body2" color="text.secondary">
        {message}
      </Typography>
    </Box>
  );

  if (backdrop) {
    return (
      <Backdrop open={true} sx={{ zIndex: 1000 }}>
        <Paper sx={{ p: 3 }}>
          {content}
        </Paper>
      </Backdrop>
    );
  }

  return content;
};

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
  severity?: 'error' | 'warning' | 'info';
}

export const ErrorState: React.FC<ErrorStateProps> = ({ 
  message, 
  onRetry, 
  severity = 'error' 
}) => {
  return (
    <Alert 
      severity={severity} 
      action={
        onRetry && (
          <Box 
            component="button" 
            onClick={onRetry}
            sx={{ 
              background: 'none', 
              border: 'none', 
              color: 'inherit', 
              cursor: 'pointer',
              textDecoration: 'underline'
            }}
          >
            Retry
          </Box>
        )
      }
    >
      {message}
    </Alert>
  );
};

interface EmptyStateProps {
  message: string;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({ message, action }) => {
  return (
    <Box 
      display="flex" 
      flexDirection="column" 
      alignItems="center" 
      justifyContent="center"
      gap={2}
      p={3}
    >
      <Typography variant="h6" color="text.secondary">
        {message}
      </Typography>
      {action}
    </Box>
  );
};
