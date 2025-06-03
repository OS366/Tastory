# Tastory Log Viewing Guide

This guide explains how to view logs for both the backend (Cloud Run) and frontend (Firebase) deployments.

## Backend Logs (Cloud Run)

### Using gcloud CLI

```bash
# View real-time logs
gcloud run logs read --service tastory-api --tail 50 -f

# View logs from the last hour
gcloud run logs read --service tastory-api --limit 100 --since 1h

# View logs with specific severity
gcloud run logs read --service tastory-api --filter "severity>=ERROR"

# View logs for a specific time range
gcloud run logs read --service tastory-api --since 2024-06-02T10:00:00Z --until 2024-06-02T12:00:00Z

# Export logs to a file
gcloud run logs read --service tastory-api --limit 1000 > backend-logs.txt
```

### Using Google Cloud Console

1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click on the `tastory-api` service
3. Navigate to the "Logs" tab
4. Use filters to search for specific logs:
   - Severity levels (Error, Warning, Info, Debug)
   - Time range
   - Text search
   - HTTP status codes

### Useful Log Queries

```bash
# View startup logs
gcloud run logs read --service tastory-api --filter "Starting Flask app"

# View MongoDB connection logs
gcloud run logs read --service tastory-api --filter "MongoDB"

# View HTTP request logs
gcloud run logs read --service tastory-api --filter "GET" --limit 20

# View errors only
gcloud run logs read --service tastory-api --filter "severity=ERROR"

# View logs from specific container
gcloud run logs read --service tastory-api --filter "resource.labels.revision_name=~tastory-api"
```

## Frontend Logs (Firebase Hosting)

### Firebase CLI

```bash
# Install Firebase CLI if not already installed
npm install -g firebase-tools

# View hosting activity
firebase hosting:channel:list

# View deployment history
firebase hosting:sites:list
```

### Firebase Console

1. Go to [Firebase Console](https://console.firebase.google.com/project/tastory-hackathon)
2. Navigate to "Hosting" from the left menu
3. View deployment history and rollback options
4. Check "Usage" tab for traffic analytics

## Application-Level Logging

### Backend Python Logs

The backend uses Python's logging module. View different log levels:

```bash
# View all Flask app logs
gcloud run logs read --service tastory-api --filter "flask.app"

# View search query logs
gcloud run logs read --service tastory-api --filter "Search query"

# View embedding generation logs
gcloud run logs read --service tastory-api --filter "embedding"
```

### Frontend JavaScript Logs

Frontend logs are visible in the browser console. To capture them:

1. Open Chrome DevTools (F12)
2. Go to Console tab
3. Look for logs with these patterns:
   - `Browser language detected:`
   - `Error fetching suggestions:`
   - `Search error:`
   - `TTS` (Text-to-Speech logs)

## Monitoring and Alerts

### Set up log-based alerts

```bash
# Create an alert for high error rate
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="High Error Rate Alert" \
  --condition-display-name="Error rate > 5%" \
  --condition-filter='resource.type="cloud_run_revision" AND severity="ERROR"'
```

### View metrics

```bash
# View Cloud Run metrics
gcloud run services describe tastory-api --region us-central1 --format "value(status.traffic)"

# View current resource usage
gcloud run services describe tastory-api --region us-central1 --format "value(spec.template.spec.containers[0].resources)"
```

## Debugging Tips

### 1. Backend Connection Issues

```bash
# Check if MongoDB connection is working
gcloud run logs read --service tastory-api --filter "Connected to MongoDB" --limit 10

# Check for timeout errors
gcloud run logs read --service tastory-api --filter "timeout" --limit 10
```

### 2. Performance Issues

```bash
# View slow requests (>2s)
gcloud run logs read --service tastory-api --filter "httpRequest.latency>2s"

# View memory usage warnings
gcloud run logs read --service tastory-api --filter "memory"
```

### 3. Search Issues

```bash
# View search queries and results
gcloud run logs read --service tastory-api --filter "/chat" --limit 20

# Check embedding generation
gcloud run logs read --service tastory-api --filter "generate_query_embedding"
```

## Export and Analysis

### Export logs for analysis

```bash
# Export to BigQuery
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tastory-api" \
  --format json > logs.json

# Export last 24 hours of logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=tastory-api AND timestamp>=\"$(date -u -d '24 hours ago' '+%Y-%m-%dT%H:%M:%S.%3NZ')\"" \
  --format json > daily-logs.json
```

### Create a log sink for long-term storage

```bash
gcloud logging sinks create tastory-logs-sink \
  storage.googleapis.com/YOUR_BUCKET_NAME \
  --log-filter='resource.type="cloud_run_revision" AND resource.labels.service_name="tastory-api"'
```

## Quick Commands Reference

```bash
# Most recent errors
gcloud run logs read --service tastory-api --filter "severity=ERROR" --limit 10

# Live tail of logs
gcloud run logs tail --service tastory-api

# Logs from specific deployment
gcloud run logs read --service tastory-api --filter "labels.deployment-id=YOUR_DEPLOYMENT_ID"

# HTTP 5xx errors
gcloud run logs read --service tastory-api --filter "httpRequest.status>=500"

# Slow requests
gcloud run logs read --service tastory-api --filter "httpRequest.latency>1s"
```

## Troubleshooting Common Issues

### "Permission denied" errors

- Ensure you're authenticated: `gcloud auth login`
- Check project: `gcloud config set project tastory-hackathon`

### No logs appearing

- Wait 1-2 minutes for logs to propagate
- Check service name: `gcloud run services list`
- Verify region: `--region us-central1`

### Too many logs

- Use `--limit` flag to restrict results
- Add time filters with `--since` and `--until`
- Use specific filters like severity or text search
