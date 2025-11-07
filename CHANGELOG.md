# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **2FA Pre-Authentication Flow Security Enhancements** (PR #1149)
  - Atomic token consumption using Redis WATCH/MULTI to prevent race conditions
  - Production JWT secret validation with fail-fast startup check
  - New error codes: `TMP_TOKEN_CONSUMED` (401), `SCOPE_MISSING` (401)
  - Comprehensive concurrency tests for atomic operations
  - **BREAKING**: Production environments must set `JWT_SECRET_KEY` to a secure value
    - Application will fail to start if default test key is used in production
    - Set `ENVIRONMENT=production` and `JWT_SECRET_KEY=<secure-key>` before deployment
  - See: [Auth V2 API Reference](handoff/20250928/40_App/api-backend/docs/AUTH_V2_API_REFERENCE.md)

- **Monitoring Dashboard v2** (PR #1114, PR #1118)
  - Real-time monitoring dashboard with intelligent degradation handling
  - Primary endpoint: `/api/phase7/monitoring/dashboard` (public, no auth)
  - Legacy endpoint: `/api/dashboard/data` (deprecated)
  - Graceful degradation semantics:
    - Redis failure → 200 OK with fallback metrics (`available: false`, `source: 'fallback'`)
    - DB failure → 200 OK with degraded status + critical alert
    - Both failures → 503 Service Unavailable with `ServiceUnavailableError`
  - OpenAPI schema: `ServiceUnavailableError` with optional `request_id` field
  - DB health check test seam (`check_db_health()`) for reliable testing
  - Integration tests: `test_dashboard_503_integration.py`
  - TypeScript types with `@deprecated` markers for legacy endpoint
  - Comprehensive documentation in ONBOARDING_GUIDE.md, ENVIRONMENTS.md, PROJECT_STRUCTURE_REPORT.md
  - Troubleshooting guide: `docs/deployment/troubleshooting-monitoring.md`

### Changed
- **2FA Error Code Standardization** (PR #1149)
  - `SCOPE_MISSING` error changed from 500 to 401 Unauthorized
  - `SCOPE_MISMATCH` remains 403 Forbidden (scope present but wrong)
  - Improves API consistency and client error handling

- **OpenAPI Authentication Alignment** (PR #1118)
  - Removed `bearerAuth` security requirement from monitoring endpoints
  - Both `/api/dashboard/data` and `/api/phase7/monitoring/dashboard` are now correctly documented as public endpoints
  - Matches actual implementation (no `@jwt_required` decorator)

### Deprecated
- **Legacy Dashboard Endpoint** (PR #1118)
  - `/api/dashboard/data` is deprecated in favor of `/api/phase7/monitoring/dashboard`
  - TypeScript types include `@deprecated` JSDoc markers with migration guidance
  - Deprecation timeline: TBD (tracked in future release notes)

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
   # Required for production: Set secure JWT secret for 2FA tokens
   export ENVIRONMENT=production
   export JWT_SECRET_KEY="<generate-secure-random-key>"
   # Optional: Set custom orchestrator path
   export ORCHESTRATOR_PATH="/path/to/orchestrator"
   ```

   **Generate secure JWT secret:**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Run Deployment Verification**:
   ```bash
   python scripts/verify_deployment.py
   ```

3. **Verify 2FA Configuration** (PR #1149):
   ```bash
   # Test staging environment with concurrent requests
   cd handoff/20250928/40_App/api-backend
   python scripts/test_staging_concurrent_consumption.py
   ```

4. **Monitor After Deployment**:
   - Check Sentry for reduction in errors (expected: ~35 fewer errors)
   - Monitor health endpoint: `/healthz`
   - Verify Redis connectivity in logs
   - **NEW**: Monitor 2FA flow metrics:
     - `TMP_TOKEN_CONSUMED` error rate (should be near zero)
     - JWT secret validation on startup (check logs for ✅ success message)
     - 2FA enrollment and challenge success rates
     - Redis WATCH/MULTI operation latency

### Rollback Plan

If issues occur after deployment:

1. Check environment variables are correctly set
2. Verify orchestrator path exists
3. If errors persist, rollback to previous version
4. Review Sentry logs for specific error messages

## [Previous Versions]

See git history for changes in previous versions.
