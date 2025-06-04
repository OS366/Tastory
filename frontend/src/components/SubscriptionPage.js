import React from 'react';
import {
  Box,
  Container,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
} from '@mui/material';
import {
  Check as CheckIcon,
  Speed as SpeedIcon,
  Analytics as AnalyticsIcon,
  Security as SecurityIcon,
  Star as StarIcon,
} from '@mui/icons-material';
import SubscribeButton from './SubscribeButton';

const SubscriptionPage = () => {
  const benefits = [
    {
      title: 'Advanced Search',
      description: 'Get access to advanced recipe search filters and sorting options',
      icon: <SpeedIcon sx={{ color: '#FFB300' }} />,
    },
    {
      title: 'Recipe Analytics',
      description: 'View detailed nutritional information and cooking insights',
      icon: <AnalyticsIcon sx={{ color: '#FFB300' }} />,
    },
    {
      title: 'Premium Features',
      description: 'Access to meal planning and shopping list generation',
      icon: <StarIcon sx={{ color: '#FFB300' }} />,
    },
    {
      title: 'API Access',
      description: 'Get programmatic access to our recipe database',
      icon: <SecurityIcon sx={{ color: '#FFB300' }} />,
    },
  ];

  return (
    <Container maxWidth="md">
      <Box sx={{ py: 8 }}>
        <Typography
          variant="h3"
          component="h1"
          align="center"
          gutterBottom
          sx={{
            fontWeight: 700,
            background: 'linear-gradient(45deg, #FFB300 30%, #FFA000 90%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          Upgrade to Premium
        </Typography>
        
        <Typography
          variant="h6"
          align="center"
          color="text.secondary"
          paragraph
          sx={{ mb: 6 }}
        >
          Get access to advanced features and support Tastory's development
        </Typography>

        <Paper
          elevation={3}
          sx={{
            p: 4,
            borderRadius: 4,
            background: theme => 
              theme.palette.mode === 'dark' 
                ? 'linear-gradient(145deg, #1e1e1e 0%, #2d2d2d 100%)'
                : 'linear-gradient(145deg, #ffffff 0%, #f5f5f5 100%)',
          }}
        >
          <Box sx={{ mb: 4, textAlign: 'center' }}>
            <Typography
              variant="h4"
              component="div"
              sx={{ 
                fontWeight: 700,
                color: '#FFB300',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 1,
              }}
            >
              $5
              <Typography
                component="span"
                variant="h6"
                color="text.secondary"
                sx={{ fontWeight: 400 }}
              >
                /month
              </Typography>
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <List sx={{ mb: 4 }}>
            {benefits.map((benefit, index) => (
              <ListItem key={index} sx={{ py: 2 }}>
                <ListItemIcon>
                  {benefit.icon}
                </ListItemIcon>
                <ListItemText
                  primary={
                    <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
                      {benefit.title}
                    </Typography>
                  }
                  secondary={benefit.description}
                />
                <CheckIcon sx={{ color: 'success.main', ml: 2 }} />
              </ListItem>
            ))}
          </List>

          <Box sx={{ textAlign: 'center' }}>
            <SubscribeButton />
            <Typography
              variant="body2"
              color="text.secondary"
              sx={{ mt: 2 }}
            >
              Cancel anytime. No commitment required.
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default SubscriptionPage; 