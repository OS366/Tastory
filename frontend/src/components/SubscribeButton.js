import React, { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { Button, CircularProgress } from '@mui/material';
import { Star as StarIcon } from '@mui/icons-material';

// Initialize Stripe
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLIC_KEY);

const SubscribeButton = () => {
  const [loading, setLoading] = useState(false);

  const handleSubscribe = async () => {
    setLoading(true);
    try {
      const stripe = await stripePromise;
      if (!stripe) throw new Error('Stripe failed to initialize');

      // Get Checkout Session ID from the server
      const response = await fetch(`${process.env.REACT_APP_API_URL}/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });

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
      alert('Failed to initialize checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Button
      variant="contained"
      color="primary"
      onClick={handleSubscribe}
      disabled={loading}
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
      }}
    >
      {loading ? 'Processing...' : 'Subscribe - $5/month'}
    </Button>
  );
};

export default SubscribeButton; 