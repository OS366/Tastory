# GCP Hackathon Deployment Checklist

## Pre-Deployment Checklist

### ✅ Code Preparation

- [x] Flask backend updated to use PORT environment variable
- [x] Dockerfile created with production settings
- [x] .dockerignore configured
- [x] Cloud Build configuration (cloudbuild.yaml)
- [x] Firebase hosting configuration (firebase.json)
- [x] Deployment script created (scripts/deploy-to-gcp.sh)

### ✅ Local Testing

- [ ] Test backend locally with Docker:
  ```bash
  docker build -t tastory-api .
  docker run -p 8080:8080 -e PORT=8080 -e MONGODB_URI=$MONGODB_URI tastory-api
  ```
- [ ] Test frontend build:
  ```bash
  cd frontend
  npm run build
  ```

## Deployment Steps

### 1. Google Cloud Setup

- [ ] Login to Google Cloud:
  ```bash
  gcloud auth login
  ```
- [ ] Create project (if not exists):
  ```bash
  gcloud projects create tastory-hackathon
  ```
- [ ] Set billing account (required for Cloud Run)
- [ ] Enable APIs:
  ```bash
  gcloud services enable run.googleapis.com firebase.googleapis.com
  ```

### 2. Deploy Backend

- [ ] Run deployment script:
  ```bash
  ./scripts/deploy-to-gcp.sh
  ```
- [ ] Verify backend is running:
  ```bash
  curl https://tastory-api-xxxxx-uc.a.run.app
  ```

### 3. Deploy Frontend

- [ ] Frontend will be deployed automatically by the script
- [ ] Verify at: https://tastory-hackathon.web.app

## Demo Preparation

### Performance Demos

- [ ] Prepare load testing script
- [ ] Document response times (<2s for 230K recipes)
- [ ] Show auto-scaling metrics

### Feature Demos

- [ ] Search functionality with instant results
- [ ] Multilingual TTS (6 languages)
- [ ] Recent searches with persistence
- [ ] Mobile responsiveness

### Technical Demos

- [ ] Show GCP Console metrics
- [ ] Demonstrate CI/CD pipeline
- [ ] Show cost analysis ($0 during development)

## Hackathon Presentation Points

### 1. Innovation

- "The Food Search Engine" - Better than Google/ChatGPT for recipes
- 230,000+ recipes with vector search
- Multilingual voice support

### 2. Technical Excellence

- Cloud Run for serverless scaling
- Firebase for global CDN
- MongoDB Atlas with vector embeddings
- GitHub Actions CI/CD

### 3. Business Value

- $0 cost during development (free tier)
- Scales to millions of users
- <2 second response time
- Global availability

### 4. GCP Integration

- Native GCP services used
- Ready for additional Google AI services
- Monitoring and logging integrated

## Post-Deployment Monitoring

### Commands

```bash
# View logs
gcloud run logs tail --service tastory-api

# Check metrics
gcloud run services describe tastory-api

# Update deployment
gcloud run deploy tastory-api --source .
```

### Dashboards

- Cloud Run: https://console.cloud.google.com/run
- Firebase: https://console.firebase.google.com
- Monitoring: https://console.cloud.google.com/monitoring

## Troubleshooting

### Common Issues

1. **502 Bad Gateway**

   - Check logs: `gcloud run logs read --service tastory-api`
   - Verify MongoDB connection
   - Check memory limits

2. **Slow Performance**

   - Increase Cloud Run instances
   - Check MongoDB indexes
   - Review vector search settings

3. **Frontend Not Loading**
   - Check Firebase deployment
   - Verify API URL in environment
   - Check CORS settings

## Cleanup (After Hackathon)

```bash
# Delete project (removes all resources)
gcloud projects delete tastory-hackathon

# Or just stop services
gcloud run services delete tastory-api
firebase hosting:disable
```

## Support Resources

- GCP Support: https://cloud.google.com/support
- Stack Overflow: Tag with `google-cloud-run`
- Firebase Support: https://firebase.google.com/support

## Final Checks

- [ ] All features working
- [ ] Performance metrics documented
- [ ] Cost analysis prepared
- [ ] Demo script rehearsed
- [ ] Backup deployment ready
- [ ] Team briefed on architecture
