# GitHub Actions Permissions Guide

## Overview

GitHub Actions workflows require specific permissions to perform certain operations. This guide explains the permissions needed for various CI/CD tasks.

## Required Permissions

### Security Scanning with SARIF Upload

When using security scanning tools (like Trivy, CodeQL, etc.) that upload results in SARIF format:

```yaml
permissions:
  contents: read # Required to checkout code
  security-events: write # Required to upload SARIF results
  actions: read # Required for workflow information
```

### Common Permission Issues

1. **"Resource not accessible by integration"**

   - This error occurs when the GITHUB_TOKEN lacks required permissions
   - Solution: Add appropriate permissions to the workflow

2. **Code Scanning Not Available**
   - Some repositories (especially private ones) may not have code scanning enabled
   - Solution: Make SARIF upload optional with `continue-on-error: true`

## Workflow Configuration

### Global Permissions

Set permissions at the workflow level:

```yaml
name: CI

on:
  push:
  pull_request:

permissions:
  contents: read
  security-events: write
  actions: read
```

### Job-Level Permissions

For better isolation, set permissions per job:

```yaml
jobs:
  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write
    steps:
      # Your security scanning steps
```

## Best Practices

1. **Principle of Least Privilege**

   - Only grant permissions that are actually needed
   - Use job-level permissions when possible

2. **Handle Failures Gracefully**

   - Use `continue-on-error: true` for non-critical steps
   - Provide fallback behavior when permissions are insufficient

3. **Document Required Permissions**
   - Always comment why specific permissions are needed
   - Help future maintainers understand the requirements

## Example: Security Scan with Trivy

```yaml
security-scan:
  name: Security Scan
  runs-on: ubuntu-latest
  permissions:
    contents: read
    security-events: write
  continue-on-error: true
  steps:
    - uses: actions/checkout@v4

    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: "fs"
        format: "sarif"
        output: "trivy-results.sarif"

    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v4
      if: always()
      continue-on-error: true
      with:
        sarif_file: "trivy-results.sarif"
```

## Repository Settings

For full code scanning functionality:

1. Go to Settings → Security & analysis
2. Enable "Code scanning"
3. Configure alert settings as needed

## References

- [GitHub Actions Permissions](https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs)
- [SARIF Upload Documentation](https://docs.github.com/en/code-security/code-scanning/integrating-with-code-scanning/uploading-a-sarif-file-to-github)
- [Security Events Permission](https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs#defining-access-for-the-github_token-scopes)
