#!/bin/bash

# Fix Cloud Run environment variable type conflict

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Fixing Cloud Run Environment Variables${NC}"
echo "=========================================="

SERVICE_NAME="tastory-api"
REGION="us-central1"

echo -e "${YELLOW}Current service configuration:${NC}"
gcloud run services describe $SERVICE_NAME --region $REGION --format="yaml(spec.template.spec.containers[0].env)" || echo "Service not found"

echo -e "\n${YELLOW}Clearing existing environment variables...${NC}"
# Update the service to clear all env vars first
gcloud run services update $SERVICE_NAME \
  --region $REGION \
  --clear-env-vars

echo -e "\n${GREEN}✅ Environment variables cleared${NC}"

echo -e "\n${YELLOW}Re-running deployment...${NC}"
# Now trigger the deployment again
echo "Run 'git commit --amend --no-edit && git push -f origin main' to trigger deployment"
echo "Or manually run the deployment script" 