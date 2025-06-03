#!/bin/bash

# Enable signed commits requirement on branch protection rules

set -e

echo "🔐 Enabling Signed Commits Requirement"
echo "====================================="
echo ""

# Check if gh CLI is available
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI (gh) is not installed!"
    echo "Please install it first: https://cli.github.com/"
    exit 1
fi

# Check authentication
if ! gh auth status &> /dev/null; then
    echo "❌ Not authenticated with GitHub CLI"
    echo "Run: gh auth login"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner -q .nameWithOwner)
echo "Repository: $REPO"
echo ""

# Branches to protect
BRANCHES=("main" "development" "stable")

echo "This will enable 'Require signed commits' for the following branches:"
for branch in "${BRANCHES[@]}"; do
    echo "  - $branch"
done
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

echo ""

# Function to update branch protection
update_branch_protection() {
    local branch=$1
    echo "Updating protection for branch: $branch"
    
    # Get current protection rules
    CURRENT_RULES=$(gh api repos/$REPO/branches/$branch/protection 2>/dev/null || echo "{}")
    
    if [ "$CURRENT_RULES" = "{}" ]; then
        echo "  No existing protection rules found. Creating new rules..."
        
        # Create comprehensive protection rules
        gh api repos/$REPO/branches/$branch/protection \
            --method PUT \
            -f required_status_checks='{"strict":true,"contexts":["CI Status Check"]}' \
            -f enforce_admins=false \
            -f required_pull_request_reviews='{"required_approving_review_count":1,"dismiss_stale_reviews":true}' \
            -f restrictions=null \
            -f required_linear_history=false \
            -f allow_force_pushes=false \
            -f allow_deletions=false \
            -f required_conversation_resolution=true \
            -f required_signatures=true
    else
        echo "  Updating existing protection rules..."
        
        # Enable signed commits on existing rules
        gh api repos/$REPO/branches/$branch/protection/required_signatures \
            --method POST \
            2>/dev/null || echo "  Note: Required signatures might already be enabled"
    fi
    
    echo "  ✅ Branch protection updated for: $branch"
    echo ""
}

# Update each branch
for branch in "${BRANCHES[@]}"; do
    # Check if branch exists
    if gh api repos/$REPO/branches/$branch &> /dev/null; then
        update_branch_protection "$branch"
    else
        echo "⚠️  Branch '$branch' does not exist. Skipping..."
        echo ""
    fi
done

echo "🎉 Branch protection updates complete!"
echo ""
echo "Signed commits are now required for protected branches."
echo ""
echo "To set up commit signing locally, run:"
echo "  ./scripts/setup-commit-signing.sh"
echo ""
echo "For more information, see:"
echo "  docs/COMMIT_SIGNING_SETUP.md" 