#!/bin/bash

# Temporarily disable main branch protection for solo developer

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔓 Disabling Main Branch Protection${NC}"
echo "===================================="

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

echo -e "${YELLOW}Removing branch protection from 'main'...${NC}"

# Delete branch protection entirely
gh api \
  --method DELETE \
  -H "Accept: application/vnd.github+json" \
  "/repos/$OWNER/$REPO/branches/$BRANCH/protection"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Successfully removed main branch protection!${NC}"
    echo ""
    echo "You can now:"
    echo "  ✓ Merge without reviewers"
    echo "  ✓ Push directly to main"
    echo "  ✓ Use unverified commits"
    echo ""
    echo -e "${YELLOW}Warning: Branch protection is completely disabled.${NC}"
    echo "Consider re-enabling it after the deployment."
else
    echo -e "${RED}❌ Failed to remove branch protection${NC}"
    echo ""
    echo "Alternative: Manually disable it at:"
    echo "https://github.com/$OWNER/$REPO/settings/branches"
    echo ""
    echo "1. Click on 'main' branch rule"
    echo "2. Scroll to bottom and click 'Delete this rule'"
fi 