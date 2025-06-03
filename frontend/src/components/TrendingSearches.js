import React, { useState, useEffect } from 'react';
import { Chip, Box, Typography, CircularProgress } from '@mui/material';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
import WhatshotIcon from '@mui/icons-material/Whatshot';
import { styled } from '@mui/material/styles';

const TrendingContainer = styled(Box)(({ theme }) => ({
  display: 'flex',
  alignItems: 'center',
  gap: theme.spacing(1),
  padding: theme.spacing(2, 0),
  overflowX: 'auto',
  '&::-webkit-scrollbar': {
    height: '4px',
  },
  '&::-webkit-scrollbar-track': {
    backgroundColor: 'transparent',
  },
  '&::-webkit-scrollbar-thumb': {
    backgroundColor: theme.palette.divider,
    borderRadius: '2px',
  },
}));

const TrendingChip = styled(Chip)(({ theme }) => ({
  cursor: 'pointer',
  transition: 'all 0.2s ease',
  '&:hover': {
    transform: 'translateY(-2px)',
    boxShadow: theme.shadows[4],
  },
}));

function TrendingSearches({ onSearchClick, apiUrl }) {
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetchTrending = async () => {
    try {
      const response = await fetch(`${apiUrl}/trending`);
      if (!response.ok) {
        throw new Error('Failed to fetch trending searches');
      }
      const data = await response.json();
      setTrending(data.trending || []);
      setError(null);
    } catch (err) {
      console.error('Error fetching trending:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrending();
    
    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchTrending, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, [apiUrl]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 2 }}>
        <CircularProgress size={24} />
      </Box>
    );
  }

  if (error || trending.length === 0) {
    return null; // Don't show anything if there's an error or no trending data
  }

  return (
    <Box sx={{ mb: 3 }}>
      <TrendingContainer>
        <Box sx={{ display: 'flex', alignItems: 'center', flexShrink: 0 }}>
          <WhatshotIcon sx={{ color: 'error.main', mr: 1 }} />
          <Typography variant="body2" sx={{ fontWeight: 600, whiteSpace: 'nowrap' }}>
            Trending Now:
          </Typography>
        </Box>
        
        {trending.map((item, index) => (
          <TrendingChip
            key={item.query}
            label={item.query}
            onClick={() => onSearchClick(item.query)}
            icon={item.trend === 'up' ? <TrendingUpIcon /> : undefined}
            color={item.trend === 'up' ? 'primary' : 'default'}
            variant={item.trend === 'up' ? 'filled' : 'outlined'}
            size="small"
          />
        ))}
        
        {trending.length > 7 && (
          <Typography variant="caption" sx={{ color: 'text.secondary', flexShrink: 0 }}>
            +{trending.length - 7} more
          </Typography>
        )}
      </TrendingContainer>
    </Box>
  );
}

export default TrendingSearches; 