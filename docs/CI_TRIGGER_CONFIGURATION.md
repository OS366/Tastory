# CI Trigger Configuration

## Overview

The Tastory CI/CD pipeline is configured to run automatically on every commit to any branch, ensuring continuous quality checks throughout development.

## Current Configuration

### CI Workflow (.github/workflows/ci.yml)

```yaml
on:
  push: # Trigger on every push to any branch
  workflow_dispatch: # Keep manual triggering option
```

This configuration means:

- ✅ **Every commit** to any branch triggers CI automatically
- ✅ **No branch restrictions** - works on feature branches, hotfixes, etc.
- ✅ **Manual trigger** option remains available via GitHub UI or CLI
- ❌ **No pull request triggers** - CI runs on commits, not PR events

### Benefits

1. **Early Detection**: Issues are caught immediately after each commit
2. **Continuous Feedback**: Developers get instant feedback on their changes
3. **Branch Protection**: All branches benefit from CI checks
4. **Simplified Workflow**: No need to create PRs just to run CI

### Other Workflows

- **Deploy** (.github/workflows/deploy.yml): Only triggers on pushes to `main` branch
- **Release** (.github/workflows/release.yml): Only triggers on version tags (v*.*.\*)
- **Dependency Review** (.github/workflows/dependency-review.yml): Only runs on pull requests

## Usage

### Automatic Triggers

Simply push your commits:

```bash
git add .
git commit -m "feat: your changes"
git push origin your-branch
```

### Manual Triggers

Using GitHub CLI:

```bash
gh workflow run ci.yml --ref your-branch
```

### Monitor CI Status

Using the helper script:

```bash
./check-ci.sh
```

## Considerations

- **Cost**: More CI runs mean more GitHub Actions minutes used
- **Performance**: Every commit triggers a full CI suite
- **Notifications**: Configure notifications to avoid CI spam

## Future Enhancements

Consider adding:

- Path filters to skip CI for documentation-only changes
- Different CI configurations for different branch patterns
- Conditional jobs based on changed files
