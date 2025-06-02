#!/bin/bash

# Verify Branch Protection Rules for Tastory Repository
# This script checks that all branch protection rules are properly configured

echo "🔍 Verifying Branch Protection Rules for Tastory Repository"
echo "==========================================================="

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check protection rule
check_protection() {
    local branch=$1
    local expected_reviewers=$2
    
    echo -e "\n📌 Checking ${YELLOW}$branch${NC} branch protection..."
    
    # Check if protection exists
    if gh api repos/OS366/Tastory/branches/$branch/protection 2>/dev/null >/dev/null; then
        echo -e "  ✅ Protection enabled"
        
        # Check required reviewers
        actual_reviewers=$(gh api repos/OS366/Tastory/branches/$branch/protection 2>/dev/null | jq -r '.required_pull_request_reviews.required_approving_review_count // 0')
        if [ "$actual_reviewers" == "$expected_reviewers" ]; then
            echo -e "  ✅ Required reviewers: ${GREEN}$actual_reviewers${NC} (Expected: $expected_reviewers)"
        else
            echo -e "  ❌ Required reviewers: ${RED}$actual_reviewers${NC} (Expected: $expected_reviewers)"
        fi
        
        # Check dismiss stale reviews
        dismiss_stale=$(gh api repos/OS366/Tastory/branches/$branch/protection 2>/dev/null | jq -r '.required_pull_request_reviews.dismiss_stale_reviews // false')
        if [ "$dismiss_stale" == "true" ]; then
            echo -e "  ✅ Dismiss stale reviews: ${GREEN}Enabled${NC}"
        else
            echo -e "  ⚠️  Dismiss stale reviews: ${YELLOW}Disabled${NC}"
        fi
        
        # Check force push protection
        allow_force=$(gh api repos/OS366/Tastory/branches/$branch/protection 2>/dev/null | jq -r '.allow_force_pushes.enabled // false')
        if [ "$allow_force" == "false" ]; then
            echo -e "  ✅ Force push protection: ${GREEN}Enabled${NC}"
        else
            echo -e "  ❌ Force push protection: ${RED}Disabled${NC}"
        fi
        
        # Check deletion protection
        allow_deletion=$(gh api repos/OS366/Tastory/branches/$branch/protection 2>/dev/null | jq -r '.allow_deletions.enabled // false')
        if [ "$allow_deletion" == "false" ]; then
            echo -e "  ✅ Deletion protection: ${GREEN}Enabled${NC}"
        else
            echo -e "  ❌ Deletion protection: ${RED}Disabled${NC}"
        fi
        
        # Special note for development branch
        if [ "$branch" == "development" ] && [ "$expected_reviewers" == "0" ]; then
            echo -e "  ℹ️  Solo developer mode: ${YELLOW}Self-merge allowed${NC}"
        fi
        
    else
        echo -e "  ❌ ${RED}No protection rules found!${NC}"
    fi
}

# Check default branch
echo -e "\n🌟 Default Branch Configuration"
default_branch=$(gh api repos/OS366/Tastory --jq '.default_branch')
if [ "$default_branch" == "development" ]; then
    echo -e "  ✅ Default branch: ${GREEN}$default_branch${NC}"
else
    echo -e "  ❌ Default branch: ${RED}$default_branch${NC} (Expected: development)"
fi

# Check each branch
check_protection "development" "0"
check_protection "stable" "2"
check_protection "main" "2"

echo -e "\n==========================================================="
echo "✨ Protection verification complete!"
echo ""
echo "📚 Reference: See BRANCHING_STRATEGY.md for full details" 