#!/bin/bash

# Tastory Full Deployment Script
# Deploys both backend (Cloud Run) and frontend (Firebase)

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Tastory Full Deployment Script${NC}"
echo "====================================="

# Check for required tools
check_requirements() {
    echo -e "${YELLOW}Checking requirements...${NC}"
    
    if ! command -v gcloud &> /dev/null; then
        echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
        exit 1
    fi
    
    if ! command -v npm &> /dev/null; then
        echo -e "${RED}❌ npm not found. Please install Node.js first.${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}✅ All requirements met${NC}"
}

# Deploy backend to Cloud Run
deploy_backend() {
    echo -e "\n${YELLOW}📦 Deploying Backend to Cloud Run...${NC}"
    
    # Check if we're in the project root
    if [ ! -f "app.py" ]; then
        echo -e "${RED}❌ Error: app.py not found. Please run from project root.${NC}"
        exit 1
    fi
    
    # Submit build to Cloud Build
    echo "Building Docker image..."
    gcloud builds submit --config cloudbuild.yaml
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Backend deployed successfully!${NC}"
        echo "Backend URL: https://tastory-api-vbx2teipca-uc.a.run.app"
    else
        echo -e "${RED}❌ Backend deployment failed${NC}"
        exit 1
    fi
}

# Deploy frontend to Firebase
deploy_frontend() {
    echo -e "\n${YELLOW}🎨 Deploying Frontend to Firebase...${NC}"
    
    # Check if frontend directory exists
    if [ ! -d "frontend" ]; then
        echo -e "${RED}❌ Error: frontend directory not found${NC}"
        exit 1
    fi
    
    # Build frontend
    echo "Building frontend..."
    cd frontend
    npm install
    npm run build
    cd ..
    
    # Deploy to Firebase
    echo "Deploying to Firebase..."
    npx firebase deploy --only hosting
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend deployed successfully!${NC}"
        echo "Frontend URL: https://tastory-hackathon.web.app"
    else
        echo -e "${RED}❌ Frontend deployment failed${NC}"
        exit 1
    fi
}

# Test deployments
test_deployments() {
    echo -e "\n${YELLOW}🧪 Testing deployments...${NC}"
    
    # Test backend
    echo -n "Testing backend health... "
    BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tastory-api-vbx2teipca-uc.a.run.app/health)
    if [ "$BACKEND_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Backend is healthy${NC}"
    else
        echo -e "${RED}❌ Backend health check failed (HTTP $BACKEND_STATUS)${NC}"
    fi
    
    # Test frontend
    echo -n "Testing frontend... "
    FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://tastory-hackathon.web.app)
    if [ "$FRONTEND_STATUS" = "200" ]; then
        echo -e "${GREEN}✅ Frontend is accessible${NC}"
    else
        echo -e "${RED}❌ Frontend check failed (HTTP $FRONTEND_STATUS)${NC}"
    fi
}

# Show deployment info
show_info() {
    echo -e "\n${GREEN}📋 Deployment Summary${NC}"
    echo "====================="
    echo "Frontend: https://tastory-hackathon.web.app"
    echo "Backend API: https://tastory-api-vbx2teipca-uc.a.run.app"
    echo ""
    echo "View logs:"
    echo "- Backend: gcloud run logs read --service tastory-api"
    echo "- Frontend: firebase hosting:channel:list"
    echo ""
    echo "Monitor backend: https://console.cloud.google.com/run/detail/us-central1/tastory-api/"
}

# Main deployment flow
main() {
    check_requirements
    
    # Parse arguments
    if [ "$1" = "--backend-only" ]; then
        deploy_backend
    elif [ "$1" = "--frontend-only" ]; then
        deploy_frontend
    elif [ "$1" = "--help" ]; then
        echo "Usage: $0 [--backend-only|--frontend-only|--help]"
        echo "  No args: Deploy both frontend and backend"
        echo "  --backend-only: Deploy only the backend"
        echo "  --frontend-only: Deploy only the frontend"
        echo "  --help: Show this help message"
        exit 0
    else
        # Deploy both
        deploy_backend
        deploy_frontend
    fi
    
    test_deployments
    show_info
    
    echo -e "\n${GREEN}✨ Deployment complete!${NC}"
}

# Run main function
main "$@" 