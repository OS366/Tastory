import React, { useState, useEffect } from 'react';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  Container,
  Box,
  Typography,
  TextField,
  Button,
  Grid,
  Card,
  CardMedia,
  CardContent,
  CardActions,
  IconButton,
  Badge,
  AppBar,
  Toolbar,
  InputAdornment,
  Autocomplete,
  Chip,
  CircularProgress,
  Pagination,
  useMediaQuery,
  Paper,
  Drawer,
  List,
  ListItem,
  ListItemText,
  Rating,
  Fab,
  Tooltip,
  Dialog,
  DialogContent
} from '@mui/material';
import {
  Search as SearchIcon,
  Favorite as FavoriteIcon,
  FavoriteBorder as FavoriteBorderIcon,
  DarkMode as DarkModeIcon,
  LightMode as LightModeIcon,
  Info as InfoIcon,
  RestaurantMenu as IngredientsIcon,
  MenuBook as InstructionsIcon,
  DonutSmall as NutritionIcon,
  Close as CloseIcon,
  VolumeUp as VolumeUpIcon,
  Stop as StopIcon,
  RestaurantMenu as RestaurantMenuIcon
} from '@mui/icons-material';
import ErrorBoundary, { ErrorPage } from './ErrorBoundary';
import TrendingSearches from './components/TrendingSearches';
import About from './components/About';
import Privacy from './components/Privacy';
import Tips from './components/Tips';
import SubscriptionPage from './components/SubscriptionPage';

function App() {
  const [darkMode, setDarkMode] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);
  const [favorites, setFavorites] = useState({});
  const [showFavorites, setShowFavorites] = useState(false);
  const [suggestions, setSuggestions] = useState([]);
  const [recentSearches, setRecentSearches] = useState([]);
  const [selectedRecipe, setSelectedRecipe] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [drawerContent, setDrawerContent] = useState('info');
  const [suggestionTimer, setSuggestionTimer] = useState(null);
  const [browserLang, setBrowserLang] = useState('en');
  const [backendError, setBackendError] = useState(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [dialogContent, setDialogContent] = useState(null);

  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  // Get API URL - safe for browser environment
  const getApiUrl = () => {
    // Check if we're in production (Firebase hosting)
    if (window.location.hostname === 'tastory-hackathon.web.app' || 
        window.location.hostname === 'tastory-hackathon.firebaseapp.com') {
      return 'https://tastory-api-vbx2teipca-uc.a.run.app';
    }
    
    // Check if process.env exists and has our variable
    if (typeof process !== 'undefined' && process.env && process.env.REACT_APP_API_URL) {
      return process.env.REACT_APP_API_URL;
    }
    
    // Default to localhost for development
    return 'http://localhost:5001';
  };

  const API_URL = getApiUrl();

  // Create gold theme
  const theme = createTheme({
    palette: {
      mode: darkMode ? 'dark' : 'light',
      primary: {
        main: '#FFB300', // Gold 500
        light: '#FFD700', // Gold 300
        dark: '#FF8F00', // Gold 700
      },
      secondary: {
        main: '#FFA000', // Gold 600
      },
      background: {
        default: darkMode ? '#121212' : '#f5f5f5',
        paper: darkMode ? '#1e1e1e' : '#ffffff',
      },
    },
    typography: {
      h1: {
        fontSize: '2.5rem',
        fontWeight: 700,
      },
      h2: {
        fontSize: '2rem',
        fontWeight: 600,
      },
      h3: {
        fontSize: '1.5rem',
        fontWeight: 600,
      },
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: 'none',
            fontWeight: 600,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
            boxShadow: '0 4px 12px rgba(0,0,0,0.1)',
            transition: 'box-shadow 0.3s ease',
            '&:hover': {
              boxShadow: '0 8px 24px rgba(0,0,0,0.15)',
            },
          },
        },
      },
      MuiTextField: {
        styleOverrides: {
          root: {
            '& .MuiOutlinedInput-root': {
              borderRadius: 8,
            },
          },
        },
      },
    },
  });

  // Load favorites from localStorage
  useEffect(() => {
    const savedFavorites = localStorage.getItem('tastoryFavorites');
    if (savedFavorites) {
      setFavorites(JSON.parse(savedFavorites));
    }
    
    const savedSearches = localStorage.getItem('tastoryRecentSearches');
    if (savedSearches) {
      setRecentSearches(JSON.parse(savedSearches));
    }
    
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      setDarkMode(savedTheme === 'dark');
    }
    // If no saved theme, keep the default (true for dark mode)
  }, []);

  // Save theme preference
  useEffect(() => {
    localStorage.setItem('theme', darkMode ? 'dark' : 'light');
  }, [darkMode]);

  // Clean up suggestion timer on unmount
  useEffect(() => {
    return () => {
      if (suggestionTimer) {
        clearTimeout(suggestionTimer);
      }
    };
  }, [suggestionTimer]);

  // Fetch search suggestions
  const fetchSuggestions = async (query) => {
    if (query.length < 2) {
      setSuggestions([]);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/suggest?query=${encodeURIComponent(query)}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setSuggestions(data);
      setBackendError(null); // Clear any previous errors
    } catch (error) {
      console.error('Error fetching suggestions:', error);
      setSuggestions([]);
      // Don't set backend error for suggestions - just fail silently
    }
  };

  // Search functionality
  const handleSearch = async (query, pageNum = 1) => {
    if (!query) return;
    
    setLoading(true);
    setSearchQuery(query);
    setBackendError(null);
    
    try {
      const response = await fetch(`${API_URL}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: query, page: pageNum }),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (data.success && data.recipes) {
        // Process the JSON response directly
        const recipes = data.recipes.map((recipe) => ({
          id: recipe.id,
          name: recipe.name,
          calories: recipe.calories,
          image: recipe.image || '',
          rating: recipe.rating || '0',
          reviews: recipe.reviews || '0',
          url: recipe.url || '',
          ingredients: recipe.ingredients || [],
          instructions: recipe.instructions || [],
          nutrition: recipe.nutrition || {},
          additionalInfo: recipe.additionalInfo || {}
        }));
        
        setSearchResults(recipes);
        setTotalPages(data.totalPages || 1);
        setPage(data.currentPage || pageNum);
        
        // Save to recent searches
        const updatedSearches = [query, ...recentSearches.filter(s => s !== query)].slice(0, 5);
        setRecentSearches(updatedSearches);
        localStorage.setItem('tastoryRecentSearches', JSON.stringify(updatedSearches));
      } else {
        // Handle error or no results
        setSearchResults([]);
        setTotalPages(0);
        console.error('Search failed:', data.error);
      }
    } catch (error) {
      console.error('Search error:', error);
      setSearchResults([]);
      setTotalPages(0);
      setBackendError(error);
    } finally {
      setLoading(false);
    }
  };

  // Toggle favorite
  const toggleFavorite = (recipe) => {
    const newFavorites = { ...favorites };
    if (newFavorites[recipe.id]) {
      delete newFavorites[recipe.id];
    } else {
      newFavorites[recipe.id] = {
        ...recipe,
        dateAdded: new Date().toISOString(),
      };
    }
    setFavorites(newFavorites);
    localStorage.setItem('tastoryFavorites', JSON.stringify(newFavorites));
  };

  // Detect browser language
  useEffect(() => {
    const lang = navigator.language || navigator.userLanguage || 'en';
    // Extract the primary language code (e.g., 'es' from 'es-ES')
    const primaryLang = lang.split('-')[0];
    
    // Use actual browser language
    setBrowserLang(primaryLang);
    console.log('Browser language detected:', lang, 'Primary:', primaryLang);
  }, []);

  // If there's a backend error, show the error page
  if (backendError) {
    return (
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <ErrorPage 
          error={backendError} 
          onRetry={() => {
            setBackendError(null);
            if (searchQuery) {
              handleSearch(searchQuery, page);
            }
          }}
        />
      </ThemeProvider>
    );
  }

  const handleNavClick = (content) => {
    setDialogContent(content);
    setDialogOpen(true);
  };

  const handleDialogClose = () => {
    setDialogOpen(false);
  };

  const renderDialogContent = () => {
    switch (dialogContent) {
      case 'about':
        return <About />;
      case 'tips':
        return <Tips />;
      case 'privacy':
        return <Privacy />;
      case 'subscribe':
        return <SubscriptionPage />;
      default:
        return null;
    }
  };

  return (
    <ErrorBoundary>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        
        <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
          {/* Header */}
          <AppBar position="static" color="transparent" elevation={0} sx={{ mb: 4 }}>
            <Toolbar sx={{ justifyContent: 'space-between' }}>
              {/* Left side navigation */}
              <Box sx={{ display: 'flex', gap: 3 }}>
                <Typography
                  component="button"
                  onClick={() => handleNavClick('about')}
                  sx={{
                    background: 'none',
                    border: 'none',
                    color: 'text.secondary',
                    cursor: 'pointer',
                    '&:hover': { color: 'primary.main' },
                    transition: 'color 0.2s'
                  }}
                >
                  About
                </Typography>
                <Typography
                  component="button"
                  onClick={() => handleNavClick('subscribe')}
                  sx={{
                    background: 'none',
                    border: 'none',
                    color: 'primary.main',
                    cursor: 'pointer',
                    fontWeight: 'bold',
                    '&:hover': { color: 'primary.dark' },
                    transition: 'color 0.2s'
                  }}
                >
                  Upgrade
                </Typography>
                <Typography
                  component="button"
                  onClick={() => handleNavClick('tips')}
                  sx={{
                    background: 'none',
                    border: 'none',
                    color: 'text.secondary',
                    cursor: 'pointer',
                    '&:hover': { color: 'primary.main' },
                    transition: 'color 0.2s'
                  }}
                >
                  Tips
                </Typography>
                <Typography
                  component="button"
                  onClick={() => handleNavClick('privacy')}
                  sx={{
                    background: 'none',
                    border: 'none',
                    color: 'text.secondary',
                    cursor: 'pointer',
                    '&:hover': { color: 'primary.main' },
                    transition: 'color 0.2s'
                  }}
                >
                  Privacy
                </Typography>
              </Box>

              {/* Right side icons */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Tooltip title={`Switch to ${darkMode ? 'light' : 'dark'} mode`}>
                  <IconButton onClick={() => setDarkMode(!darkMode)} color="inherit">
                    {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
                  </IconButton>
                </Tooltip>
                <Tooltip title="View favorites">
                  <IconButton
                    onClick={() => setShowFavorites(!showFavorites)}
                    color={showFavorites ? 'primary' : 'inherit'}
                  >
                    <Badge badgeContent={Object.keys(favorites).length} color="primary">
                      {showFavorites ? <FavoriteIcon /> : <FavoriteBorderIcon />}
                    </Badge>
                  </IconButton>
                </Tooltip>
              </Box>
            </Toolbar>
          </AppBar>

          <Container maxWidth="xl" sx={{ py: 4 }}>
            {/* Logo and Title Section */}
            <Box sx={{ textAlign: 'center', mb: 6 }}>
              <Box sx={{ position: 'relative', display: 'inline-block', mb: 2 }}>
                <img 
                  src="/images/logo.png" 
                  alt="Tastory Logo" 
                  style={{ 
                    width: 100, 
                    height: 100, 
                    borderRadius: '50%', 
                    border: '4px solid #FFB300' 
                  }}
                />
                <Chip 
                  label="BETA" 
                  size="small" 
                  color="primary"
                  sx={{ 
                    position: 'absolute', 
                    top: -5, 
                    right: -5,
                    fontWeight: 700,
                    fontSize: '0.7rem'
                  }}
                />
              </Box>
              <Typography variant="h1" component="h1" sx={{ mb: 1, color: 'primary.main', fontWeight: 800 }}>
                Tastory
              </Typography>
              <Typography variant="h5" component="h2" sx={{ mb: 3, color: 'text.secondary', fontWeight: 300 }}>
                The Food Search Engine
              </Typography>

              {/* Search Bar */}
              <Box sx={{ mb: 4 }}>
                <Box sx={{ 
                  maxWidth: 600, 
                  mx: 'auto'
                }}>
                  <Autocomplete
                    freeSolo
                    options={suggestions}
                    inputValue={searchQuery}
                    onInputChange={(event, newValue) => {
                      setSearchQuery(newValue);
                      
                      // Clear existing timer
                      if (suggestionTimer) {
                        clearTimeout(suggestionTimer);
                      }
                      
                      // Set new timer for debounced suggestion fetch
                      const newTimer = setTimeout(() => {
                        fetchSuggestions(newValue);
                      }, 300);
                      
                      setSuggestionTimer(newTimer);
                    }}
                    renderOption={(props, option) => (
                      <Box 
                        component="li" 
                        {...props} 
                        sx={{ 
                          py: 1.5, 
                          px: 2,
                          '&:hover': {
                            backgroundColor: theme => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 179, 0, 0.08)',
                          }
                        }}
                      >
                        <SearchIcon sx={{ mr: 1.5, color: 'text.secondary', fontSize: 20 }} />
                        <Typography variant="body2" sx={{ fontWeight: 500 }}>{option}</Typography>
                      </Box>
                    )}
                    sx={{
                      '& .MuiAutocomplete-popupIndicator': { display: 'none' },
                      '& .MuiAutocomplete-clearIndicator': { display: 'none' }
                    }}
                    componentsProps={{
                      paper: {
                        sx: {
                          mt: 1,
                          borderRadius: '12px',
                          boxShadow: '0 4px 20px rgba(0,0,0,0.1)',
                          border: theme => theme.palette.mode === 'dark' ? '1px solid rgba(255, 255, 255, 0.1)' : 'none',
                        }
                      }
                    }}
                    renderInput={(params) => (
                      <TextField
                        {...params}
                        fullWidth
                        placeholder="Search for any recipe, ingredient, or cuisine..."
                        variant="outlined"
                        onKeyPress={(event) => {
                          if (event.key === 'Enter' && searchQuery.trim()) {
                            event.preventDefault();
                            handleSearch(searchQuery);
                          }
                        }}
                        sx={{
                          '& .MuiOutlinedInput-root': {
                            paddingRight: '4px',
                            backgroundColor: theme => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.09)' : '#fff',
                            border: '1px solid',
                            borderColor: theme => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.23)' : 'rgba(0, 0, 0, 0.23)',
                            borderRadius: '12px',
                            transition: 'all 0.2s ease',
                            '&:hover': {
                              borderColor: theme => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.4)' : 'rgba(0, 0, 0, 0.4)',
                              backgroundColor: theme => theme.palette.mode === 'dark' ? 'rgba(255, 255, 255, 0.11)' : '#fff',
                            },
                            '&.Mui-focused': {
                              borderColor: '#FFB300',
                              boxShadow: '0 0 0 2px rgba(255, 179, 0, 0.1)',
                            },
                            '& fieldset': {
                              border: 'none',
                            }
                          },
                          '& .MuiInputBase-input': {
                            fontSize: { xs: '0.875rem', sm: '1rem' },
                            fontWeight: 500,
                          }
                        }}
                        InputProps={{
                          ...params.InputProps,
                          sx: {
                            height: { xs: 48, sm: 56 },
                            pr: { xs: '110px', sm: '130px' },
                            display: 'flex',
                            alignItems: 'center',
                            position: 'relative',
                            '& .MuiInputBase-input': {
                              pr: 0
                            },
                            '& .MuiAutocomplete-endAdornment': {
                              display: 'none'
                            }
                          },
                          endAdornment: (
                            <Box sx={{ 
                              position: 'absolute',
                              right: 8,
                              top: '50%',
                              transform: 'translateY(-50%)',
                              display: 'flex', 
                              alignItems: 'center',
                              zIndex: 1
                            }}>
                              <Button
                                variant="contained"
                                color="primary"
                                onClick={() => handleSearch(searchQuery)}
                                startIcon={<SearchIcon />}
                                sx={{ 
                                  height: { xs: 36, sm: 40 },
                                  borderRadius: '8px',
                                  px: { xs: 2, sm: 3 },
                                  fontSize: { xs: '0.875rem', sm: '1rem' },
                                  fontWeight: 600,
                                  boxShadow: 'none',
                                  textTransform: 'none',
                                  background: '#FFB300',
                                  color: '#000',
                                  transition: 'all 0.2s ease',
                                  '&:hover': {
                                    background: '#FFA000',
                                    boxShadow: '0 2px 8px rgba(255, 179, 0, 0.3)',
                                    transform: 'translateY(-1px)',
                                  },
                                  '&:active': {
                                    transform: 'translateY(0) scale(0.98)',
                                  },
                                  '& .MuiButton-startIcon': {
                                    mr: { xs: 0.5, sm: 1 }
                                  }
                                }}
                              >
                                Search
                              </Button>
                            </Box>
                          ),
                        }}
                      />
                    )}
                  />
                </Box>
              </Box>

              {/* Trending Searches - between search bar and banner */}
              <Box sx={{ 
                maxWidth: 800, 
                mx: 'auto',
                mb: 3,
                mt: 2,
                px: 2
              }}>
                <TrendingSearches onSearchClick={handleSearch} apiUrl={API_URL} />
              </Box>

              {/* Recent Searches */}
              {recentSearches.length > 0 && !showFavorites && (
                <Box sx={{ mb: 4, maxWidth: 800, mx: 'auto' }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                    <Typography variant="h6" sx={{ flexGrow: 1 }}>
                      Recent Searches
                    </Typography>
                    <Button 
                      size="small" 
                      onClick={() => {
                        setRecentSearches([]);
                        localStorage.removeItem('tastoryRecentSearches');
                      }}
                      sx={{ textTransform: 'none', color: 'text.secondary' }}
                    >
                      Clear history
                    </Button>
                  </Box>
                  <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                    {recentSearches.map((search, index) => (
                      <Chip
                        key={index}
                        label={search}
                        onClick={() => handleSearch(search)}
                        onDelete={() => {
                          const newSearches = recentSearches.filter((_, i) => i !== index);
                          setRecentSearches(newSearches);
                          localStorage.setItem('tastoryRecentSearches', JSON.stringify(newSearches));
                        }}
                        color="primary"
                        variant="outlined"
                        icon={<SearchIcon sx={{ fontSize: 16 }} />}
                        sx={{ 
                          '&:hover': { 
                            backgroundColor: 'primary.main',
                            color: 'primary.contrastText',
                            '& .MuiChip-deleteIcon': {
                              color: 'primary.contrastText'
                            }
                          }
                        }}
                      />
                    ))}
                  </Box>
                </Box>
              )}

              {/* Loading */}
              {loading && (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                  <CircularProgress size={60} />
                </Box>
              )}

              {/* Results or Favorites */}
              {!loading && (
                <>
                  {showFavorites ? (
                    // Favorites View
                    <Box>
                      <Typography variant="h4" gutterBottom>
                        Your Favorite Recipes
                      </Typography>
                      <Grid 
                        container 
                        spacing={2}
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: {
                            xs: '1fr',
                            sm: 'repeat(2, 1fr)',
                            md: 'repeat(3, 1fr)',
                            lg: 'repeat(4, 1fr)'
                          },
                          gap: 2
                        }}
                      >
                        {Object.values(favorites).map((recipe) => (
                          <Box key={recipe.id}>
                            <RecipeCard
                              recipe={recipe}
                              isFavorite={true}
                              onToggleFavorite={() => toggleFavorite(recipe)}
                              onOpenDetails={() => {
                                setSelectedRecipe(recipe);
                                setDrawerOpen(true);
                              }}
                            />
                          </Box>
                        ))}
                      </Grid>
                    </Box>
                  ) : (
                    // Search Results
                    <>
                      {searchResults.length > 0 && (
                        <Box sx={{ mb: 3, color: 'text.secondary' }}>
                          <Typography variant="body2">
                            About {totalPages * 12} results found for "<strong>{searchQuery}</strong>" in 0.{Math.floor(Math.random() * 9) + 1}s
                          </Typography>
                        </Box>
                      )}
                      
                      <Grid 
                        container 
                        spacing={2}
                        sx={{
                          display: 'grid',
                          gridTemplateColumns: {
                            xs: '1fr',
                            sm: 'repeat(2, 1fr)',
                            md: 'repeat(3, 1fr)',
                            lg: 'repeat(4, 1fr)'
                          },
                          gap: 2
                        }}
                      >
                        {searchResults.map((recipe) => (
                          <Box key={recipe.id}>
                            <RecipeCard
                              recipe={recipe}
                              isFavorite={!!favorites[recipe.id]}
                              onToggleFavorite={() => toggleFavorite(recipe)}
                              onOpenDetails={() => {
                                setSelectedRecipe(recipe);
                                setDrawerOpen(true);
                              }}
                            />
                          </Box>
                        ))}
                      </Grid>

                      {/* Pagination */}
                      {totalPages > 1 && (
                        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
                          <Pagination
                            count={totalPages}
                            page={page}
                            onChange={(e, value) => handleSearch(searchQuery, value)}
                            color="primary"
                            size="large"
                          />
                        </Box>
                      )}
                    </>
                  )}
                </>
              )}
            </Box>
          </Container>

          {/* Recipe Details Drawer */}
          <RecipeDrawer
            open={drawerOpen}
            onClose={() => setDrawerOpen(false)}
            recipe={selectedRecipe}
            drawerContent={drawerContent}
            setDrawerContent={setDrawerContent}
            browserLang={browserLang}
          />

          {/* Dialog for About, Tips, Privacy, and Subscribe */}
          <Dialog
            open={dialogOpen}
            onClose={handleDialogClose}
            maxWidth="md"
            fullWidth
            sx={{
              '& .MuiDialog-paper': {
                borderRadius: 3,
                m: 2,
              }
            }}
          >
            <DialogContent sx={{ p: 0 }}>
              {renderDialogContent()}
            </DialogContent>
          </Dialog>
        </Box>
      </ThemeProvider>
    </ErrorBoundary>
  );
}

// Recipe Card Component
function RecipeCard({ recipe, isFavorite, onToggleFavorite, onOpenDetails }) {
  return (
    <Card sx={{ 
      height: 360, // Slightly reduced height for better fit
      width: '100%',
      display: 'flex', 
      flexDirection: 'column',
      transition: 'transform 0.2s ease, box-shadow 0.2s ease',
      overflow: 'hidden',
      '&:hover': {
        transform: 'translateY(-4px)',
      }
    }}>
      <Box sx={{ height: 180, overflow: 'hidden', flexShrink: 0, position: 'relative' }}>
        {recipe.image ? (
          <CardMedia
            component="img"
            height="180"
            image={recipe.image}
            alt={recipe.name}
            onClick={() => window.open(recipe.url, '_blank')}
            sx={{ 
              cursor: 'pointer',
              objectFit: 'cover',
              width: '100%',
              height: '100%',
              position: 'absolute',
              top: 0,
              left: 0
            }}
          />
        ) : (
          <Box
            sx={{
              height: '100%',
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              backgroundColor: theme => theme.palette.mode === 'dark' ? 'grey.800' : 'grey.100',
              cursor: 'pointer',
            }}
            onClick={() => window.open(recipe.url, '_blank')}
          >
            <Box
              sx={{
                textAlign: 'center',
                p: 2
              }}
            >
              <IngredientsIcon
                sx={{
                  fontSize: 48,
                  color: theme => theme.palette.mode === 'dark' ? 'grey.600' : 'grey.400',
                  mb: 0.5
                }}
              />
              <Typography
                variant="body2"
                sx={{
                  color: theme => theme.palette.mode === 'dark' ? 'grey.500' : 'grey.600',
                  fontStyle: 'italic',
                  fontSize: '0.8rem'
                }}
              >
                No image available
              </Typography>
            </Box>
          </Box>
        )}
      </Box>
      
      <CardContent sx={{ 
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        p: 1.5,
        pb: 1
      }}>
        <Typography 
          variant="h6" 
          sx={{
            fontSize: '0.95rem',
            fontWeight: 600,
            lineHeight: 1.2,
            height: '2.4em',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            display: '-webkit-box',
            WebkitLineClamp: 2,
            WebkitBoxOrient: 'vertical',
            mb: 0.5
          }}
        >
          {recipe.name}
        </Typography>
        
        <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5, fontSize: '0.8rem' }}>
          Calories: {recipe.calories}
        </Typography>
        
        <Box sx={{ mt: 'auto', display: 'flex', alignItems: 'center' }}>
          <Rating 
            value={parseFloat(recipe.rating) || 0} 
            readOnly 
            size="small"
            sx={{ color: 'primary.main', fontSize: '1rem' }}
          />
          <Typography variant="caption" sx={{ ml: 0.5, fontSize: '0.7rem' }}>
            ({recipe.reviews} reviews)
          </Typography>
        </Box>
      </CardContent>
      
      <CardActions sx={{ 
        p: 0.5,
        height: 44,
        flexShrink: 0
      }}>
        <IconButton onClick={onToggleFavorite} color="error" size="small">
          {isFavorite ? <FavoriteIcon fontSize="small" /> : <FavoriteBorderIcon fontSize="small" />}
        </IconButton>
        <Box sx={{ flexGrow: 1 }} />
        <IconButton onClick={onOpenDetails} size="small">
          <InfoIcon fontSize="small" />
        </IconButton>
      </CardActions>
    </Card>
  );
}

// Recipe Details Drawer Component
function RecipeDrawer({ open, onClose, recipe, drawerContent, setDrawerContent, browserLang }) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [currentUtterance, setCurrentUtterance] = useState(null);
  const [voicesLoaded, setVoicesLoaded] = useState(false);

  // TODO: Future Features
  // 1. AI Cooking Coach - Step-by-step voice guidance with timers
  // 2. Ingredient substitution suggestions based on dietary restrictions
  // 3. Cooking technique videos linked to each step
  // 4. Real-time cooking Q&A during recipe preparation

  // Initialize speech synthesis
  const synth = window.speechSynthesis;

  // Translation dictionary for common cooking terms
  const translations = {
    es: { // Spanish
      'Here are the recipe details': 'Aquí están los detalles de la receta',
      'Created by': 'Creado por',
      'Published on': 'Publicado el',
      'Preparation time is': 'El tiempo de preparación es',
      'Here are the ingredients you will need': 'Estos son los ingredientes que necesitarás',
      'That\'s all the ingredients': 'Esos son todos los ingredientes',
      'No ingredients information is available for this recipe': 'No hay información de ingredientes disponible para esta receta',
      'Here are the cooking instructions': 'Estas son las instrucciones de cocina',
      'Step': 'Paso',
      'Enjoy your meal': 'Disfruta tu comida',
      'No instructions are available for this recipe': 'No hay instrucciones disponibles para esta receta',
      'Nutrition information per serving': 'Información nutricional por porción',
      'contains': 'contiene',
      'content is': 'el contenido es',
      'No nutrition information is available for this recipe': 'No hay información nutricional disponible para esta receta',
      'to': 'a', // for number ranges like "1 to 2"
      'minutes': 'minutos',
      'Servings': 'Porciones',
      'Author': 'Autor',
      'Category': 'Categoría',
      'Prep Time': 'Tiempo de preparación'
    },
    fr: { // French
      'Here are the recipe details': 'Voici les détails de la recette',
      'Created by': 'Créé par',
      'Published on': 'Publié le',
      'Preparation time is': 'Le temps de préparation est',
      'Here are the ingredients you will need': 'Voici les ingrédients dont vous aurez besoin',
      'That\'s all the ingredients': 'C\'est tous les ingrédients',
      'No ingredients information is available for this recipe': 'Aucune information sur les ingrédients n\'est disponible pour cette recette',
      'Here are the cooking instructions': 'Voici les instructions de cuisson',
      'Step': 'Étape',
      'Enjoy your meal': 'Bon appétit',
      'No instructions are available for this recipe': 'Aucune instruction n\'est disponible pour cette recette',
      'Nutrition information per serving': 'Informations nutritionnelles par portion',
      'contains': 'contient',
      'content is': 'le contenu est',
      'No nutrition information is available for this recipe': 'Aucune information nutritionnelle n\'est disponible pour cette recette',
      'to': 'à',
      'minutes': 'minutes',
      'Servings': 'Portions',
      'Author': 'Auteur',
      'Category': 'Catégorie',
      'Prep Time': 'Temps de préparation'
    },
    de: { // German
      'Here are the recipe details': 'Hier sind die Rezeptdetails',
      'Created by': 'Erstellt von',
      'Published on': 'Veröffentlicht am',
      'Preparation time is': 'Die Zubereitungszeit beträgt',
      'Here are the ingredients you will need': 'Hier sind die Zutaten, die Sie benötigen',
      'That\'s all the ingredients': 'Das sind alle Zutaten',
      'No ingredients information is available for this recipe': 'Für dieses Rezept sind keine Informationen zu den Zutaten verfügbar',
      'Here are the cooking instructions': 'Hier sind die Kochanweisungen',
      'Step': 'Schritt',
      'Enjoy your meal': 'Guten Appetit',
      'No instructions are available for this recipe': 'Für dieses Rezept sind keine Anweisungen verfügbar',
      'Nutrition information per serving': 'Nährwertangaben pro Portion',
      'contains': 'enthält',
      'content is': 'der Inhalt ist',
      'No nutrition information is available for this recipe': 'Für dieses Rezept sind keine Nährwertangaben verfügbar',
      'to': 'bis',
      'minutes': 'Minuten',
      'Servings': 'Portionen',
      'Author': 'Autor',
      'Category': 'Kategorie',
      'Prep Time': 'Zubereitungszeit'
    },
    it: { // Italian
      'Here are the recipe details': 'Ecco i dettagli della ricetta',
      'Created by': 'Creato da',
      'Published on': 'Pubblicato il',
      'Preparation time is': 'Il tempo di preparazione è',
      'Here are the ingredients you will need': 'Ecco gli ingredienti di cui avrai bisogno',
      'That\'s all the ingredients': 'Questi sono tutti gli ingredienti',
      'No ingredients information is available for this recipe': 'Non sono disponibili informazioni sugli ingredienti per questa ricetta',
      'Here are the cooking instructions': 'Ecco le istruzioni di cucina',
      'Step': 'Passo',
      'Enjoy your meal': 'Buon appetito',
      'No instructions are available for this recipe': 'Non sono disponibili istruzioni per questa ricetta',
      'Nutrition information per serving': 'Informazioni nutrizionali per porzione',
      'contains': 'contiene',
      'content is': 'il contenuto è',
      'No nutrition information is available for this recipe': 'Non sono disponibili informazioni nutrizionali per questa ricetta',
      'to': 'a',
      'minutes': 'minuti',
      'Servings': 'Porzioni',
      'Author': 'Autore',
      'Category': 'Categoria',
      'Prep Time': 'Tempo di preparazione'
    },
    pt: { // Portuguese
      'Here are the recipe details': 'Aqui estão os detalhes da receita',
      'Created by': 'Criado por',
      'Published on': 'Publicado em',
      'Preparation time is': 'O tempo de preparação é',
      'Here are the ingredients you will need': 'Aqui estão os ingredientes que você precisará',
      'That\'s all the ingredients': 'Esses são todos os ingredientes',
      'No ingredients information is available for this recipe': 'Não há informações sobre ingredientes disponíveis para esta receita',
      'Here are the cooking instructions': 'Aqui estão as instruções de cozimento',
      'Step': 'Passo',
      'Enjoy your meal': 'Bom apetite',
      'No instructions are available for this recipe': 'Não há instruções disponíveis para esta receita',
      'Nutrition information per serving': 'Informação nutricional por porção',
      'contains': 'contém',
      'content is': 'o conteúdo é',
      'No nutrition information is available for this recipe': 'Não há informações nutricionais disponíveis para esta receita',
      'to': 'a',
      'minutes': 'minutos',
      'Servings': 'Porções',
      'Author': 'Autor',
      'Category': 'Categoria',
      'Prep Time': 'Tempo de preparo'
    }
  };

  // Helper function to translate text
  const translate = (text, lang = browserLang) => {
    if (lang === 'en' || !translations[lang]) return text;
    return translations[lang][text] || text;
  };

  // Check Web Speech API support
  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      console.error('Web Speech API is not supported in this browser!');
    } else {
      console.log('Web Speech API is supported!');
      console.log('Speech synthesis object:', window.speechSynthesis);
    }
  }, []);

  // Debug browserLang prop
  useEffect(() => {
    console.log('RecipeDrawer: browserLang prop changed to:', browserLang);
  }, [browserLang]);

  // Load voices when available
  useEffect(() => {
    const loadVoices = () => {
      const voices = synth.getVoices();
      console.log('LoadVoices called, found', voices.length, 'voices');
      if (voices.length > 0) {
        setVoicesLoaded(true);
        console.log('Available TTS voices:');
        voices.forEach(voice => {
          console.log(`- ${voice.name} (${voice.lang})${voice.localService ? ' [Local]' : ' [Remote]'}`);
        });
        
        // Log Spanish voices specifically if browser is Spanish
        if (browserLang === 'es') {
          console.log('\nSpanish voices available:');
          const spanishVoices = voices.filter(v => v.lang.startsWith('es'));
          spanishVoices.forEach(voice => {
            console.log(`- ${voice.name} (${voice.lang})`);
          });
        }
        
        // Log French voices specifically if browser is French
        if (browserLang === 'fr') {
          console.log('\nFrench voices available:');
          const frenchVoices = voices.filter(v => v.lang.startsWith('fr'));
          frenchVoices.forEach(voice => {
            console.log(`- ${voice.name} (${voice.lang})`);
          });
        }
      }
    };

    // Load voices immediately if available
    loadVoices();

    // Also listen for voices changed event
    if (synth.onvoiceschanged !== undefined) {
      synth.onvoiceschanged = loadVoices;
    }
    
    // Try loading voices after a delay as a fallback
    const timeoutId = setTimeout(loadVoices, 100);

    return () => {
      if (synth.onvoiceschanged !== undefined) {
        synth.onvoiceschanged = null;
      }
      clearTimeout(timeoutId);
    };
  }, [browserLang]);

  // Clean up speech when drawer closes or content changes
  useEffect(() => {
    return () => {
      if (synth.speaking) {
        synth.cancel();
        setIsSpeaking(false);
      }
    };
  }, [drawerContent, open]);

  // Function to get text content for TTS
  const getTextForTTS = () => {
    console.log('getTextForTTS called with drawerContent:', drawerContent);
    console.log('Recipe data:', recipe);
    console.log('browserLang in getTextForTTS:', browserLang);
    
    if (!recipe) {
      console.error('No recipe data available for TTS');
      return '';
    }
    
    let text = '';
    
    switch (drawerContent) {
      case 'info':
        text = `${recipe.name}... ... `;  // Recipe name stays in original language
        if (recipe.additionalInfo) {
          const translatedPhrase = translate('Here are the recipe details');
          console.log('Translated phrase:', translatedPhrase);
          text += translatedPhrase + '... ... ';
          Object.entries(recipe.additionalInfo).forEach(([key, value]) => {
            // Translate keys and format values
            if (key === 'Author') {
              text += `${translate('Created by')} ${value}... ... `;
            } else if (key === 'Published') {
              text += `${translate('Published on')} ${value}... ... `;
            } else if (key === 'Prep Time') {
              // Handle prep time translation
              const translatedValue = value.replace('minutes', translate('minutes'));
              text += `${translate('Preparation time is')} ${translatedValue}... ... `;
            } else if (key === 'Servings' || key === 'Category') {
              text += `${translate(key)}: ${value}... ... `;
            } else {
              text += `${key}: ${value}... ... `;
            }
            text += '   ';  // Extra pause between items
          });
        }
        break;
        
      case 'ingredients':
        text = translate('Here are the ingredients you will need') + '... ... ';
        if (recipe.ingredients && recipe.ingredients.length > 0) {
          recipe.ingredients.forEach((ingredient, index) => {
            // Replace number ranges for better TTS pronunciation
            let pronounceableIngredient = ingredient
              .replace(/(\d+)\s*-\s*(\d+)/g, `$1 ${translate('to')} $2`)  // Use translated "to"
              .replace(/(\d+)\s*–\s*(\d+)/g, `$1 ${translate('to')} $2`)
              .replace(/(\d+)\s*—\s*(\d+)/g, `$1 ${translate('to')} $2`);
            
            text += `${pronounceableIngredient}... `;
            text += '   '; // Significant pause after each ingredient
            // Add an even longer breathing pause every 3 ingredients
            if ((index + 1) % 3 === 0 && index < recipe.ingredients.length - 1) {
              text += '     ';  // Very long pause for breath
            }
          });
          text += '     ' + translate('That\'s all the ingredients');
        } else {
          text = translate('No ingredients information is available for this recipe');
        }
        break;
        
      case 'instructions':
        text = translate('Here are the cooking instructions') + '... ... ';
        if (recipe.instructions && recipe.instructions.length > 0) {
          recipe.instructions.forEach((instruction, index) => {
            text += `${translate('Step')} ${index + 1}... ... ${instruction}... `;
            text += '     ';  // Very long pause between steps
          });
          text += '     ' + translate('Enjoy your meal');
        } else {
          text = translate('No instructions are available for this recipe');
        }
        break;
        
      case 'nutrition':
        text = translate('Nutrition information per serving') + '... ... ';
        if (recipe.nutrition && Object.keys(recipe.nutrition).length > 0) {
          Object.entries(recipe.nutrition).forEach(([nutrient, value]) => {
            // Make nutrition info more natural
            if (nutrient.toLowerCase().includes('fat')) {
              text += `${nutrient} ${translate('content is')} ${value}... ... `;
            } else if (nutrient.toLowerCase().includes('protein')) {
              text += `${translate('contains')} ${value} ${nutrient}... ... `;
            } else {
              text += `${nutrient}: ${value}... ... `;
            }
            text += '  '; // Pause between nutrients
          });
        } else {
          text = translate('No nutrition information is available for this recipe');
        }
        break;
    }
    
    return text;
  };

  // Handle TTS toggle
  const handleTTSToggle = () => {
    console.log('=== TTS Toggle clicked ===');
    console.log('Is currently speaking:', isSpeaking);
    console.log('Speech synthesis available:', 'speechSynthesis' in window);
    console.log('Voices loaded:', voicesLoaded);
    console.log('Current browserLang:', browserLang);
    
    if (isSpeaking) {
      // Stop speaking
      console.log('Stopping speech...');
      synth.cancel();
      setIsSpeaking(false);
      setCurrentUtterance(null);
    } else {
      // Start speaking
      const text = getTextForTTS();
      console.log('Text to speak:', text);
      
      if (text.trim()) {
        console.log('=== TTS DEBUG ===');
        console.log('Browser language:', browserLang);
        console.log('Text to speak (first 100 chars):', text.substring(0, 100));
        
        const utterance = new SpeechSynthesisUtterance(text);
        
        // Configure speech settings for even more natural, slower speech
        utterance.rate = 0.65; // Much slower for very natural effect
        utterance.pitch = 0.92; // Slightly lower pitch for warmth
        utterance.volume = 0.8; // Even softer volume
        
        // Initialize utterance language based on browserLang
        let finalUtteranceLang = browserLang;
        if (browserLang !== 'en') {
          const langMap = {
            'es': 'es-ES',
            'fr': 'fr-FR',
            'de': 'de-DE',
            'it': 'it-IT',
            'pt': 'pt-BR'
          };
          finalUtteranceLang = langMap[browserLang] || browserLang;
        }
        utterance.lang = finalUtteranceLang; // Set initial lang
        console.log('Initial utterance language set to:', utterance.lang);

        // Try to use a voice that matches the browser language
        const voices = synth.getVoices();
        console.log('Total available voices:', voices.length);
        
        // If no voices loaded, try to load them
        if (voices.length === 0) {
          console.warn('No voices loaded yet. Trying to speak anyway...');
          console.warn('This might cause TTS to fail silently. Try clicking the button again in a moment.');
        }
        
        // Find voices for the current language
        const languageVoices = voices.filter(voice => 
          voice.lang.startsWith(browserLang) || 
          (browserLang === 'en' && voice.lang.startsWith('en'))
        );
        
        console.log(`Found ${languageVoices.length} voices for language: ${browserLang}`);
        if (languageVoices.length > 0) {
          console.log('Available voices for', browserLang + ':');
          languageVoices.forEach(v => console.log(`- ${v.name} (${v.lang})`));
        }
        
        let preferredVoice = null;
        
        // Language-specific female voice preferences
        if (browserLang === 'es') {
          // Spanish: Prefer female Spanish voices
          const spanishFemaleNames = [
            'Mónica', 'Paulina', 'Laura', 'Helena', 'Isabel', 'Marta',
            'Carmen', 'Ana', 'Lucia', 'Sofia', 'Maria', 'Conchita',
            'Google español de Estados Unidos', 'Google español',
            'Microsoft Helena Desktop', 'Microsoft Laura Desktop',
            'Microsoft Sabina Desktop', 'es-ES', 'es-MX', 'Female'
          ];
          
          console.log('Looking for Spanish female voice...');
          for (const voiceName of spanishFemaleNames) {
            preferredVoice = languageVoices.find(voice => 
              voice.name.toLowerCase().includes(voiceName.toLowerCase())
            );
            if (preferredVoice) {
              console.log(`Selected Spanish female voice: ${preferredVoice.name}`);
              break;
            }
          }
        } else if (browserLang === 'fr') {
          // French: Prefer female French voices
          const frenchFemaleNames = [
            'Amélie', 'Audrey', 'Aurélie', 'Julie', 'Marie',
            'Google français', 'Microsoft Julie', 'Female', 'female'
          ];
          
          for (const voiceName of frenchFemaleNames) {
            preferredVoice = languageVoices.find(voice => 
              voice.name.toLowerCase().includes(voiceName.toLowerCase())
            );
            if (preferredVoice) break;
          }
        } else if (browserLang === 'de') {
          // German: Prefer female German voices
          const germanFemaleNames = [
            'Anna', 'Hedda', 'Katja', 'Marlene', 'Vicki',
            'Google Deutsch', 'Microsoft Hedda', 'Female', 'female'
          ];
          
          for (const voiceName of germanFemaleNames) {
            preferredVoice = languageVoices.find(voice => 
              voice.name.toLowerCase().includes(voiceName.toLowerCase())
            );
            if (preferredVoice) break;
          }
        } else if (browserLang === 'it') {
          // Italian: Prefer female Italian voices
          const italianFemaleNames = [
            'Alice', 'Elsa', 'Carla', 'Bianca',
            'Google italiano', 'Microsoft Elsa', 'Female', 'female'
          ];
          
          for (const voiceName of italianFemaleNames) {
            preferredVoice = languageVoices.find(voice => 
              voice.name.toLowerCase().includes(voiceName.toLowerCase())
            );
            if (preferredVoice) break;
          }
        } else if (browserLang === 'pt') {
          // Portuguese: Prefer female Portuguese voices
          const portugueseFemaleNames = [
            'Francisca', 'Fernanda', 'Catarina', 'Raquel',
            'Google português', 'Microsoft Maria', 'Female', 'female'
          ];
          
          for (const voiceName of portugueseFemaleNames) {
            preferredVoice = languageVoices.find(voice => 
              voice.name.toLowerCase().includes(voiceName.toLowerCase())
            );
            if (preferredVoice) break;
          }
        } else {
          // For other languages including English, use generic female characteristics
          const preferredCharacteristics = ['Female', 'female', 'Woman', 'woman', 'Google', 'Microsoft'];
          
          for (const characteristic of preferredCharacteristics) {
            preferredVoice = languageVoices.find(voice => 
              voice.name.includes(characteristic)
            );
            if (preferredVoice) break;
          }
        }
        
        // If no preferred voice found, use any voice for that language
        if (!preferredVoice && languageVoices.length > 0) {
          // Prefer local voices over remote ones
          preferredVoice = languageVoices.find(v => v.localService) || languageVoices[0];
        }
        
        // Fallback to English if no voice found for the language
        if (!preferredVoice && browserLang !== 'en') {
          console.log('No voice found for', browserLang, ', falling back to English');
          const englishVoices = voices.filter(v => v.lang.startsWith('en'));
          
          // Try to find a soothing English voice
          const soothingVoiceNames = [
            'Samantha', 'Karen', 'Tessa', 'Fiona', 'Victoria',
            'Google US English Female', 'Google UK English Female',
            'Microsoft Zira', 'Microsoft Hazel', 'Female'
          ];
          
          for (const voiceName of soothingVoiceNames) {
            preferredVoice = englishVoices.find(v => v.name.includes(voiceName));
            if (preferredVoice) break;
          }
          
          if (!preferredVoice && englishVoices.length > 0) {
            preferredVoice = englishVoices[0];
          }
        }
        
        if (preferredVoice) {
          utterance.voice = preferredVoice;
          // IMPORTANT: Override utterance lang with the selected voice's specific lang
          if (utterance.lang !== preferredVoice.lang) {
             console.log(`Updating utterance language from ${utterance.lang} to ${preferredVoice.lang} to match selected voice.`);
             utterance.lang = preferredVoice.lang;
          }
          console.log('Selected TTS voice:', preferredVoice.name, '(', preferredVoice.lang, ')');
        } else {
          console.log('Using default system voice (or first available for initial utterance.lang).');
        }
        
        utterance.onstart = () => {
          console.log('Speech started!');
          setIsSpeaking(true);
        };
        
        utterance.onend = () => {
          console.log('Speech ended!');
          setIsSpeaking(false);
          setCurrentUtterance(null);
        };
        
        utterance.onerror = (event) => {
          console.error('Speech synthesis error:', event);
          console.error('Error type:', event.error);
          setIsSpeaking(false);
          setCurrentUtterance(null);
        };
        
        setCurrentUtterance(utterance);
        console.log('Speaking with utterance:', utterance);
        console.log('Utterance text:', utterance.text.substring(0, 100));
        console.log('Utterance lang:', utterance.lang);
        console.log('Utterance voice:', utterance.voice);
        
        try {
          synth.speak(utterance);
          console.log('Called synth.speak()');
          console.log('Is synth speaking?', synth.speaking);
          console.log('Is synth paused?', synth.paused);
          console.log('Is synth pending?', synth.pending);
        } catch (error) {
          console.error('Error calling synth.speak():', error);
        }
      }
    }
  };

  if (!recipe) return null;

  // Enhanced close handler that also stops TTS
  const handleClose = () => {
    if (synth.speaking) {
      synth.cancel();
      setIsSpeaking(false);
    }
    onClose();
  };

  return (
    <Drawer anchor="right" open={open} onClose={handleClose}>
      <Box sx={{ width: 350, p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">Recipe Details</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Test TTS" arrow>
              <IconButton 
                onClick={() => {
                  console.log('Test TTS clicked');
                  console.log('Browser support:', 'speechSynthesis' in window);
                  console.log('Synth object:', window.speechSynthesis);
                  
                  const testUtterance = new SpeechSynthesisUtterance('Hello, this is a test. Can you hear me?');
                  testUtterance.lang = 'en-US';
                  testUtterance.rate = 0.9;
                  testUtterance.pitch = 1;
                  testUtterance.volume = 1;
                  
                  testUtterance.onstart = () => {
                    console.log('Test started');
                    console.log('Speaking:', window.speechSynthesis.speaking);
                    console.log('Paused:', window.speechSynthesis.paused);
                    console.log('Pending:', window.speechSynthesis.pending);
                  };
                  testUtterance.onend = () => console.log('Test ended');
                  testUtterance.onerror = (e) => {
                    console.error('Test error:', e);
                    console.error('Error type:', e.error);
                    console.error('Error utterance:', e.utterance);
                  };
                  
                  try {
                    window.speechSynthesis.cancel(); // Cancel any existing speech
                    window.speechSynthesis.speak(testUtterance);
                    console.log('Test utterance queued');
                  } catch (error) {
                    console.error('Error speaking test:', error);
                  }
                }}
                size="small"
              >
                🔊
              </IconButton>
            </Tooltip>
            <Tooltip title={isSpeaking ? "Stop reading" : "Read content aloud"} arrow>
              <IconButton 
                onClick={handleTTSToggle}
                color="primary"
                sx={{
                  animation: isSpeaking ? 'pulse 1.5s ease-in-out infinite' : 'none',
                  '@keyframes pulse': {
                    '0%': {
                      transform: 'scale(1)',
                      opacity: 1,
                    },
                    '50%': {
                      transform: 'scale(1.1)',
                      opacity: 0.8,
                    },
                    '100%': {
                      transform: 'scale(1)',
                      opacity: 1,
                    },
                  },
                }}
              >
                {isSpeaking ? <StopIcon /> : <VolumeUpIcon />}
              </IconButton>
            </Tooltip>
            <IconButton onClick={handleClose}>
              <CloseIcon />
            </IconButton>
          </Box>
        </Box>

        <Box sx={{ display: 'flex', gap: 1, mb: 3 }}>
          <Fab
            size="small"
            color={drawerContent === 'info' ? 'primary' : 'default'}
            onClick={() => setDrawerContent('info')}
          >
            <InfoIcon />
          </Fab>
          <Fab
            size="small"
            color={drawerContent === 'ingredients' ? 'primary' : 'default'}
            onClick={() => setDrawerContent('ingredients')}
          >
            <IngredientsIcon />
          </Fab>
          <Fab
            size="small"
            color={drawerContent === 'instructions' ? 'primary' : 'default'}
            onClick={() => setDrawerContent('instructions')}
          >
            <InstructionsIcon />
          </Fab>
          <Fab
            size="small"
            color={drawerContent === 'nutrition' ? 'primary' : 'default'}
            onClick={() => setDrawerContent('nutrition')}
          >
            <NutritionIcon />
          </Fab>
        </Box>

        {/* Cooking Mode Button */}
        <Box sx={{ mb: 2 }}>
          <Button
            variant="contained"
            fullWidth
            color="secondary"
            startIcon={<RestaurantMenuIcon />}
            onClick={() => {
              // TODO: Implement cooking mode
              alert('Cooking Mode coming soon! This will provide step-by-step voice guidance.');
            }}
            sx={{
              background: 'linear-gradient(45deg, #FFA000 30%, #FFB300 90%)',
              boxShadow: '0 3px 5px 2px rgba(255, 179, 0, .3)',
              color: 'white',
              fontWeight: 'bold',
            }}
          >
            Start Cooking Mode 🍳
          </Button>
        </Box>

        {/* Content based on selection */}
        {drawerContent === 'info' && (
          <Box>
            <Typography variant="h6" gutterBottom>
              {recipe.name}
            </Typography>
            {recipe.additionalInfo && (
              <List dense>
                {Object.entries(recipe.additionalInfo).map(([key, value]) => (
                  <ListItem key={key} disableGutters>
                    <ListItemText
                      primary={key}
                      secondary={value}
                      primaryTypographyProps={{ fontWeight: 'medium' }}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Box>
        )}

        {drawerContent === 'ingredients' && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Ingredients
            </Typography>
            {recipe.ingredients && recipe.ingredients.length > 0 ? (
              <List>
                {recipe.ingredients.map((ingredient, index) => (
                  <ListItem key={index} disableGutters>
                    <Typography variant="body2">• {ingredient}</Typography>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No ingredients available
              </Typography>
            )}
          </Box>
        )}

        {drawerContent === 'instructions' && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Instructions
            </Typography>
            {recipe.instructions && recipe.instructions.length > 0 ? (
              <List>
                {recipe.instructions.map((instruction, index) => (
                  <ListItem key={index} disableGutters>
                    <Typography variant="body2">
                      {index + 1}. {instruction}
                    </Typography>
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No instructions available
              </Typography>
            )}
          </Box>
        )}

        {drawerContent === 'nutrition' && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Nutrition (per serving)
            </Typography>
            {recipe.nutrition && Object.keys(recipe.nutrition).length > 0 ? (
              <List dense>
                {Object.entries(recipe.nutrition).map(([nutrient, value]) => (
                  <ListItem key={nutrient} disableGutters>
                    <ListItemText
                      primary={nutrient}
                      secondary={value}
                      primaryTypographyProps={{ fontWeight: 'medium' }}
                    />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No nutrition information available
              </Typography>
            )}
          </Box>
        )}
      </Box>
    </Drawer>
  );
}

export default App; 