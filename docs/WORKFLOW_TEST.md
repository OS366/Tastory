# Workflow Test Document

## Purpose

This document was created as part of testing the Tastory branching workflow.

## Test Details

- **Branch**: `feature/test-workflow-validation`
- **Target**: `development` branch
- **Date**: June 2, 2025
- **Purpose**: Validate branch protection rules and PR workflow

## Workflow Steps Tested

### 1. Feature Branch Creation ✅

- Created from `development` branch
- Follows naming convention: `feature/test-workflow-validation`

### 2. Making Changes ✅

- Creating this test document
- Will commit with conventional commit message

### 3. Pull Request Process

- Will create PR to `development`
- Should require 1 reviewer (as per protection rules)
- Tests dismiss stale reviews feature

## Expected Outcomes

1. PR creation should succeed
2. Direct push to `development` should fail (except for admins)
3. PR should require 1 approval before merging
4. Stale reviews should be dismissed on new commits

## Additional Notes

This is a test file and can be removed after workflow validation is complete.
