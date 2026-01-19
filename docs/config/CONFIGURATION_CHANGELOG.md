# Configuration Change Evidence Ledger

This document tracks all configuration changes with rationale and approval, aligned with Blueprint 2025 Final Section 4.6 (Evidence Ledger - Decision Record).

## Format

Each entry follows this structure:

| Field | Description |
|-------|-------------|
| Date | YYYY-MM-DD format |
| Variable(s) | Environment variable name(s) affected |
| Change Type | Added, Modified, Deprecated, Removed |
| Old Value | Previous default value (if applicable) |
| New Value | New default value (if applicable) |
| Rationale | Why this change was made |
| Approver | GitHub username of approver |
| Related Issue/PR | Links to related GitHub issues and PRs |

---

## 2026-01

### 2026-01-19: SMTP, CLOUD_ENV, and Referral Configuration

| Field | Value |
|-------|-------|
| Date | 2026-01-19 |
| Variable(s) | `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `EMAIL_FROM`, `CLOUD_ENV`, `REFERRAL_MAX_USAGE`, `REFERRAL_DEFAULT_POINTS` |
| Change Type | Added |
| Old Value | N/A |
| New Value | See defaults below |
| Rationale | Add missing configuration definitions for email sending, cloud environment identification, and referral system |
| Approver | @RC918 |
| Related Issue/PR | #4187, #4189, #4190, #4191, PR #4258 |

**Default Values:**
- `SMTP_HOST`: "" (empty)
- `SMTP_PORT`: 587
- `SMTP_USER`: None (SecretStr)
- `SMTP_PASSWORD`: None (SecretStr)
- `EMAIL_FROM`: "" (empty)
- `CLOUD_ENV`: "development"
- `REFERRAL_MAX_USAGE`: 5
- `REFERRAL_DEFAULT_POINTS`: 100

---

### 2026-01-18: Deprecation Milestone Tracking System

| Field | Value |
|-------|-------|
| Date | 2026-01-18 |
| Variable(s) | `DEPRECATION_REGISTRY` (internal constant) |
| Change Type | Added |
| Old Value | N/A |
| New Value | Centralized registry with TypedDict |
| Rationale | Implement deprecation milestone tracking for tech debt management |
| Approver | @RC918 |
| Related Issue/PR | #4223, #4237, #4238, PR #4235, PR #4252 |

---

### 2026-01-18: Thread-Safe TokenService Singleton

| Field | Value |
|-------|-------|
| Date | 2026-01-18 |
| Variable(s) | N/A (code architecture change) |
| Change Type | Modified |
| Old Value | Non-thread-safe singleton |
| New Value | Thread-safe singleton with double-checked locking |
| Rationale | Fix potential race condition in multi-threaded environments |
| Approver | @RC918 |
| Related Issue/PR | #4233, PR #4250 |

---

### 2026-01-18: JWT Deprecation Warning

| Field | Value |
|-------|-------|
| Date | 2026-01-18 |
| Variable(s) | `JWT_EXPIRATION_MINUTES` |
| Change Type | Deprecated |
| Old Value | Active |
| New Value | Deprecated (use `ACCESS_TOKEN_EXPIRY_MINUTES`) |
| Rationale | Standardize JWT configuration naming |
| Approver | @RC918 |
| Related Issue/PR | #4219, PR #4221 |

**Removal Date:** 2026-06-30

---

### 2026-01-18: Centralized TokenService Abstraction

| Field | Value |
|-------|-------|
| Date | 2026-01-18 |
| Variable(s) | `JWT_ALGORITHM`, `JWT_SECRET_KEY` |
| Change Type | Modified |
| Old Value | Hardcoded in multiple files |
| New Value | Centralized in TokenService |
| Rationale | DRY refactoring for JWT operations |
| Approver | @RC918 |
| Related Issue/PR | #4220, PR #4224 |

---

### 2026-01-18: DB Pool and JWT Settings Migration

| Field | Value |
|-------|-------|
| Date | 2026-01-18 |
| Variable(s) | `DB_POOL_SIZE`, `DB_POOL_MAX`, `DB_POOL_RECYCLE`, `DB_POOL_PRE_PING`, `DB_POOL_TIMEOUT`, `JWT_ALGORITHM` |
| Change Type | Added |
| Old Value | Hardcoded values |
| New Value | Configurable via environment |
| Rationale | Migrate hardcoded settings to settings.py for centralized management |
| Approver | @RC918 |
| Related Issue/PR | P1.3-P1.5, PR #4216 |

**Default Values:**
- `DB_POOL_SIZE`: 5
- `DB_POOL_MAX`: 10
- `DB_POOL_RECYCLE`: 300
- `DB_POOL_PRE_PING`: true
- `DB_POOL_TIMEOUT`: 10
- `JWT_ALGORITHM`: "HS256"

---

### 2026-01-17: IaC Sync - Feature Flags and Numeric Settings

| Field | Value |
|-------|-------|
| Date | 2026-01-17 |
| Variable(s) | 29 feature flags + numeric settings |
| Change Type | Added to render.yaml |
| Old Value | Not in IaC |
| New Value | Synced to render.yaml |
| Rationale | Sync production IaC settings for consistency |
| Approver | @RC918 |
| Related Issue/PR | #4180, #4181, PR #4211 |

---

## How to Add New Entries

When making configuration changes:

1. Add a new entry at the top of the current month section
2. Fill in all required fields
3. Link to the related GitHub issue and PR
4. Get approval before merging

For PR template guidance, see `.github/PULL_REQUEST_TEMPLATE/config_change.md`.
