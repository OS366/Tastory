#!/bin/bash

# Deploy frontend to Firebase after login
# Usage: ./scripts/deploy-frontend-final.sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ID="tastory-hackathon"

echo -e "${GREEN}🚀 Deploying Frontend to Firebase${NC}"

# Change to frontend directory
cd frontend

# Deploy using npx (works with Node 19)
echo -e "${YELLOW}Deploying to Firebase Hosting...${NC}"
npx firebase-tools@13.0.0 deploy --only hosting --project $PROJECT_ID

# Get the hosting URL
HOSTING_URL="https://$PROJECT_ID.web.app"

echo -e "\n${GREEN}🎉 DEPLOYMENT COMPLETE!${NC}"
echo -e "\n${YELLOW}Your Tastory app is now live:${NC}"
echo -e "Frontend: ${GREEN}$HOSTING_URL${NC}"
echo -e "Backend API: ${GREEN}https://tastory-api-vbx2teipca-uc.a.run.app${NC}"

echo -e "\n${YELLOW}Test your app:${NC}"
echo "1. Open $HOSTING_URL in your browser"
echo "2. Search for recipes like 'pasta' or 'chocolate cake'"
echo "3. Test the TTS feature (currently in French mode)"

echo -e "\n${YELLOW}For the hackathon:${NC}"
echo "- Show the <2s search performance"
echo "- Demonstrate 230K+ recipes"
echo "- Highlight GCP architecture"
echo "- Show $0 development cost"

# Open in browser
echo -e "\n${YELLOW}Opening your app in the browser...${NC}"
open "$HOSTING_URL" 