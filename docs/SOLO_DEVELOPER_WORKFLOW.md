# Solo Developer Workflow Guide

## Overview

This guide explains how to work effectively as a solo developer with Tastory's branch protection rules configured for self-merge capabilities.

## Current Configuration

### Branch Protection Status

- **Development Branch**: Requires PRs, but allows self-merge (0 reviewers required)
- **Stable Branch**: Requires 2 reviewers (team collaboration ready)
- **Main Branch**: Requires 2 reviewers + admin approval (production ready)

## Workflow Steps

### 1. Daily Development Flow

```bash
# Always start from development branch
git checkout development
git pull origin development

# Create feature branch
git checkout -b feature/your-feature-name

# Make your changes
# ... edit files ...
git add .
git commit -m "feat: your feature description"

# Push feature branch
git push -u origin feature/your-feature-name
```

### 2. Creating Pull Requests

```bash
# Using GitHub CLI (recommended)
gh pr create --base development --title "feat: Your feature" --body "Description"

# Or visit the URL provided by git push
```

### 3. Self-Merging Process

Since development branch requires 0 reviewers, you can:

1. **Review your own code** - Even though not required, it's good practice
2. **Wait for CI checks** - All status checks must pass
3. **Merge immediately** - Click "Merge pull request" on GitHub or use:
   ```bash
   gh pr merge <PR-NUMBER> --merge
   ```

### 4. Cleanup

```bash
# After merging, update local development
git checkout development
git pull origin development

# Delete local feature branch
git branch -d feature/your-feature-name

# Delete remote feature branch (if not auto-deleted)
git push origin --delete feature/your-feature-name
```

## Benefits of This Setup

### ✅ Advantages

1. **Version Control History** - All changes go through PRs
2. **CI/CD Integration** - Tests run on every change
3. **Easy Collaboration** - Ready to add team members
4. **Professional Workflow** - Industry-standard practices
5. **No Approval Delays** - Self-merge for rapid iteration

### 🛡️ Safeguards

- No direct pushes to protected branches
- All changes must pass status checks
- Clear audit trail of all changes
- Easy to increase protection as team grows

## Transitioning to Team Development

When you're ready to add collaborators:

1. **Update development branch protection**:

   ```bash
   # Change required_approving_review_count from 0 to 1
   ```

2. **Add collaborators** to the repository

3. **Update this guide** to reflect team workflow

## Quick Commands Reference

```bash
# Check branch protection status
./scripts/verify-branch-protection.sh

# Create PR from current branch
gh pr create

# List open PRs
gh pr list

# Merge a PR
gh pr merge <NUMBER>

# View PR status
gh pr view <NUMBER>
```

## Tips for Solo Developers

1. **Write Good PR Descriptions** - Future you will thank present you
2. **Use Conventional Commits** - Maintains clean history
3. **Review Your Own Code** - Catch issues before merging
4. **Keep PRs Small** - Easier to review and revert if needed
5. **Use Draft PRs** - For work in progress

## Troubleshooting

### "PR requires approval" error

- Run `./scripts/verify-branch-protection.sh`
- Ensure development shows "0 required reviewers"

### Can't push to development

- You must create a PR even as admin
- Direct pushes are blocked by design

### PR won't merge

- Check all CI status checks are passing
- Pull latest changes: `git pull origin development`

## Remember

Even though you can self-merge, maintaining good practices now makes it easier to collaborate later!
