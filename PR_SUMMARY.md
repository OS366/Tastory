# Pull Request Summary

## PR 1: development → stable

### Title

Release: CI/CD Pipeline, Error Handling, and Major Cleanup

### Description

This release includes comprehensive improvements to the Tastory application:

#### 🚀 CI/CD & Deployment

- Complete GitHub Actions workflow for automatic deployment to GCP
- Backend deploys to Cloud Run on push to main
- Frontend deploys to Firebase Hosting
- Unified deployment script (`scripts/deploy-all.sh`)

#### 🛡️ Error Handling

- Custom ErrorBoundary component with Tastory-styled 404 page
- Graceful backend error handling with retry functionality
- Fixed process.env errors in production

#### 🧹 Project Cleanup

- Removed 3.5GB of data files (moved to git-ignored `data/` folder)
- Removed unused dependencies (Tailwind CSS)
- Organized scripts into `scripts/` folder
- Organized documentation into `docs/` folder
- Added comprehensive .gitignore rules

#### 📚 Documentation

- Complete log viewing guide for GCP and Firebase
- Deployment setup documentation
- CI/CD configuration guides

### Changes: 43 commits, +5,887 lines, -1,280 lines

---

## PR 2: stable → main

### Title

Production Release: Tastory v1.0 - The Food Search Engine

### Description

🎉 **Ready for production deployment with full automation!**

This release deploys the complete Tastory application with:

- ✅ 230K+ searchable recipes
- ✅ AI-powered semantic search
- ✅ Multilingual TTS support
- ✅ <2 second search response time
- ✅ Automatic CI/CD pipeline

**Upon merge, GitHub Actions will automatically:**

1. Deploy backend to Cloud Run
2. Deploy frontend to Firebase Hosting
3. Run health checks
4. Report deployment status

### Production URLs

- Frontend: https://tastory-hackathon.web.app
- Backend API: https://tastory-api-vbx2teipca-uc.a.run.app

### Requirements

Ensure these GitHub Secrets are configured:

- [x] `GCP_SA_KEY`
- [x] `MONGODB_URI`
- [x] `FIREBASE_SERVICE_ACCOUNT`
