import React from 'react';
import { Box, Typography, Button, Paper } from '@mui/material';
import { Cancel as CancelIcon } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const SubscriptionCanceled = () => {
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
        <CancelIcon
          sx={{
            fontSize: 64,
            color: 'text.secondary',
            mb: 2,
          }}
        />
        <Typography variant="h4" gutterBottom>
          Subscription Canceled
        </Typography>
        <Typography variant="body1" sx={{ mb: 3 }}>
          Your subscription process was canceled. If you have any questions or concerns,
          please don't hesitate to contact our support team.
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button
            variant="outlined"
            onClick={() => navigate('/')}
            sx={{
              borderColor: '#FFB300',
              color: '#FFB300',
              '&:hover': {
                borderColor: '#FFA000',
                backgroundColor: 'rgba(255, 179, 0, 0.04)',
              },
            }}
          >
            Return Home
          </Button>
          <Button
            variant="contained"
            onClick={() => navigate('/pricing')}
            sx={{
              background: 'linear-gradient(45deg, #FFB300 30%, #FFA000 90%)',
              color: 'black',
              fontWeight: 'bold',
              '&:hover': {
                background: 'linear-gradient(45deg, #FFA000 30%, #FF8F00 90%)',
              },
            }}
          >
            View Plans
          </Button>
        </Box>
      </Paper>
    </Box>
  );
};

export default SubscriptionCanceled; 