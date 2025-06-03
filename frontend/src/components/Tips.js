import React from 'react';
import { Typography, Paper, Container, Box } from '@mui/material';

function Tips() {
  return (
    <Container maxWidth="md">
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#FFB300', fontWeight: 700 }}>
          Support Tastory
        </Typography>
        
        <Typography variant="body1" paragraph>
          If you find Tastory helpful and would like to support its development, you can give us a tip! Every contribution helps us maintain and improve the service.
        </Typography>

        <Typography variant="h5" gutterBottom sx={{ mt: 4, color: '#FFB300', fontWeight: 600 }}>
          Scan to Tip
        </Typography>
        
        <Box sx={{ 
          display: 'flex', 
          justifyContent: 'center',
          alignItems: 'center',
          flexDirection: 'column',
          my: 4 
        }}>
          <Box 
            component="img"
            src="/images/tip-qr-code.png"
            alt="Tip QR Code"
            sx={{
              width: 200,
              height: 200,
              border: '2px solid',
              borderColor: '#FFB300',
              borderRadius: 2,
              p: 2,
              mb: 2,
              backgroundColor: 'white',
              boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
              '&:hover': {
                boxShadow: '0 6px 20px rgba(255, 179, 0, 0.3)',
                transform: 'scale(1.05)',
                transition: 'all 0.3s ease'
              }
            }}
            onError={(e) => {
              e.target.style.display = 'none';
            }}
          />
          <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', maxWidth: 300 }}>
            Scan this QR code with your phone's camera to send a tip via PayPal, Venmo, or your preferred payment app
          </Typography>
        </Box>

        <Typography variant="body1" sx={{ mt: 4, textAlign: 'center', fontStyle: 'italic', color: 'text.secondary' }}>
          Thank you for your support! 🙏✨
        </Typography>
      </Paper>
    </Container>
  );
}

export default Tips; 