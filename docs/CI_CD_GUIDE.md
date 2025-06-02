# CI/CD Pipeline Guide

## Overview

Tastory uses GitHub Actions for continuous integration and deployment. The pipeline ensures code quality, security, and automated deployments.

## Workflows

### 1. CI Workflow (`ci.yml`)

**Triggers**:

- Push to `development`, `stable`, or `main`
- Pull requests to protected branches

**Jobs**:

#### Backend Tests

- **Linting**: Black, isort, Flake8
- **Testing**: pytest with coverage across Python 3.9, 3.10, 3.11
- **Security**: Vulnerability scanning with Trivy

#### Frontend Tests

- **Linting**: ESLint for React code
- **Build**: Webpack production build
- **Artifacts**: Build artifacts saved for 7 days

#### Status Check

- **alls-green**: Required status check for branch protection

### 2. Deploy Workflow (`deploy.yml`)

**Triggers**:

- Push to `main` branch
- Manual workflow dispatch

**Environments**:

- Production (default)
- Staging (manual selection)

**Jobs**:

- Backend deployment (placeholder for actual deployment)
- Frontend deployment (placeholder for actual deployment)
- Post-deployment notifications

### 3. Release Workflow (`release.yml`)

**Triggers**:

- Push of version tags (`v*.*.*`)

**Features**:

- Automated changelog generation
- GitHub release creation
- Version file updates
- PR creation for version bumps

### 4. Dependency Review (`dependency-review.yml`)

**Triggers**:

- Pull requests to protected branches

**Checks**:

- License compliance
- Security vulnerabilities
- Outdated dependencies

## Configuration Files

### Python Linting

#### `.flake8`

- Max line length: 120
- Ignored errors: E203, W503, E501
- Max complexity: 10

#### `pyproject.toml`

- Black formatter settings
- isort import sorting
- pytest configuration
- Coverage settings

### Frontend Linting

#### `frontend/.eslintrc.json`

- React and React Hooks rules
- ES2021 environment
- Custom rule configurations

## Required Secrets

Add these in GitHub repository settings:

### Production Deployment

- `API_URL`: Backend API endpoint
- `DATABASE_URL`: MongoDB connection string
- `DEPLOY_KEY`: SSH key for deployment server

### Notifications (Optional)

- `SLACK_WEBHOOK`: Slack notifications
- `DISCORD_WEBHOOK`: Discord notifications

## Setting Up CI/CD

### 1. Enable Required Status Checks

After the first CI run, update branch protection:

```bash
# Run verification script
./scripts/verify-branch-protection.sh

# In GitHub UI:
# Settings → Branches → Edit protection rule
# Add "CI Status Check" as required
```

### 2. Configure Environments

1. Go to Settings → Environments
2. Create `production` environment
3. Add protection rules:
   - Required reviewers
   - Deployment branches: `main` only

### 3. Set Up Deployment

Replace placeholder deployment steps in `deploy.yml`:

#### For Heroku:

```yaml
- name: Deploy to Heroku
  uses: akhileshns/heroku-deploy@v3.12.12
  with:
    heroku_api_key: ${{secrets.HEROKU_API_KEY}}
    heroku_app_name: "tastory-app"
    heroku_email: "your-email@example.com"
```

#### For AWS:

```yaml
- name: Deploy to AWS
  uses: aws-actions/configure-aws-credentials@v1
  with:
    aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
    aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
    aws-region: us-east-1
```

## Running CI Locally

### Python Linting

```bash
# Install tools
pip install black isort flake8

# Run checks
black --check app.py
isort --check-only app.py
flake8 app.py
```

### Frontend Linting

```bash
cd frontend
npm install
npx eslint src/
```

## Troubleshooting

### CI Failures

1. **Black formatting errors**:

   ```bash
   black app.py  # Auto-fix
   ```

2. **Import sorting errors**:

   ```bash
   isort app.py  # Auto-fix
   ```

3. **ESLint errors**:
   ```bash
   npx eslint src/ --fix  # Auto-fix
   ```

### Deployment Issues

- Check environment secrets are set
- Verify deployment branches in environment settings
- Check deployment service status

## Best Practices

1. **Keep CI Fast**

   - Use caching for dependencies
   - Run jobs in parallel
   - Skip unnecessary steps

2. **Security First**

   - Regular dependency updates
   - Vulnerability scanning
   - License compliance

3. **Clear Feedback**
   - Descriptive job names
   - Helpful error messages
   - Status badges in README

## Future Enhancements

- [ ] Add E2E testing with Cypress/Playwright
- [ ] Implement database migration checks
- [ ] Add performance testing
- [ ] Set up staging environment auto-deploy
- [ ] Add mobile app builds (if applicable)
- [ ] Implement rollback mechanisms
