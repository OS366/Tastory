import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Button, CircularProgress } from '@mui/material';
import { Star as StarIcon } from '@mui/icons-material';

// Initialize Stripe
const initializeStripe = () => {
  const key = process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY;
  if (!key) {
    console.error('Stripe publishable key is not set. Please check your environment variables.');
    return null;
  }
  return loadStripe(key);
};

const stripePromise = initializeStripe();

const SubscribeButton = () => {
  const [loading, setLoading] = useState(false);

  const handleSubscribe = async () => {
    if (!stripePromise) {
      alert('Stripe is not properly configured. Please contact support.');
      return;
    }

    setLoading(true);
    try {
      const stripe = await stripePromise;
      if (!stripe) {
        throw new Error('Stripe failed to initialize. Please check your publishable key.');
      }

      // Get Checkout Session ID from the server
      const response = await fetch(`${process.env.REACT_APP_API_URL || 'http://localhost:5001'}/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to create checkout session');
      }

      const session = await response.json();
      if (session.error) throw new Error(session.error);

      // Redirect to Checkout
      const result = await stripe.redirectToCheckout({
        sessionId: session.id,
      });

      if (result.error) {
        throw new Error(result.error.message);
      }
    } catch (error) {
      console.error('Error:', error);
      alert('Failed to initialize checkout: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="contained"
      color="primary"
      onClick={handleSubscribe}
      disabled={loading || !stripePromise}
      startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <StarIcon />}
      sx={{
        background: 'linear-gradient(45deg, #FFB300 30%, #FFA000 90%)',
        color: 'black',
        fontWeight: 'bold',
        textTransform: 'none',
        px: 3,
        py: 1,
        borderRadius: 2,
        boxShadow: '0 3px 5px 2px rgba(255, 179, 0, .3)',
        '&:hover': {
          background: 'linear-gradient(45deg, #FFA000 30%, #FF8F00 90%)',
          transform: 'translateY(-1px)',
          boxShadow: '0 4px 8px 2px rgba(255, 179, 0, .4)',
        },
        '&:active': {
          transform: 'translateY(0)',
        },
        '&.Mui-disabled': {
          background: 'linear-gradient(45deg, #ccc 30%, #999 90%)',
          color: '#666',
        }
      }}
    >
      {loading ? 'Processing...' : (!stripePromise ? 'Payment Not Available' : 'Subscribe - $5/month')}
    </Button>
  );
};

export default SubscribeButton; 