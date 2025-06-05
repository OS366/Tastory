#!/bin/bash

# Manual backend deployment to fix environment variable conflicts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Manual Backend Deployment${NC}"
echo "============================"

PROJECT_ID="tastory-hackathon"
SERVICE_NAME="tastory-api"
REGION="us-central1"

# Get MongoDB URI from .env file
if [ -f .env ]; then
    export $(grep MONGODB_URI .env | xargs)
    echo -e "${GREEN}✅ Found MongoDB URI in .env${NC}"
else
    echo -e "${RED}❌ No .env file found${NC}"
    echo "Please create .env with MONGODB_URI"
    exit 1
fi

echo -e "\n${YELLOW}Building Docker image...${NC}"
docker build -t gcr.io/$PROJECT_ID/$SERVICE_NAME:manual .

echo -e "\n${YELLOW}Pushing to GCR...${NC}"
docker push gcr.io/$PROJECT_ID/$SERVICE_NAME:manual

echo -e "\n${YELLOW}Deploying to Cloud Run (without env vars)...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image gcr.io/$PROJECT_ID/$SERVICE_NAME:manual \
    --region $REGION \
    --platform managed \
    --allow-unauthenticated \
    --memory 2Gi \
    --min-instances 1 \
    --max-instances 100

echo -e "\n${YELLOW}Setting environment variables...${NC}"
gcloud run services update $SERVICE_NAME \
    --region $REGION \
    --set-env-vars "MONGODB_URI=$MONGODB_URI"

echo -e "\n${GREEN}✅ Deployment complete!${NC}"
echo "Testing health endpoint..."
sleep 10
curl https://tastory-api-vbx2teipca-uc.a.run.app/health || echo "Health check failed - service may still be starting" 