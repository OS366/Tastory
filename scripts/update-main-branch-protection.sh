#!/bin/bash

# Update main branch protection for solo developer workflow
# Removes 2 reviewer requirement and verified commits requirement

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔧 Updating Main Branch Protection for Solo Developer${NC}"
echo "===================================================="

# Variables
OWNER="OS366"
REPO="Tastory"
BRANCH="main"

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}❌ GitHub CLI (gh) not found. Please install it first.${NC}"
    echo "Install with: brew install gh"
    exit 1
fi

# Check authentication
echo -e "${YELLOW}Checking GitHub authentication...${NC}"
if ! gh auth status &> /dev/null; then
    echo -e "${RED}❌ Not authenticated. Running 'gh auth login'...${NC}"
    gh auth login
fi

echo -e "${YELLOW}Updating branch protection rules for 'main'...${NC}"

# Update branch protection with minimal requirements for solo developer
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO/branches/$BRANCH/protection" \
  --field required_status_checks='{"strict":false,"contexts":[]}' \
  --field enforce_admins=false \
  --field required_pull_request_reviews=null \
  --field restrictions=null \
  --field allow_force_pushes=false \
  --field allow_deletions=false \
  --field required_conversation_resolution=false \
  --field lock_branch=false \
  --field allow_fork_syncing=true \
  --field required_linear_history=false \
  --field required_signatures=false

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Successfully updated main branch protection!${NC}"
    echo ""
    echo "Changes made:"
    echo "  ✓ Removed 2 reviewer requirement"
    echo "  ✓ Removed verified commits requirement"
    echo "  ✓ Removed required status checks"
    echo "  ✓ Prevented force pushes and deletions"
    echo ""
    echo -e "${GREEN}You can now merge to main as a solo developer!${NC}"
else
    echo -e "${RED}❌ Failed to update branch protection${NC}"
    echo "You may need to update permissions manually in GitHub settings"
fi

echo ""
echo "To verify changes, visit:"
echo "https://github.com/$OWNER/$REPO/settings/branches" 