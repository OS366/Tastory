#!/bin/bash

# Quick fix for service account issue
# Usage: ./scripts/fix-service-account.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="tastory-hackathon"
REGION="us-central1"
SERVICE_NAME="tastory-api"

echo -e "${GREEN}🔧 Fixing service account permissions...${NC}"

# Get the project number
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
echo -e "${YELLOW}Project number: $PROJECT_NUMBER${NC}"

# Grant Cloud Run access to the secret using the default compute service account
echo -e "${YELLOW}Granting secret access to Cloud Run service account...${NC}"
gcloud secrets add-iam-policy-binding mongodb-uri \
    --member="serviceAccount:${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

echo -e "${GREEN}✅ Service account permissions fixed!${NC}"

# Continue with deployment
echo -e "\n${YELLOW}Continuing with Cloud Run deployment...${NC}"

# Load MongoDB URI
if [ -z "$MONGODB_URI" ]; then
    if [ -f .env ]; then
        source .env
    fi
fi

# Deploy to Cloud Run
gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --port 8080 \
    --min-instances 1 \
    --max-instances 100 \
    --memory 512Mi \
    --cpu 1 \
    --timeout 300 \
    --set-env-vars "DB_NAME=tastory,RECIPES_COLLECTION=recipes" \
    --set-secrets "MONGODB_URI=mongodb-uri:latest"

# Get the service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Backend deployed to: $SERVICE_URL${NC}"

# Update frontend configuration
echo -e "\n${YELLOW}Updating frontend configuration...${NC}"
cat > frontend/.env.production.local << EOF
# Auto-generated by fix-service-account.sh
REACT_APP_API_URL=$SERVICE_URL
REACT_APP_ENABLE_TTS=true
REACT_APP_ENABLE_RECENT_SEARCHES=true
REACT_APP_ENABLE_STATS_DISPLAY=true
EOF

echo -e "${GREEN}✅ Frontend configuration updated${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Build frontend: cd frontend && npm run build"
echo "2. Deploy frontend: firebase deploy --only hosting --project $PROJECT_ID"
echo ""
echo "Or run the full deployment script again:"
echo "./scripts/manual-deploy-after-project.sh" 