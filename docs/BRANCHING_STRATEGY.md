# Tastory Branching Strategy

## Overview

Tastory follows a three-tier branching model designed to ensure code quality and stable releases.

## Branch Hierarchy

### 1. `development` (Default Branch)

- **Purpose**: Active development and feature integration
- **Who uses it**: All developers for daily work
- **Merges from**: Feature branches, bug fix branches
- **Merges to**: `stable` branch
- **Protection**: Basic protection, requires PR reviews

### 2. `stable`

- **Purpose**: Integration testing and release preparation
- **Who uses it**: QA team and release managers
- **Merges from**: `development` branch only
- **Merges to**: `main` branch
- **Protection**: Strict protection, requires passing tests and multiple reviews

### 3. `main`

- **Purpose**: Production releases only
- **Who uses it**: Release managers only
- **Merges from**: `stable` branch only
- **Merges to**: Hotfix branches (if needed)
- **Protection**: Maximum protection, requires admin approval

## Workflow

### Feature Development

1. Create feature branch from `development`

   ```bash
   git checkout development
   git pull origin development
   git checkout -b feature/your-feature-name
   ```

2. Make changes and push to feature branch

   ```bash
   git add .
   git commit -m "feat: your feature description"
   git push origin feature/your-feature-name
   ```

3. Create PR to merge into `development`

### Release Process

1. **Development → Stable**

   - When features are ready for testing
   - Create PR from `development` to `stable`
   - Run comprehensive tests
   - Fix any issues in `development` and re-merge

2. **Stable → Main**
   - When all tests pass and release is approved
   - Create PR from `stable` to `main`
   - Tag the release on `main`
   ```bash
   git checkout main
   git pull origin main
   git tag -a v1.0.0 -m "Release version 1.0.0"
   git push origin v1.0.0
   ```

### Hotfix Process

1. Create hotfix branch from `main`

   ```bash
   git checkout main
   git pull origin main
   git checkout -b hotfix/critical-bug-fix
   ```

2. Fix the issue and create PRs to:
   - `main` (immediate fix)
   - `stable` (include in next release)
   - `development` (ensure fix is in future development)

## Branch Naming Conventions

- Features: `feature/short-description`
- Bug fixes: `bugfix/issue-number-description`
- Hotfixes: `hotfix/critical-issue-description`
- Releases: `release/v1.0.0`

## Commit Message Format

Follow conventional commits:

- `feat:` New features
- `fix:` Bug fixes
- `docs:` Documentation changes
- `style:` Code style changes (formatting, semicolons, etc.)
- `refactor:` Code refactoring
- `test:` Test additions or changes
- `chore:` Build process or auxiliary tool changes

## Protection Rules

### Development Branch

- Require pull request reviews (1 reviewer)
- Dismiss stale pull request approvals
- Require branches to be up to date

### Stable Branch

- Require pull request reviews (2 reviewers)
- Require status checks to pass
- Require branches to be up to date
- Include administrators in restrictions

### Main Branch

- Require pull request reviews (2 reviewers + admin)
- Require status checks to pass
- Require branches to be up to date
- Restrict who can push (release managers only)
- Require signed commits

## Solo Developer Configuration

For solo developers or during the initial development phase, the `development` branch protection can be adjusted to:

- **Required reviewers**: 0 (allows self-merge)
- **Still requires**: Pull requests (no direct pushes)
- **Maintains**: All other protection features

This configuration ensures code goes through PRs for documentation and history while allowing solo developers to merge their own work. As the team grows, increase the required reviewers accordingly.

### Adjusting for Team Growth

```bash
# Solo developer (current)
required_approving_review_count: 0

# Small team (2-5 developers)
required_approving_review_count: 1

# Larger team (5+ developers)
required_approving_review_count: 2
```

## Quick Reference

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   feature   │ --> │ development │ --> │   stable    │ --> │    main    │
│  branches   │     │  (default)  │     │   (test)    │     │ (release)  │
└─────────────┘     └─────────────┘     └─────────────┘     └────────────┘
```

## GitHub Settings

The repository is configured with:

- **Default branch**: `development`
- **Protected branches**: All three main branches
- **Auto-delete head branches**: Enabled for feature branches
- **Merge options**: Squash and merge preferred for features
