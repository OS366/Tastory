#!/bin/bash

# Update branch protection rules to include CI Status Check
# Run this after the first CI workflow has completed

echo "🔄 Updating branch protection rules with CI Status Check..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to update protection with status checks
update_protection_with_ci() {
    local branch=$1
    local reviewers=$2
    
    echo -e "\n📌 Updating ${YELLOW}$branch${NC} branch protection..."
    
    # Create JSON configuration
    cat > ${branch}-protection-ci.json << EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["CI Status Check"]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "required_approving_review_count": $reviewers
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_linear_history": false
}
EOF
    
    # Apply the protection
    gh api repos/OS366/Tastory/branches/$branch/protection -X PUT --input ${branch}-protection-ci.json
    
    # Clean up
    rm ${branch}-protection-ci.json
    
    echo -e "  ✅ Updated with CI Status Check requirement"
}

# Update each branch
update_protection_with_ci "development" "0"
update_protection_with_ci "stable" "2"
update_protection_with_ci "main" "2"

echo -e "\n✅ Branch protection rules updated with CI requirements!"
echo -e "Run ${GREEN}./scripts/verify-branch-protection.sh${NC} to verify the changes." 