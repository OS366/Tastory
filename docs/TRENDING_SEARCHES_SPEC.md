# Trending Searches Feature Specification

## Overview

Add a trending searches feature to Tastory that shows popular recipe searches in real-time, helping users discover what others are cooking.

## User Stories

1. As a user, I want to see what recipes are trending so I can discover popular dishes
2. As a user, I want to click on trending searches to quickly search for those recipes
3. As a user, I want trending searches to update regularly to stay current

## Feature Components

### 1. Backend API Endpoints

#### `/api/trending` - GET

- Returns top 10 trending searches
- Updates every 15 minutes
- Response format:

```json
{
  "trending": [
    {
      "query": "chocolate chip cookies",
      "count": 342,
      "trend": "up", // up, down, stable
      "percentChange": 25
    }
    // ... more items
  ],
  "lastUpdated": "2024-06-03T12:00:00Z"
}
```

#### `/api/search/log` - POST (Internal)

- Logs search queries for trending calculation
- Stores: query, timestamp, user_session_id
- Used to calculate trending searches

### 2. Frontend Components

#### TrendingSearches Component

- Location: Above search bar on homepage
- Features:
  - Horizontal scrollable list of trending terms
  - Fire emoji 🔥 for items trending up
  - Click to search functionality
  - Auto-refresh every 5 minutes

#### UI Design

```
🔥 Trending Now: [chocolate cake] [pasta recipes] [healthy breakfast] [+7 more]
```

### 3. Database Schema

#### New Collection: `search_logs`

```javascript
{
  "_id": ObjectId,
  "query": "chocolate cake",
  "timestamp": ISODate("2024-06-03T12:00:00Z"),
  "session_id": "uuid",
  "results_count": 45
}
```

#### New Collection: `trending_cache`

```javascript
{
  "_id": "current",
  "trending": [...],
  "updated_at": ISODate("2024-06-03T12:00:00Z"),
  "calculation_time_ms": 145
}
```

### 4. Implementation Plan

#### Phase 1: Backend Infrastructure

1. Create search logging endpoint
2. Implement trending calculation algorithm
3. Add caching layer for performance
4. Create trending API endpoint

#### Phase 2: Frontend Integration

1. Create TrendingSearches component
2. Integrate with existing search
3. Add animations and styling
4. Implement auto-refresh

#### Phase 3: Analytics & Optimization

1. Add analytics tracking
2. Optimize calculation algorithm
3. Add personalization options
4. A/B test display variations

## Trending Algorithm

### Calculation Method

1. **Time Windows**: Last 1 hour, 6 hours, 24 hours
2. **Scoring Formula**:
   ```
   score = (recent_count * 3 + medium_count * 2 + daily_count) / time_decay_factor
   ```
3. **Filters**:
   - Minimum 5 searches to qualify
   - Remove inappropriate content
   - Deduplicate similar queries

### Performance Considerations

- Calculate trending every 15 minutes via cron job
- Cache results in MongoDB
- Use aggregation pipeline for efficiency
- Index on timestamp for fast queries

## Success Metrics

- Click-through rate on trending searches
- Increased user engagement
- More diverse recipe discoveries
- Reduced bounce rate

## Future Enhancements

1. Personalized trending (based on user preferences)
2. Regional trending searches
3. Seasonal trending highlights
4. Social sharing of trending recipes
