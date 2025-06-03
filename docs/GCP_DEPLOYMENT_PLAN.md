# GCP Deployment Plan for Tastory

## Overview

Deploy Tastory on Google Cloud Platform for the Google Hackathon, leveraging GCP services for scalability and performance.

## Architecture

### Current Setup

- **Backend**: Flask API (Python) on port 5001
- **Frontend**: React app on port 3000
- **Database**: MongoDB Atlas (external)
- **Search**: Vector embeddings with all-MiniLM-L6-v2

### GCP Architecture

```
┌─────────────────┐     ┌──────────────────┐
│                 │     │                  │
│  Firebase       │     │  Cloud Run       │
│  Hosting        │────▶│  (Backend API)   │
│  (Frontend)     │     │                  │
└─────────────────┘     └──────────────────┘
         │                       │
         │                       ▼
         │              ┌──────────────────┐
         │              │                  │
         └─────────────▶│  MongoDB Atlas   │
                        │  (External)      │
                        └──────────────────┘
```

## Deployment Strategy

### Phase 1: Backend on Cloud Run

- Containerize Flask API with Docker
- Deploy to Cloud Run for automatic scaling
- Set up Cloud Build for CI/CD
- Configure environment variables

### Phase 2: Frontend on Firebase Hosting

- Build React app for production
- Deploy to Firebase Hosting
- Set up custom domain (optional)
- Configure CDN for global performance

### Phase 3: Additional GCP Services

- **Cloud CDN**: Cache static assets
- **Cloud Armor**: DDoS protection
- **Cloud Monitoring**: Performance tracking
- **Cloud Logging**: Centralized logs

## Implementation Steps

### 1. Project Setup

```bash
# Install Google Cloud SDK
brew install google-cloud-sdk

# Authenticate
gcloud auth login

# Create new project
gcloud projects create tastory-hackathon --name="Tastory Recipe Search"

# Set project
gcloud config set project tastory-hackathon

# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable firebase.googleapis.com
```

### 2. Backend Deployment (Cloud Run)

#### Dockerfile for Backend

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run uses PORT environment variable
ENV PORT 8080
EXPOSE 8080

CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
```

#### Deploy Command

```bash
# Build and deploy
gcloud run deploy tastory-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars MONGODB_URI=$MONGODB_URI
```

### 3. Frontend Deployment (Firebase)

#### Setup Firebase

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Login
firebase login

# Initialize
firebase init hosting

# Deploy
npm run build
firebase deploy
```

### 4. Configuration Updates

#### Frontend API URL

Update `frontend/.env.production`:

```
REACT_APP_API_URL=https://tastory-api-xxxxx-uc.a.run.app
```

## Cost Optimization

### Free Tier Usage

- **Cloud Run**: 2 million requests/month free
- **Firebase Hosting**: 10GB storage, 360MB/day transfer free
- **Cloud Build**: 120 build-minutes/day free

### Estimated Monthly Cost

- Development: $0 (within free tier)
- Production (low traffic): ~$10-20
- Production (high traffic): ~$50-100

## Hackathon Advantages

### Why GCP for Google Hackathon?

1. **Native Integration**: Seamless Google services integration
2. **Scalability**: Auto-scaling with Cloud Run
3. **Performance**: Global CDN with Firebase
4. **Innovation**: Showcase GCP expertise
5. **Free Credits**: Hackathon participants often get GCP credits

### Bonus Features for Judges

- Add Google Cloud Vision API for food image analysis
- Integrate Google Cloud Translation API for multilingual recipes
- Use Google Cloud Speech-to-Text for voice search
- Implement Google Analytics for usage insights

## Security Best Practices

- Store secrets in Secret Manager
- Enable Cloud IAM for access control
- Use Cloud Armor for DDoS protection
- Implement HTTPS everywhere
- Regular security scanning with Cloud Security Scanner

## Monitoring & Logging

- Set up Cloud Monitoring dashboards
- Configure alerts for errors and performance
- Use Cloud Trace for request tracing
- Implement structured logging

## Demo Preparation

1. Prepare load testing to show auto-scaling
2. Create monitoring dashboard to show real-time metrics
3. Document architecture with diagrams
4. Prepare cost analysis showing efficiency
5. Create backup region for reliability demo
