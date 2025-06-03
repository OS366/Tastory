#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up branch protection rules for Tastory repository...${NC}"

# Function to set branch protection
setup_branch_protection() {
    local branch=$1
    local required_reviews=$2
    
    echo -e "\n${YELLOW}Setting up protection rules for ${branch} branch...${NC}"
    
    # Create JSON payload for the API
    json_payload=$(cat << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["test", "lint"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismissal_restrictions": {},
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": $required_reviews
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true,
  "lock_branch": false
}
EOF
)
    
    # Create branch protection rule using the JSON payload
    echo "$json_payload" | gh api \
      --method PUT \
      "/repos/OS366/Tastory/branches/$branch/protection" \
      --input -
      
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Successfully set up protection rules for ${branch} branch${NC}"
    else
        echo -e "${RED}Failed to set up protection rules for ${branch} branch${NC}"
        exit 1
    fi
}

# Check if gh CLI is installed
if ! command -v gh &> /dev/null; then
    echo -e "${RED}GitHub CLI (gh) is not installed. Please install it first.${NC}"
    exit 1
fi

# Check if logged in to GitHub
if ! gh auth status &> /dev/null; then
    echo -e "${RED}Not logged in to GitHub. Please run 'gh auth login' first.${NC}"
    exit 1
fi

# Set up protection rules for each branch
# main branch - requires 2 reviews
setup_branch_protection "main" 2

# stable branch - requires 2 reviews
setup_branch_protection "stable" 2

# development branch - requires 1 review
setup_branch_protection "development" 1

echo -e "\n${GREEN}Branch protection rules have been set up successfully!${NC}"
echo -e "${YELLOW}Remember:${NC}"
echo "- Feature branches should be merged into development via PR"
echo "- Development should be merged into stable via PR"
echo "- Stable should be merged into main via PR"
echo "- All PRs require code review and passing CI checks" 