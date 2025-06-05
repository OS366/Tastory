#!/bin/bash

# Monitor Tastory deployment to GCP

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔍 Monitoring Tastory Deployment${NC}"
echo "=================================="

# URLs
ACTIONS_URL="https://github.com/OS366/Tastory/actions"
FRONTEND_URL="https://tastory-hackathon.web.app"
BACKEND_URL="https://tastory-api-vbx2teipca-uc.a.run.app"

echo -e "\n${YELLOW}📊 Deployment Dashboard:${NC}"
echo "GitHub Actions: $ACTIONS_URL"
echo "Frontend URL: $FRONTEND_URL"
echo "Backend URL: $BACKEND_URL"

# Function to check URL status
check_url() {
    local url=$1
    local name=$2
    local status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)
    
    if [ "$status" = "200" ]; then
        echo -e "${GREEN}✅ $name is LIVE! (HTTP $status)${NC}"
    elif [ "$status" = "000" ]; then
        echo -e "${RED}❌ $name is DOWN (No response)${NC}"
    else
        echo -e "${YELLOW}⚠️  $name returned HTTP $status${NC}"
    fi
}

# Function to monitor GitHub Actions
monitor_actions() {
    echo -e "\n${YELLOW}🔄 Checking GitHub Actions workflow...${NC}"
    
    # Get latest run
    local run_info=$(gh run list --workflow="Deploy to GCP" --limit 1 --json status,conclusion,databaseId,createdAt 2>/dev/null)
    
    if [ -z "$run_info" ] || [ "$run_info" = "[]" ]; then
        echo "No deployment runs found yet. Merge to main to trigger deployment."
        return
    fi
    
    # Parse run info
    local status=$(echo "$run_info" | jq -r '.[0].status')
    local conclusion=$(echo "$run_info" | jq -r '.[0].conclusion')
    local run_id=$(echo "$run_info" | jq -r '.[0].databaseId')
    
    echo "Latest deployment run #$run_id:"
    
    if [ "$status" = "completed" ]; then
        if [ "$conclusion" = "success" ]; then
            echo -e "${GREEN}✅ Deployment COMPLETED SUCCESSFULLY!${NC}"
        else
            echo -e "${RED}❌ Deployment FAILED with conclusion: $conclusion${NC}"
        fi
    elif [ "$status" = "in_progress" ]; then
        echo -e "${YELLOW}🚀 Deployment IN PROGRESS...${NC}"
        echo "Watch live at: https://github.com/OS366/Tastory/actions/runs/$run_id"
    else
        echo "Status: $status"
    fi
}

# Main monitoring loop
echo -e "\n${BLUE}Starting monitoring...${NC}"
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo -e "${BLUE}🔍 Tastory Deployment Monitor${NC}"
    echo "=============================="
    echo "Time: $(date)"
    
    # Check GitHub Actions
    monitor_actions
    
    # Check service health
    echo -e "\n${YELLOW}🏥 Service Health Check:${NC}"
    check_url "$BACKEND_URL/health" "Backend API"
    check_url "$FRONTEND_URL" "Frontend"
    
    # GCP-specific monitoring
    echo -e "\n${YELLOW}☁️  GCP Cloud Run Status:${NC}"
    gcloud run services describe tastory-api --region us-central1 --format="value(status.url,status.conditions[0].status)" 2>/dev/null | head -2 || echo "Run 'gcloud auth login' to see Cloud Run details"
    
    echo -e "\n${YELLOW}📋 Quick Commands:${NC}"
    echo "• View logs: gcloud run logs tail --service tastory-api"
    echo "• View Actions: open $ACTIONS_URL"
    echo "• Test backend: curl $BACKEND_URL/health"
    
    echo -e "\n${BLUE}Refreshing in 10 seconds...${NC}"
    sleep 10
done 