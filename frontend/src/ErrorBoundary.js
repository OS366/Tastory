import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { RestaurantMenu as RestaurantMenuIcon } from '@mui/icons-material';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Error caught by boundary:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <ErrorPage error={this.state.error} />;
    }

    return this.props.children;
  }
}

export function ErrorPage({ error, onRetry }) {
  const isBackendError = error?.message?.includes('fetch') || 
                        error?.message?.includes('Failed to fetch') ||
                        error?.message?.includes('Network');

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          py: 4
        }}
      >
        <Box sx={{ position: 'relative', mb: 4 }}>
          <RestaurantMenuIcon 
            sx={{ 
              fontSize: 120, 
              color: 'primary.main',
              opacity: 0.3
            }} 
          />
          <Typography
            variant="h1"
            sx={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              fontSize: '4rem',
              fontWeight: 700,
              color: 'primary.main'
            }}
          >
            404
          </Typography>
        </Box>

        <Typography variant="h4" gutterBottom sx={{ fontWeight: 600, mb: 2 }}>
          Oops! Something went wrong
        </Typography>

        <Typography variant="body1" color="text.secondary" sx={{ mb: 4 }}>
          {isBackendError 
            ? "We're having trouble connecting to our recipe database. Our chefs are working on it!"
            : "The page you're looking for seems to have wandered off to the kitchen."}
        </Typography>

        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => window.location.href = '/'}
            sx={{ 
              px: 4,
              py: 1.5,
              borderRadius: 2,
              fontWeight: 600
            }}
          >
            Back to Home
          </Button>
          
          {onRetry && (
            <Button
              variant="outlined"
              color="primary"
              onClick={onRetry}
              sx={{ 
                px: 4,
                py: 1.5,
                borderRadius: 2,
                fontWeight: 600
              }}
            >
              Try Again
            </Button>
          )}
        </Box>

        <Typography 
          variant="caption" 
          color="text.secondary" 
          sx={{ mt: 6, fontStyle: 'italic' }}
        >
          Error: {error?.message || 'Unknown error occurred'}
        </Typography>
      </Box>
    </Container>
  );
}

export default ErrorBoundary; 