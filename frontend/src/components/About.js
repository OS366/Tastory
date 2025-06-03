import React from 'react';
import { Box, Typography, Paper, Container, Link } from '@mui/material';

function About() {
  return (
    <Container maxWidth="md">
      <Paper sx={{ p: 4, mt: 4 }}>
        <Typography variant="h4" component="h1" gutterBottom sx={{ color: '#FFB300', fontWeight: 700 }}>
          About Tastory
        </Typography>
        
        <Typography variant="body1" paragraph>
          Tastory is a powerful recipe search engine built on top of Food.com, one of the world's largest food communities. Our AI-powered search helps you find the perfect recipe from Food.com's extensive collection.
        </Typography>

        <Typography variant="h5" gutterBottom sx={{ mt: 4, color: '#FFB300', fontWeight: 600 }}>
          Key Features
        </Typography>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="body1" paragraph>
            • Natural Language Search: Ask for recipes in plain English
          </Typography>
          <Typography variant="body1" paragraph>
            • Smart Filtering: Find recipes by ingredients, cuisine, or dietary restrictions
          </Typography>
          <Typography variant="body1" paragraph>
            • Real-time Translation: Recipes available in multiple languages
          </Typography>
          <Typography variant="body1" paragraph>
            • Voice Support: Listen to recipe instructions hands-free
          </Typography>
        </Box>

        <Typography variant="h5" gutterBottom sx={{ color: '#FFB300', fontWeight: 600 }}>
          Food.com Statistics
        </Typography>
        
        <Box sx={{ mb: 4 }}>
          <Typography variant="body1" paragraph>
            • Over 500,000 user-submitted recipes
          </Typography>
          <Typography variant="body1" paragraph>
            • More than 125 million recipe ratings and reviews
          </Typography>
          <Typography variant="body1" paragraph>
            • Active community of home cooks since 1999
          </Typography>
        </Box>

        <Typography variant="h5" gutterBottom sx={{ color: '#FFB300', fontWeight: 600 }}>
          About David Labs
        </Typography>
        
        <Typography variant="body1" paragraph>
          Tastory is a product of{' '}
          <Link 
            href="https://www.davidlabs.ca" 
            target="_blank" 
            rel="noopener noreferrer"
            sx={{ 
              color: '#FFB300',
              textDecoration: 'none',
              '&:hover': {
                textDecoration: 'underline',
                color: '#FFA000'
              }
            }}
          >
            David Labs
          </Link>
          , a technology company focused on building innovative AI-powered solutions. We're passionate about combining cutting-edge technology with everyday needs to create useful and accessible tools.
        </Typography>

        <Typography variant="body1" sx={{ mt: 4, fontStyle: 'italic', color: 'text.secondary' }}>
          Tastory is an independent project and is not officially affiliated with Food.com. We simply help you search their amazing recipe collection more effectively.
        </Typography>
      </Paper>
    </Container>
  );
}

export default About; 