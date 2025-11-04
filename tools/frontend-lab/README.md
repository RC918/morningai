# ⚠️ DEPRECATED: Frontend Lab (Archived)

> **🚨 DO NOT USE THIS DIRECTORY FOR NEW DEVELOPMENT 🚨**
> 
> This directory is **DEPRECATED** and kept for historical reference only.
> All scripts intentionally fail to prevent accidental usage.
> 
> **Use instead**: `handoff/20250928/40_App/frontend-dashboard/`

---

This directory contains the archived `frontend-dashboard-deploy` directory.

**Status**: ⛔ DEPRECATED - Consolidated into production frontend  
**Date Archived**: 2025-10-28  
**Related Issue**: #867  
**Related PR**: TBD

## Why Archived?

The `frontend-dashboard-deploy` directory was originally created for Storybook and Lighthouse CI testing. It has been fully consolidated into the production frontend at `handoff/20250928/40_App/frontend-dashboard/`.

## What Was Migrated?

- ✅ LHCI configuration (lighthouserc.json, lighthouserc.main.json)
- ✅ LHCI puppeteer auth script (lhci-puppeteer-auth.js)
- ✅ Storybook configuration (.storybook/)
- ✅ All CI workflows (lhci.yml, storybook-deploy.yml, frontend.yml)
- ✅ All LHCI scripts (make-lhci-pr-comment.js, update-baseline-and-trend.js)
- ✅ Package manager standardization (pnpm@9.15.1)

Note: make-lhci-cookie.js was removed in PR #917 as it was unused.

## Migration Details

See `docs/TECHNICAL_DEBT_ROADMAP.md` Issue #2 for full migration details.

## Do Not Use

This directory is kept for historical reference only. All future development should use:
- **Production Frontend**: `handoff/20250928/40_App/frontend-dashboard/`
- **Package Name**: `frontend-dashboard`
- **Storybook**: `pnpm --filter frontend-dashboard build-storybook`
- **LHCI**: Configured to use production frontend

