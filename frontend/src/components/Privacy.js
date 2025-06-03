import React from 'react';
import { Typography, Paper, Container } from '@mui/material';

function Privacy() {
  return (
    <Container maxWidth="md">
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#FFB300', fontWeight: 700 }}>
          Privacy Policy
        </Typography>
        
        <Typography variant="body1" paragraph>
          At Tastory, we take your privacy seriously. We believe in being transparent about our data collection practices.
        </Typography>

        <Typography variant="h5" gutterBottom sx={{ mt: 4, color: '#FFB300', fontWeight: 600 }}>
          Data Collection
        </Typography>
        
        <Typography variant="body1" paragraph>
          We collect only the minimum data necessary to provide you with the best recipe search experience:
        </Typography>

        <Typography variant="body1" component="div" sx={{ ml: 2, mb: 3 }}>
          • Search Keywords: We collect and analyze search terms to improve our search algorithms and provide trending searches feature.
        </Typography>

        <Typography variant="h5" gutterBottom sx={{ color: '#FFB300', fontWeight: 600 }}>
          What We Don't Collect
        </Typography>
        
        <Typography variant="body1" paragraph>
          We do not collect:
        </Typography>

        <Typography variant="body1" component="div" sx={{ ml: 2 }}>
          • Personal Information
          • User Accounts
          • Browsing History
          • Device Information
          • Cookies
        </Typography>

        <Typography variant="h5" gutterBottom sx={{ mt: 4, color: '#FFB300', fontWeight: 600 }}>
          Local Storage
        </Typography>
        
        <Typography variant="body1" paragraph>
          Your favorites and theme preferences are stored locally on your device and are never transmitted to our servers.
        </Typography>

        <Typography variant="body1" sx={{ mt: 4, fontStyle: 'italic', color: 'text.secondary' }}>
          For any privacy concerns, please contact us at privacy@davidlabs.ca
        </Typography>
      </Paper>
    </Container>
  );
}

export default Privacy; 