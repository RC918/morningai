# Configuration Optimization - GitHub Issues Template

This document contains pre-formatted GitHub Issues for the Configuration Optimization initiative.
Copy each issue to create them in your GitHub Project Board.

---

## Phase 1: IaC Single Source of Truth (P1)

### Issue 1.1: Sync production feature flags to render.yaml

**Title:** `[Config P1.1] Sync production feature flags to render.yaml`

**Labels:** `config-optimization`, `phase-1`, `iac`

**Body:**
```markdown
## Background

As part of the Configuration Optimization initiative (Phase 1: IaC Single Source of Truth), we need to sync the actual production feature flag values to render.yaml.

## Blueprint Alignment

Section 4.3 Model Governance Framework v2 - Single Source of Truth

## Problem

29 feature flags have different values between IaC defaults (render.yaml) and Dashboard actual settings. The IaC should reflect the actual production configuration.

## Tasks

- [ ] Update render.yaml with the following TRUE flags:
  - ENABLE_DYNAMIC_ROUTING: true
  - ENABLE_GITHUB_REVIEW_POSTING: true
  - ENABLE_MEMORY_CONSOLIDATION: true
  - ENABLE_MEMORY_V2: true
  - ENABLE_SELF_CRITIQUE: true
  - REFACTOR_AGENT_AUTO_PR: true
  - REGRESSION_PIPELINE_AUTO_GENERATE: true
  - REGRESSION_TEST_WRITE_TO_DISK: true
  - USE_DEBATE_ENGINE: true
  - USE_DEPENDENCY_ANALYSIS: true
  - USE_LLM_PLANNER: true
  - USE_LLM_REVIEWER: true
  - USE_MULTI_SPECIALIST_REVIEW: true
  - USE_POSTGRES_CHECKPOINTER: true
  - USE_REGRESSION_PIPELINE: true
  - USE_REVIEW_CONSOLIDATION: true
  - USE_SELF_REFINEMENT: true
  - USE_TEST_COVERAGE_FLAGGING: true
  - ENABLE_SIMPLE_CODER: true
  - ENABLE_REVIEW_FEEDBACK_LOOP: true
  - ENABLE_REVIEW_PATTERN_RETRIEVAL: true
  - DRIFT_RETRY_ENABLED: true
  - CROSS_PROVIDER_FALLBACK_ENABLED: true
  - RATE_LIMIT_FAIL_FAST: true

- [ ] Update render.yaml with the following FALSE flags:
  - ENABLE_FAILURE_LEARNING_CONTEXT: false
  - GITHUB_REVIEW_POSTING_DRY_RUN: false
  - PR_DEDUP_DRY_RUN: false
  - ROUTING_FORCE_TIER_FLOOR: false
  - RATE_LIMIT_BY_USER: false

- [ ] Document the rationale for each production value in comments

## Acceptance Criteria

- [ ] render.yaml reflects actual production configuration
- [ ] All changes are documented with rationale
- [ ] Deployment from IaC produces same configuration as current Dashboard
```

---

### Issue 1.2: Sync numeric settings to render.yaml

**Title:** `[Config P1.2] Sync numeric settings to render.yaml`

**Labels:** `config-optimization`, `phase-1`, `iac`

**Body:**
```markdown
## Background

Numeric configuration values in production differ from IaC defaults.

## Blueprint Alignment

Section 4.3 Model Governance Framework v2 - Single Source of Truth

## Tasks

- [ ] Update render.yaml with production numeric values:
  - GUNICORN_WORKERS: 2 (current default: 4)
  - RQ_MAX_JOBS: 50 (current default: 0)
  - DEGRADED_CHECKPOINT_MAX_PER_THREAD: 5 (current default: 10)
  - DEGRADED_CHECKPOINT_MEMORY_HARD_LIMIT_MB: 512 (current default: 1024)
  - RATE_LIMIT_REQUESTS: 100 (current default: 60)

- [ ] Update string settings:
  - LLM_PROVIDER: gemini (current default: auto)
  - ROUTING_ALLOWED_PROVIDERS: gemini,alicloud,openai (current default: '')
  - COOKIE_SAMESITE: None (current default: Lax)

## Acceptance Criteria

- [ ] All numeric settings match production values
- [ ] Changes documented with performance/security rationale
```

---

### Issue 1.3: Migrate hardcoded DB pool settings to settings.py

**Title:** `[Config P1.3] Migrate hardcoded DB pool settings to settings.py`

**Labels:** `config-optimization`, `phase-1`, `refactor`

**Body:**
```markdown
## Background

Database connection pool settings are hardcoded in `database.py` instead of being managed through the centralized settings.py configuration.

## Blueprint Alignment

Section 4.3 Model Governance Framework v2 - Centralized Configuration

## Current State

In `handoff/20250928/40_App/api-backend/src/extensions/database.py`:
```python
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_pre_ping": True,      # Should be DB_POOL_PRE_PING
    "pool_recycle": 300,        # Should be DB_POOL_RECYCLE (prod: 3600)
    "pool_size": 5,             # Should be DB_POOL_SIZE
    "max_overflow": 10,         # Should be DB_POOL_MAX_OVERFLOW (prod: 5)
    "pool_timeout": 10,
}
```

## Tasks

- [ ] Add Field definitions to `common/config/settings.py`:
  - `db_pool_size: int = Field(default=5, alias="DB_POOL_SIZE")`
  - `db_pool_max_overflow: int = Field(default=10, alias="DB_POOL_MAX_OVERFLOW")`
  - `db_pool_recycle: int = Field(default=300, alias="DB_POOL_RECYCLE")`
  - `db_pool_pre_ping: bool = Field(default=True, alias="DB_POOL_PRE_PING")`
  - `db_pool_timeout: int = Field(default=10, alias="DB_POOL_TIMEOUT")`

- [ ] Update `database.py` to use settings

- [ ] Add to `env.schema.yaml`

- [ ] Update render.yaml with production values

## Acceptance Criteria

- [ ] All DB pool settings configurable via environment variables
- [ ] No hardcoded values in database.py
- [ ] Production values documented in IaC
```

---

### Issue 1.4: Migrate JWT_ALGORITHM to settings.py

**Title:** `[Config P1.4] Migrate JWT_ALGORITHM to settings.py`

**Labels:** `config-optimization`, `phase-1`, `refactor`

**Body:**
```markdown
## Background

JWT_ALGORITHM is hardcoded in `auth_service.py` instead of being configurable.

## Current State

In `handoff/20250928/40_App/api-backend/src/services/auth_service.py`:
```python
JWT_ALGORITHM = 'HS256'
```

## Tasks

- [ ] Add Field definition to `common/config/settings.py`:
  - `jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")`

- [ ] Update `auth_service.py` to use settings

- [ ] Add to `env.schema.yaml`

## Acceptance Criteria

- [ ] JWT_ALGORITHM configurable via environment variable
- [ ] Default value remains HS256 for backward compatibility
```

---

### Issue 1.5: Unify JWT expiration naming

**Title:** `[Config P1.5] Unify JWT expiration naming (JWT_EXPIRATION_MINUTES)`

**Labels:** `config-optimization`, `phase-1`, `refactor`

**Body:**
```markdown
## Background

There's a naming inconsistency between prod.md (`JWT_EXPIRATION_MINUTES`) and settings.py (`ACCESS_TOKEN_EXPIRY_MINUTES`).

## Current State

- prod.md uses: `JWT_EXPIRATION_MINUTES=60`
- settings.py uses: `access_token_expiry_minutes` with alias `ACCESS_TOKEN_EXPIRY_MINUTES` (default: 15)

## Tasks

- [ ] Use Pydantic v2 `validation_alias=AliasChoices` to support both names:
  ```python
  from pydantic import AliasChoices
  access_token_expiry_minutes: int = Field(
      default=15,
      validation_alias=AliasChoices('ACCESS_TOKEN_EXPIRY_MINUTES', 'JWT_EXPIRATION_MINUTES'),
      description="JWT access token expiry time in minutes"
  )
  ```
- [ ] Document both names in env.schema.yaml with note that ACCESS_TOKEN_EXPIRY_MINUTES is canonical
- [ ] Update documentation to prefer ACCESS_TOKEN_EXPIRY_MINUTES as the canonical name

## Acceptance Criteria

- [ ] Both names work as environment variables
- [ ] Documentation clarifies ACCESS_TOKEN_EXPIRY_MINUTES as the canonical name
```

---

## Phase 2: Configuration Governance (P2)

### Issue 2.1: Create configuration validation script

**Title:** `[Config P2.1] Create configuration validation script`

**Labels:** `config-optimization`, `phase-2`, `tooling`

**Body:**
```markdown
## Background

Need automated validation to ensure prod.md values match env.schema.yaml definitions.

## Blueprint Alignment

Section 4.6 Evidence Ledger - Configuration Audit Trail

## Tasks

- [ ] Create `scripts/validate_config_coverage.py`:
  - Parse env.schema.yaml for all defined variables
  - Compare against prod.md values
  - Report missing definitions
  - Report type mismatches
  - Report value discrepancies

- [ ] Add to CI workflow

## Acceptance Criteria

- [ ] Script validates all 77 prod.md values
- [ ] CI fails if configuration drift detected
- [ ] Clear error messages for each issue type
```

---

### Issue 2.2: Implement configuration drift detection

**Title:** `[Config P2.2] Implement configuration drift detection`

**Labels:** `config-optimization`, `phase-2`, `governance`

**Body:**
```markdown
## Background

Need to detect when IaC defaults differ from actual production values.

## Blueprint Alignment

Section 4.3 Model Governance Framework v2 - Drift Monitoring

## Tasks

- [ ] Create GitHub Action workflow `.github/workflows/config-drift-check.yml`
- [ ] Compare render.yaml values against env.schema.yaml
- [ ] Generate drift report on PR
- [ ] Block merge if critical drift detected

## Acceptance Criteria

- [ ] Drift detection runs on every PR
- [ ] Clear report of all discrepancies
- [ ] Configurable severity levels
```

---

### Issue 2.3: Update env.schema.yaml with missing definitions

**Title:** `[Config P2.3] Update env.schema.yaml with missing definitions`

**Labels:** `config-optimization`, `phase-2`, `documentation`

**Body:**
```markdown
## Background

16 configuration values in prod.md are not defined in env.schema.yaml.

## Missing Definitions

1. SMTP_HOST
2. SMTP_PORT
3. SMTP_USER
4. SMTP_PASSWORD
5. EMAIL_FROM
6. REFERRAL_MAX_USAGE
7. REFERRAL_DEFAULT_POINTS
8. CLOUD_ENV
9. DB_POOL_SIZE (after P1.3)
10. DB_POOL_MAX_OVERFLOW (after P1.3)
11. DB_POOL_RECYCLE (after P1.3)
12. DB_POOL_PRE_PING (after P1.3)
13. DB_POOL_TIMEOUT (after P1.3)
14. JWT_ALGORITHM (after P1.4)

Note: AUTH_ENFORCE_OWNER_2FA is excluded from this list as 2FA-related configurations are deferred per user request (currently in development/testing phase).

## Tasks

- [ ] Add schema definitions for each missing variable
- [ ] Include type, default, description, security_level
- [ ] Mark sensitive values appropriately

## Acceptance Criteria

- [ ] All prod.md values have schema definitions
- [ ] Schema validates successfully
```

---

### Issue 2.4: Create configuration change Evidence Ledger

**Title:** `[Config P2.4] Create configuration change Evidence Ledger`

**Labels:** `config-optimization`, `phase-2`, `governance`

**Body:**
```markdown
## Background

Need to track configuration changes with rationale and approval.

## Blueprint Alignment

Section 4.6 Evidence Ledger - Decision Record

## Tasks

- [ ] Create `docs/config/CONFIGURATION_CHANGELOG.md`
- [ ] Document each configuration change with:
  - Date
  - Variable name
  - Old value → New value
  - Rationale
  - Approver
  - Related Issue/PR

- [ ] Add PR template for configuration changes

## Acceptance Criteria

- [ ] All configuration changes documented
- [ ] Audit trail is searchable
- [ ] PR template enforces documentation
```

---

## Phase 3: Feature Completion (P3)

### Issue 3.1: Implement SMTP configuration

**Title:** `[Config P3.1] Implement SMTP configuration in settings.py`

**Labels:** `config-optimization`, `phase-3`, `feature`

**Body:**
```markdown
## Background

SMTP settings are referenced in documentation but not implemented in settings.py.

## Tasks

- [ ] Add Field definitions to settings.py following the dual-field secret pattern (per docs/config/settings.md):
  - `smtp_host: str = Field(default="", alias="SMTP_HOST")`
  - `smtp_port: int = Field(default=587, alias="SMTP_PORT")`
  - `_smtp_user_secret: Optional[SecretStr] = Field(default=None, alias="SMTP_USER", repr=False)`
  - `_smtp_password_secret: Optional[SecretStr] = Field(default=None, alias="SMTP_PASSWORD", repr=False)`
  - `email_from: str = Field(default="", alias="EMAIL_FROM")`
  
- [ ] Add corresponding `@property` methods for smtp_user and smtp_password to unwrap SecretStr values

- [ ] Add to env.schema.yaml with security_level: sensitive

- [ ] Update email sending code to use settings

## Acceptance Criteria

- [ ] SMTP settings configurable via environment
- [ ] Sensitive values use dual-field SecretStr pattern (not exposed in logs)
- [ ] Email functionality works with new settings
```

---

### Issue 3.2: Implement CLOUD_ENV configuration

**Title:** `[Config P3.2] Implement CLOUD_ENV configuration`

**Labels:** `config-optimization`, `phase-3`, `feature`

**Body:**
```markdown
## Background

CLOUD_ENV is used in production but not defined in settings.py.

## Tasks

- [ ] Add Field definition with Literal type for type safety (similar to `environment` field):
  ```python
  from typing import Literal
  cloud_env: Literal["development", "staging", "production"] = Field(
      default="development",
      alias="CLOUD_ENV",
      description="Cloud environment identifier"
  )
  ```

- [ ] Add to env.schema.yaml

- [ ] Document usage and valid values

## Acceptance Criteria

- [ ] CLOUD_ENV configurable via environment
- [ ] Type validation enforces valid values: development, staging, production
```

---

### Issue 3.3: Implement Referral system configuration

**Title:** `[Config P3.3] Implement Referral system configuration`

**Labels:** `config-optimization`, `phase-3`, `feature`

**Body:**
```markdown
## Background

Referral system configuration values are in prod.md but not implemented.

## Tasks

- [ ] Add Field definitions:
  - `referral_max_usage: int = Field(default=5, alias="REFERRAL_MAX_USAGE")`
  - `referral_default_points: int = Field(default=100, alias="REFERRAL_DEFAULT_POINTS")`

- [ ] Add to env.schema.yaml

- [ ] Implement referral system feature (separate EPIC)

## Acceptance Criteria

- [ ] Configuration ready for referral system
- [ ] Feature implementation tracked separately
```

---

## Quick Reference: GitHub Project Board Setup

1. Go to https://github.com/RC918/morningai/projects
2. Create new Project Board: "Configuration Optimization"
3. Add columns: "Backlog", "Phase 1 (P1)", "Phase 2 (P2)", "Phase 3 (P3)", "Done"
4. Create issues from templates above
5. Add labels: `config-optimization`, `phase-1`, `phase-2`, `phase-3`
6. Assign to appropriate columns

## Priority Order

1. **P1.1** - Sync feature flags (highest impact)
2. **P1.2** - Sync numeric settings
3. **P1.3** - Migrate DB pool settings
4. **P1.4** - Migrate JWT_ALGORITHM
5. **P1.5** - Unify JWT naming
6. **P2.1** - Validation script
7. **P2.2** - Drift detection
8. **P2.3** - Schema updates
9. **P2.4** - Evidence Ledger
10. **P3.1** - SMTP config
11. **P3.2** - CLOUD_ENV
12. **P3.3** - Referral system
