#!/bin/bash

# Script to set up branch protection rules for Tastory
# This ensures pull requests cannot be merged if CI checks fail
# Admins can override these rules when necessary

echo "🛡️  Setting up branch protection rules for Tastory..."

# Create temporary JSON file for branch protection configuration
cat > /tmp/branch-protection.json << 'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "✅ All Tests Passed - Ready for Merge",
      "Backend Linting",
      "Backend Tests", 
      "Smoke Tests",
      "Frontend Linting",
      "Frontend Build & Test"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1,
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": false,
    "restrict_pushes": false
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "block_creations": false,
  "required_conversation_resolution": true
}
EOF

# Apply branch protection rules
echo "Applying branch protection to main branch..."
gh api \
  --method PUT \
  -H "Accept: application/vnd.github+json" \
  -H "X-GitHub-Api-Version: 2022-11-28" \
  "/repos/:owner/:repo/branches/main/protection" \
  --input /tmp/branch-protection.json

# Clean up temporary file
rm /tmp/branch-protection.json

if [ $? -eq 0 ]; then
    echo "✅ Branch protection rules applied successfully!"
    echo ""
    echo "🔒 Main branch protection settings:"
    echo "   ✅ Require pull request reviews (1 approval minimum)"
    echo "   ✅ Require all CI status checks to pass"
    echo "   ✅ Require conversations to be resolved"
    echo "   ✅ Dismiss stale reviews on new commits"
    echo "   ⚠️  Admin override ENABLED (you can bypass rules)"
    echo "   ❌ Force pushes blocked"
    echo "   ❌ Branch deletions blocked"
    echo ""
    echo "📋 Required CI checks that must pass:"
    echo "   • ✅ All Tests Passed - Ready for Merge"
    echo "   • Backend Linting"
    echo "   • Backend Tests (78 comprehensive tests)"
    echo "   • Smoke Tests (critical functionality)"
    echo "   • Frontend Linting"
    echo "   • Frontend Build & Test"
    echo ""
    echo "🛡️  Pull requests will be BLOCKED unless all checks pass"
    echo "👑 As admin, you can override and merge anyway if needed"
else
    echo "❌ Failed to apply branch protection rules"
    echo "Please check your GitHub permissions and try again"
fi 