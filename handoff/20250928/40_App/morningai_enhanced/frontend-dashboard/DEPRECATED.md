# ⚠️ DEPRECATED

This directory (`morningai_enhanced/frontend-dashboard`) is **no longer in use** and has been deprecated.

## Active Frontend Directory

The active frontend codebase used by CI/CD and production is located at:
```
handoff/20250928/40_App/frontend-dashboard/
```

## Reason for Deprecation

- CI/CD workflows reference `frontend-dashboard` not `morningai_enhanced/frontend-dashboard`
- `render.yaml` deployment configuration does not use this directory
- ESLint configuration in this directory has parsing errors that do not affect the active codebase
- Keeping this directory may cause confusion for developers

## Action Required

This directory should be:
1. Archived or removed from the repository
2. Documented in project README to prevent future confusion

**Date Deprecated**: October 3, 2025
