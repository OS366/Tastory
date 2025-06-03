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
          {/* QR Code placeholder - replace src with actual QR code image */}
          <Box 
            component="img"
            alt="Tip QR Code"
            sx={{
              width: 200,
              height: 200,
              border: '2px solid',
              borderColor: '#FFB300',
              borderRadius: 2,
              p: 2,
              mb: 2
            }}
          />
          <Typography variant="body2" color="text.secondary">
            Scan this QR code with your phone's camera to send a tip
          </Typography>
        </Box>

        <Typography variant="body1" sx={{ mt: 4, textAlign: 'center', fontStyle: 'italic', color: 'text.secondary' }}>
          Thank you for your support! 🙏
        </Typography>
      </Paper>
    </Container>
  );
}

export default Tips; 