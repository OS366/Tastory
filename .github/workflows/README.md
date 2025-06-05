# 🚀 Tastory GitHub Actions Workflows

This directory contains the automated workflows for Tastory's CI/CD pipeline. Our system separates regular development builds from production releases using a **"Hot Release"** strategy.

## 📋 Workflow Overview

### 🔥 **Hot Release System** (`hot-release.yml`)

**Purpose**: Automatic deployment to GCP when GitHub releases are published

**Triggers**:

- ✅ GitHub release published
- ✅ Manual dispatch (for testing)

**What it does**:

1. 🚦 Pre-flight checks (get release tag, check if pre-release)
2. 🧪 Quick smoke tests on release code
3. 🚀 Deploy backend to GCP Cloud Run with release tag
4. 🌐 Deploy frontend to Firebase Hosting
5. ✅ Health checks and verification
6. 🎉 Success notification or 🚨 rollback on failure

**Key Features**:

- Uses release tags for Docker image versioning
- Deploys specific release code (not latest commit)
- Includes emergency rollback procedures
- Provides detailed deployment status

---

### 🔄 **Regular CI/CD Pipeline** (`ci.yml`)

**Purpose**: Continuous testing and quality assurance for all code changes

**Triggers**:

- ✅ Every push to any branch
- ✅ Pull requests to main/development
- ✅ Manual dispatch

**What it does**:

1. 🧹 **Backend Linting** (Black, isort, Flake8) - _BLOCKS MERGE_
2. 🧪 **Backend Tests** (Unit, Integration, API, Database) - _BLOCKS MERGE_
3. 💨 **Smoke Tests** (Critical functionality) - _BLOCKS MERGE_
4. 🎨 **Frontend Linting** (ESLint) - _BLOCKS MERGE_
5. 📦 **Frontend Build** - _BLOCKS MERGE_
6. ⚡ **Performance Tests** (Optional benchmarks)
7. 🔒 **Security Scanning** (Trivy, safety)
8. 📊 **Test Reports** (Coverage, summaries)

**Branch Protection**: ✅ All required jobs must pass before merge

---

### 📦 **Release Management** (`release.yml`)

**Purpose**: Create GitHub releases with changelogs when tags are pushed

**Triggers**:

- ✅ Git tags (v*.*.\*)

**What it does**:

1. 📝 Generate changelog from commits
2. 🏷️ Create GitHub release
3. 📋 Update version files
4. 🔄 Create PR with version updates

---

### 🚫 **Legacy Deploy** (`deploy.yml`)

**Status**: DISABLED - Kept for reference

**Purpose**: Old deployment workflow replaced by hot-release.yml

---

### 🔍 **Security & Quality**

#### `dependency-review.yml`

- Reviews dependency changes in PRs
- Scans for vulnerabilities
- Provides security insights

#### `verify-commits.yml`

- Validates commit message formats
- Ensures consistency

---

## 🔥 How Hot Releasing Works

### 1. **Development Phase**

```bash
git push origin feature/my-feature    # Triggers ci.yml
```

- ✅ All tests run automatically
- ✅ Branch protection prevents broken merges
- ✅ No deployment (development only)

### 2. **Release Phase**

```bash
git tag v1.2.0
git push origin v1.2.0              # Triggers release.yml
```

- ✅ Creates GitHub release
- ✅ Triggers hot-release.yml automatically
- 🔥 **DEPLOYS TO PRODUCTION GCP**

### 3. **Manual Hot Release**

- Go to GitHub Actions → "🔥 Hot Release"
- Click "Run workflow"
- Enter release tag (e.g., v1.2.0)
- 🚀 Deploys specific release to GCP

---

## 🎯 Deployment Strategy

| Event          | Workflow                          | Action            | Environment |
| -------------- | --------------------------------- | ----------------- | ----------- |
| Push to branch | `ci.yml`                          | Test only         | None        |
| Pull request   | `ci.yml`                          | Test only         | None        |
| Tag push (v\*) | `release.yml` → `hot-release.yml` | **Deploy to GCP** | Production  |
| Manual release | `hot-release.yml`                 | **Deploy to GCP** | Production  |

---

## 🛡️ Safety Features

### **Branch Protection Rules**

- ✅ All CI tests must pass
- ✅ At least 1 code review required
- ✅ Conversations must be resolved
- ✅ Up-to-date branches required

### **Hot Release Safety**

- ✅ Smoke tests before deployment
- ✅ Health checks after deployment
- ✅ Tagged releases for traceability
- 🚨 Emergency rollback procedures

### **Test Coverage**

- ✅ 80% minimum code coverage
- ✅ Unit, integration, API, database tests
- ✅ Performance benchmarks
- ✅ Security vulnerability scanning

---

## 🚀 Production URLs

After successful hot release:

- **Frontend**: https://tastory-hackathon.web.app
- **Backend**: https://tastory-api-vbx2teipca-uc.a.run.app

---

## 📊 Monitoring

### **GitHub Actions**

- View workflow runs in "Actions" tab
- Download test coverage reports
- Monitor deployment status

### **GCP Console**

- Cloud Run service logs
- Firebase Hosting metrics
- Resource usage monitoring

---

## 🔧 Troubleshooting

### **Hot Release Failed**

1. Check GitHub Actions logs
2. Verify GCP credentials (`GCP_SA_KEY` secret)
3. Check Firebase credentials (`FIREBASE_SERVICE_ACCOUNT` secret)
4. Review MongoDB connection (`MONGODB_URI` secret)

### **CI Tests Failing**

1. Run tests locally: `pytest tests/`
2. Check linting: `black --check .`
3. Review error logs in Actions tab
4. Fix issues and push again

### **Manual Deployment**

If hot release fails, use the disabled deploy.yml:

1. Enable `deploy.yml` temporarily
2. Run manual workflow dispatch
3. Re-disable after deployment

---

_🔥 Hot releasing enables rapid, reliable deployments while maintaining code quality through comprehensive CI/CD automation._
