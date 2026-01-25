# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **D-4 CI Failure Auto-Fix Enhancement** (PRs #4321, #4323, #4327, #4331, #4332)
  - **Date**: 2026-01-25
  - **Tag**: `v9.5.0-d4-ci-autofix-stable`
  - **Changes**:
    - Added `LintErrorParser` class supporting ruff, flake8, eslint, pylint output parsing (#4332)
    - Added `get_check_run_logs` function for direct CI log fetching from failed check_runs (#4327)
    - Added fallback mechanism for check_run name matching when webhook name differs (#4331)
    - Added `AUTO_FIX_ENABLED` environment variable check in CI failure path (#4323)
    - Fixed CI signature deduplication to properly set `loop_protection_triggered` (#4321)
    - Fixed LLM Reviewer type check for `response.usage` (#4312)
  - **Verified**: D-4 successfully auto-fixed lint error (F401 unused import) on PR #4330
  - **Blueprint Alignment**: Section 3.3 (Agent Catalog V2 - Coder Family), D-4 Self-Correction Loop

### Changed
- **EPIC I Encapsulation Improvements** (PR #4009, Issues #3958, #3961)
  - **Date**: 2026-01-15
  - **Tag**: `week3-pr3-epic-i-encapsulation`
  - **Changes**:
    - Added `_extract_task_type()` helper method to `CapabilityScoreManager` with robust validation
    - Handles edge cases: empty task_id, missing underscore, malformed formats
    - Added `set_provider_state()` public method to `DegradationAdvisor` for controlled state updates
    - Updated `RoutingPolicyEvolver._apply_to_routing_engine()` to use public method instead of direct private attribute access
    - Added structured logging fields for better log parsing and monitoring
  - **Blueprint Alignment**: Section 4.4 (Autonomous Provisioning v2), EPIC I Phase I-3/I-4

### Removed
- **Simple Mode Orchestrator Deprecated** (Issue #2651, PR #2767)
  - **Date**: 2025-12-15
  - **Reason**: LangGraph reached 100% rollout on 2025-12-14
  - **Impact**: All orchestrator tasks now use LangGraph exclusively
  - **Code Removed**:
    - `record_simple_task` method from `RolloutTracker` class
    - Related unit tests and integration tests for Simple Mode
    - Canary verification sections from `POST_DEPLOY_SMOKE_TEST_CHECKLIST.md`
  - **CI Guard Added**: `simple-mode-guard.yml` workflow prevents reintroduction of deprecated symbols
  - **Reference**: [ADR-005: Deprecate Simple Orchestrator Mode](docs/adr/005-deprecate-simple-orchestrator-mode.md)

### Changed
- **Documentation Migration (Epic #2374 Phase 3)** - Major reorganization of root directory documentation
  - **PR #2584 (PR6)**: Moved 13 CTO reports from root to `docs/reports/cto/`
  - **PR #2587 (PR7)**: Moved 116 reports from root to structured `docs/reports/` hierarchy
    - Coverage reports → `docs/reports/coverage/` (13 files)
    - Analysis reports → `docs/reports/analysis/` (17 files)
    - Security reports → `docs/reports/security/` (9 files)
    - Operations reports → `docs/reports/ops/` (5 files)
    - Phase reports → `docs/reports/phase/` (21 files)
    - PR review reports → `docs/reports/pr-reviews/` (13 files)
    - UI/UX reports → `docs/reports/uiux/` (8 files)
    - Validation reports → `docs/reports/validation/` (9 files)
    - Infrastructure reports → `docs/reports/infrastructure/` (3 files)
    - Calibration reports → `docs/reports/calibration/` (3 files)
    - Planning documents → `docs/reports/planning/` (7 files)
    - Guides → `docs/guides/` (4 files)
    - Runbooks → `docs/runbooks/` (2 files)
    - Release notes → `docs/releases/` (2 files)
  - **Path Mapping**: See `docs/migration/PR7_PATH_MAPPING.csv` for complete old-to-new path mapping
  - **Backward Compatibility**: Stub files created for key CTO documents (removal date: 2026-03-16)
  - **Impact**: External links to root-level report files will break; update references to new paths
- **Phase 1 main.py Refactoring Complete** (PR #2447-#2500)
  - **Phase 1.6: Route Modularization** - Moved all inline routes from main.py to dedicated blueprint modules:
    - PR1.6a: Phase 4-6 routes → `src/routes/phase456.py` (20+ endpoints)
    - PR1.6b: Phase 7 routes → `src/routes/phase7.py` (~15 endpoints)
    - PR1.6c: Dashboard/Reports/Settings routes → `src/routes/dashboard_reports.py` (~10 endpoints)
    - PR1.6d: Health/Static routes → `src/routes/health_static.py` (health checks + SPA fallback)
  - **Phase 1.7: Cleanup** - Removed empty `_register_inline_routes()` function and unused Flask imports
  - **Result**: main.py reduced from 1677 to 398 lines (-76%)
  - **Security Fix**: Path traversal vulnerability in static file serving fixed using `werkzeug.utils.safe_join`
  - **Documentation**: Route modularization documented in `docs/PHASE1_MAIN_PY_REFACTORING_PLAN.md`
  - **Test Coverage**: 184 routes baseline maintained, 28+ contract tests added

### Added
- **Python Scripts CI Workflow** - Comprehensive CI checks for Python scripts to prevent syntax errors
  - `python-scripts-ci.yml`: New workflow with 3 jobs (syntax-check, monitor-tests, integration-check)
  - **Syntax Validation**: Compiles monitor-related Python scripts using `python -m py_compile`
    - Scoped to: `monitor_orchestrator.py`, `repo_root_utils.py`, `test_monitor_graceful_degradation.py`
    - TODO: Expand to all scripts after fixing legacy syntax errors (e.g., `kg_cost_report.py:54`)
  - **Monitor Tests**: Runs `test_monitor_graceful_degradation.py` in CI environment
  - **Integration Check**: Dry-run verification that monitor script executes without syntax errors
  - **GitHub Step Summary**: Clear, actionable summaries for all check results
  - Prevents future syntax errors like the f-string backslash issue (PR #1261)
  - Runs on: PRs, pushes to main, and manual trigger (workflow_dispatch)
  - Related: PR #1261 hotfix, PR #1258 monitor improvements

### Fixed
- **Monitor Orchestrator Workflow** (PR #1258)
  - Fixed Pydantic alias for `SLACK_WEBHOOK_URL` to allow loading from environment variables
  - Added `repr=False` to prevent accidental logging of webhook URL in settings repr
  - **Behavior Change**: Monitor now gracefully degrades when Slack webhook not configured
    - Old behavior: `sys.exit(1)` if `SLACK_WEBHOOK_URL` missing
    - New behavior: Continues with health checks, prints alerts to console
    - Rationale: Allows GitHub Actions workflows to succeed in CI/CD environments without Slack
    - Production: Recommended to configure `SLACK_WEBHOOK_URL` for real-time alerts

- **Reputation Engine Path Resolution** (PR #1258)
  - Fixed `policies.yaml` path resolution with robust fallback chain
  - Changed from 4 levels up (incorrect) to 5 levels up (correct) to reach repo root
  - Added support for `POLICIES_PATH` environment variable override
  - Added multiple candidate paths for different execution environments:
    - Priority 1: `POLICIES_PATH` env var (explicit override)
    - Priority 2: Repo root resolution (5 levels up from governance/)
    - Priority 3: Current working directory
    - Priority 4: Backward compatibility (4 levels up)
    - Priority 5: Legacy relative path fallback
  - Fixes GitHub Actions workflow failures in reputation-update workflow

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
