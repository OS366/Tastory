#!/bin/bash

# Check Tastory deployment status
# Usage: ./scripts/check-deployment-status.sh

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="tastory-hackathon"
REGION="us-central1"
SERVICE_NAME="tastory-api"

echo -e "${GREEN}🔍 Checking Tastory deployment status...${NC}"

# Check if service exists
echo -e "\n${YELLOW}Checking Cloud Run service...${NC}"
if gcloud run services describe $SERVICE_NAME --region $REGION --project $PROJECT_ID &> /dev/null; then
    SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
    echo -e "${GREEN}✅ Backend is deployed!${NC}"
    echo -e "URL: ${GREEN}$SERVICE_URL${NC}"
    
    # Test the service
    echo -e "\n${YELLOW}Testing the service...${NC}"
    if curl -s "$SERVICE_URL" | grep -q "Tastory API"; then
        echo -e "${GREEN}✅ Service is responding correctly!${NC}"
    else
        echo -e "${RED}⚠️  Service is deployed but may not be responding correctly${NC}"
    fi
else
    echo -e "${RED}❌ Service not found or not yet deployed${NC}"
    
    # Check latest build
    echo -e "\n${YELLOW}Checking latest build status...${NC}"
    BUILD_ID=$(gcloud builds list --limit=1 --format="value(id)" --project=$PROJECT_ID)
    if [ ! -z "$BUILD_ID" ]; then
        echo "Latest build ID: $BUILD_ID"
        echo -e "\n${YELLOW}To view build logs, run:${NC}"
        echo "gcloud builds log $BUILD_ID"
    fi
fi

# Check frontend configuration
echo -e "\n${YELLOW}Checking frontend configuration...${NC}"
if [ -f "frontend/.env.production.local" ]; then
    echo -e "${GREEN}✅ Frontend configuration exists${NC}"
    cat frontend/.env.production.local
else
    echo -e "${YELLOW}⚠️  Frontend configuration not yet created${NC}"
fi

# Next steps
echo -e "\n${YELLOW}Next steps:${NC}"
if [ ! -z "$SERVICE_URL" ]; then
    echo "1. Build frontend: cd frontend && npm run build"
    echo "2. Deploy frontend: firebase deploy --only hosting --project $PROJECT_ID"
else
    echo "1. Wait for backend deployment to complete"
    echo "2. Run this script again to check status"
fi 