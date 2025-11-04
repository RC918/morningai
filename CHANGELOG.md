# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- **[Frontend Dashboard]** Fixed critical layout compression issue where `max-w-3xl` utility compiled to `64px` instead of `768px`, causing entire page to be squeezed into a narrow vertical column
  - **Root Cause**: Misconfigured Tailwind v4 `@theme` block (duplicate blocks, wrong token names, incorrect placement)
  - **Solution**: Created `tailwind.config.js` with proper content paths including `@morningai/shared-ui`, removed duplicate `@theme` block, placed `@theme` before `@import "tailwindcss"`, used correct `--container-*` tokens
  - **Impact**: Affects all Tailwind v4 applications using shared-ui package
  - **See**: [Tailwind v4 Configuration Guide](docs/TAILWIND_V4_CONFIGURATION_GUIDE.md) | [PR #1034](https://github.com/RC918/morningai/pull/1034)
- Fixed Redis connection configuration to prevent localhost fallback in production
- Fixed orchestrator module import errors by adding configurable path resolution
- Fixed report generator datetime serialization to support timezone-aware datetime objects
- Made visualization libraries (pandas, scikit-learn, plotly) optional imports to reduce memory footprint

### Changed
- **BREAKING**: `agent.py` and `faq.py` now require `REDIS_URL` environment variable to be set
  - Previously these modules would fall back to `redis://localhost:6379/0` if `REDIS_URL` was not set
  - Now they will raise `RuntimeError` on startup if `REDIS_URL` is not configured
  - **Migration**: Ensure `REDIS_URL` is set in all deployment environments before deploying
  
- **BREAKING**: Orchestrator path configuration changed to use environment variable
  - New environment variable: `ORCHESTRATOR_PATH` (optional)
  - If not set, falls back to relative path `../../orchestrator` from `main.py`
  - **Migration**: Set `ORCHESTRATOR_PATH` in production if orchestrator is not at the default location

### Added
- **Alembic Database Migration Framework** (PR #1107)
  - Alembic 1.13.1 infrastructure setup
  - Baseline migration (revision: 91b9a61fcafa) capturing current schema
  - CI/CD integration with PostgreSQL and SQLite testing
  - Integration test for enum value validation (`scripts/test_migration_data_insertion.py`)
  - Migration helper script (`scripts/run_alembic_migrations.sh`)
  - Comprehensive documentation (`docs/database/MIGRATIONS.md`)
  - Enum policy: lowercase values with `values_callable` parameter
- **Orchestrator Consolidation Tracking** (Issue #1105)
  - GitHub issue tracking 2026 Q1 orchestrator consolidation
  - Based on ADR-001 "Option B: Unified Architecture"
  - Comprehensive task breakdown and acceptance criteria
- Added deployment verification script (`scripts/verify_deployment.py`) to check environment configuration
- Added comprehensive unit tests for production fixes (`tests/test_production_fixes.py`)
- Added logging for orchestrator path resolution
- Added graceful degradation for rate limiting when Redis is unavailable

### Security
- Removed hardcoded Redis connection fallbacks that could expose localhost services

## Migration Guide

### For Deployment to Production

1. **Set Required Environment Variables**:
   ```bash
   export REDIS_URL="redis://your-redis-host:6379/0"
   # Optional: Set custom orchestrator path
   export ORCHESTRATOR_PATH="/path/to/orchestrator"
   ```

2. **Run Deployment Verification**:
   ```bash
   python scripts/verify_deployment.py
   ```

3. **Monitor After Deployment**:
   - Check Sentry for reduction in errors (expected: ~35 fewer errors)
   - Monitor health endpoint: `/healthz`
   - Verify Redis connectivity in logs

### Rollback Plan

If issues occur after deployment:

1. Check environment variables are correctly set
2. Verify orchestrator path exists
3. If errors persist, rollback to previous version
4. Review Sentry logs for specific error messages

## [Previous Versions]

See git history for changes in previous versions.
