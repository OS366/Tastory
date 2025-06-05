import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { CheckCircle as CheckCircleIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const SubscriptionSuccess = () => {
  const navigate = useNavigate();

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '80vh',
        p: 3,
      }}
    >
      <Paper
        elevation={3}
        sx={{
          p: 4,
          textAlign: 'center',
          maxWidth: 500,
          borderRadius: 2,
        }}
      >
        <CheckCircleIcon
          sx={{
            fontSize: 64,
            color: 'success.main',
            mb: 2,
          }}
        />
        <Typography variant="h4" gutterBottom>
          Welcome to Tastory Premium!
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          Thank you for subscribing. You now have access to all premium features including advanced search,
          analytics, and more.
        </Typography>
        <Button
          variant="contained"
          color="primary"
          onClick={() => navigate('/')}
          sx={{
            background: 'linear-gradient(45deg, #FFB300 30%, #FFA000 90%)',
            color: 'black',
            fontWeight: 'bold',
            px: 4,
            py: 1.5,
            '&:hover': {
              background: 'linear-gradient(45deg, #FFA000 30%, #FF8F00 90%)',
            },
          }}
        >
          Start Exploring
        </Button>
      </Paper>
    </Box>
  );
};

export default SubscriptionSuccess; 