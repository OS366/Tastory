# GCP Deployment Guide for Tastory

## Quick Start

Deploy Tastory to Google Cloud Platform with a single command:

```bash
./scripts/deploy-to-gcp.sh
```

## Prerequisites

1. **Google Cloud Account**

   - Sign up at https://cloud.google.com
   - Hackathon participants often get free credits

2. **Google Cloud SDK**

   - Already installed at: `/Users/sid/Downloads/google-cloud-sdk/bin/gcloud`
   - If needed: https://cloud.google.com/sdk/docs/install

3. **MongoDB Atlas**

   - Existing database with 230K+ recipes
   - Connection string in `.env` file

4. **Node.js & npm**
   - For building React frontend
   - Already installed

## Manual Deployment Steps

### 1. Authenticate with Google Cloud

```bash
gcloud auth login
```

### 2. Create GCP Project

```bash
# Create project
gcloud projects create tastory-hackathon --name="Tastory Recipe Search"

# Set as active project
gcloud config set project tastory-hackathon
```

### 3. Enable Required APIs

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable firebase.googleapis.com
```

### 4. Deploy Backend to Cloud Run

```bash
# Deploy directly from source
gcloud run deploy tastory-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URI=$MONGODB_URI,DB_NAME=tastory,RECIPES_COLLECTION=recipes
```

### 5. Deploy Frontend to Firebase

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login to Firebase
firebase login

# Build frontend
cd frontend
npm install
npm run build

# Deploy
firebase deploy --only hosting
```

## Architecture on GCP

```
┌─────────────────────────────────────────────────────────┐
│                    Google Cloud Platform                 │
├─────────────────────────┬───────────────────────────────┤
│                         │                               │
│   Firebase Hosting      │        Cloud Run             │
│   ┌───────────────┐     │     ┌─────────────────┐      │
│   │               │     │     │                 │      │
│   │  React App    │────────▶  │   Flask API     │      │
│   │  (Frontend)   │ HTTPS│     │   (Backend)     │      │
│   │               │     │     │                 │      │
│   └───────────────┘     │     └────────┬────────┘      │
│                         │              │               │
│   Features:             │              │               │
│   • Global CDN         │              ▼               │
│   • SSL/HTTPS          │     ┌─────────────────┐      │
│   • Custom domain      │     │                 │      │
│                         │     │ Secret Manager  │      │
│                         │     │ (MongoDB URI)   │      │
│                         │     └─────────────────┘      │
└─────────────────────────┴───────────────────────────────┘
                                        │
                                        ▼
                              ┌─────────────────┐
                              │                 │
                              │  MongoDB Atlas  │
                              │  (External)     │
                              │  230K+ Recipes  │
                              └─────────────────┘
```

## Cost Analysis

### Free Tier Benefits

- **Cloud Run**: 2 million requests/month free
- **Firebase Hosting**: 10GB storage, 360MB/day transfer
- **Cloud Build**: 120 build-minutes/day
- **Secret Manager**: 6 active secrets free

### Estimated Costs for Hackathon

- **During hackathon**: $0 (free tier)
- **Demo day traffic**: $0-5
- **Monthly (low traffic)**: $10-20
- **Monthly (high traffic)**: $50-100

## Performance Features

### Auto-scaling

- Cloud Run automatically scales from 1 to 100 instances
- Handles traffic spikes during demos
- Scales to zero when not in use (cost savings)

### Global Performance

- Firebase CDN serves frontend from edge locations
- Sub-100ms latency worldwide
- Automatic HTTPS with managed certificates

## Security Features

1. **Secrets Management**

   - MongoDB URI stored in Secret Manager
   - No hardcoded credentials

2. **Network Security**

   - HTTPS everywhere
   - DDoS protection built-in

3. **Access Control**
   - IAM roles for team members
   - Service accounts for applications

## Monitoring & Debugging

### View Logs

```bash
# Recent logs
gcloud run logs read --service tastory-api

# Stream live logs
gcloud run logs tail --service tastory-api
```

### Monitoring Dashboard

- Visit: https://console.cloud.google.com/run
- View metrics: requests, latency, errors
- Set up alerts for issues

## Demo Features for Judges

### 1. Load Testing Demo

```bash
# Install hey (HTTP load generator)
brew install hey

# Test auto-scaling
hey -n 10000 -c 100 https://tastory-api-xxxxx-uc.a.run.app/api/search?q=pasta
```

### 2. Global Performance Demo

- Access from different regions
- Show <100ms response times
- Demonstrate CDN cache hits

### 3. Cost Efficiency Demo

- Show $0 cost during development
- Demonstrate scale-to-zero
- Compare to traditional hosting

## Advanced GCP Features (Bonus Points)

### 1. Add Google Cloud Vision API

```python
# Analyze food images
from google.cloud import vision
client = vision.ImageAnnotatorClient()
```

### 2. Add Cloud Translation API

```python
# Translate recipes to multiple languages
from google.cloud import translate_v2
translate_client = translate_v2.Client()
```

### 3. Add Cloud Speech-to-Text

```javascript
// Voice search for recipes
const speech = new SpeechClient();
```

## Troubleshooting

### Common Issues

1. **Billing not enabled**

   - Link a billing account at https://console.cloud.google.com/billing

2. **API not enabled**

   - Run: `gcloud services enable [API_NAME]`

3. **Permission denied**

   - Check IAM roles: `gcloud projects get-iam-policy tastory-hackathon`

4. **Build fails**
   - Check logs: `gcloud builds list`

## Quick Commands Reference

```bash
# Deploy backend update
gcloud run deploy tastory-api --source .

# Deploy frontend update
cd frontend && npm run build && firebase deploy

# View service URL
gcloud run services describe tastory-api --format 'value(status.url)'

# Delete everything (cleanup)
gcloud projects delete tastory-hackathon
```

## Support

- GCP Documentation: https://cloud.google.com/docs
- Firebase Documentation: https://firebase.google.com/docs
- Cloud Run Samples: https://github.com/GoogleCloudPlatform/cloud-run-samples
