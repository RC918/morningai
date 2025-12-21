# Supabase SQL Migrations Guide

This document describes the naming conventions and validation rules for SQL migration files in the `/migrations/` directory and auxiliary migration directories.

## Overview

MorningAI uses two migration systems:

1. **Supabase SQL Migrations** (this document): Raw SQL files in `/migrations/` for Supabase PostgreSQL schema changes
2. **Alembic Migrations**: Python-based migrations in `/handoff/.../api-backend/alembic/` for SQLAlchemy models (see [MIGRATIONS.md](./MIGRATIONS.md))

This guide covers the Supabase SQL migrations system.

## Directory Structure

```
morningai/
├── migrations/                      # Main Supabase migrations (STRICT validation)
│   ├── 001_initial_schema.sql
│   ├── 002_add_rls_policies.sql
│   └── ...
├── agents/
│   ├── dev_agent/migrations/        # Agent-specific migrations
│   ├── faq_agent/migrations/
│   └── ops_agent/migrations/
└── docs/database/migrations/        # Example/documentation migrations
```

## Naming Convention

All SQL migration files must follow this format:

```
NNN_lowercase_with_underscores.sql
```

Where:
- `NNN` is a 3-digit zero-padded number (001, 002, ..., 999)
- The description uses lowercase letters, numbers, and underscores only
- The file extension is `.sql`

### Valid Examples

```
001_initial_schema.sql
002_add_rls_policies.sql
015_create_agent_tasks_table.sql
039_rls_phase2_complete_tenant_isolation.sql
```

### Invalid Examples

```
1_initial_schema.sql          # Missing zero-padding
001-initial-schema.sql        # Hyphens not allowed
001_Initial_Schema.sql        # Uppercase not allowed
001_add rls policies.sql      # Spaces not allowed
initial_schema.sql            # Missing number prefix
```

## Validation Rules

The `scripts/validate_migrations.py` script enforces these rules:

### Main Directory (`migrations/`)

Full validation with strict rules:

| Check | Type | Description |
|-------|------|-------------|
| Duplicate Numbers | ERROR | No two files can have the same migration number |
| Contiguous Numbering | WARNING | Numbers should be sequential (001, 002, 003...) |
| Naming Format | WARNING | Must match `NNN_lowercase_with_underscores.sql` |

### Auxiliary Directories (`agents/*/migrations/`, `docs/database/migrations/`)

Lighter validation (no gap checks):

| Check | Type | Description |
|-------|------|-------------|
| Duplicate Numbers | ERROR | No two files can have the same number within the directory |
| Naming Format | WARNING | Must match `NNN_lowercase_with_underscores.sql` |

Note: Gap checks are not enforced for auxiliary directories because they may have independent numbering schemes.

### Rogue Migration Detection

Any SQL file matching the migration pattern (`NNN_*.sql`) found outside allowed directories will trigger an ERROR.

## Running Validation

```bash
# Standard validation (warnings don't fail)
python scripts/validate_migrations.py

# Strict mode (warnings treated as errors)
python scripts/validate_migrations.py --strict
```

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | All validations passed |
| 1 | Validation errors found |
| 2 | Validation warnings found (only with `--strict`) |

## CI Integration

The validation script runs automatically on PRs that modify migration files via `.github/workflows/migrations-consistency.yml`.

By default, the workflow uses **soft enforcement** (warnings don't block merge). This is intentional to allow flexibility while still surfacing potential issues.

To enable strict enforcement, modify the workflow to use `--strict` flag.

## Best Practices

1. **Always use the next sequential number** for new migrations in `migrations/`
2. **Never modify deployed migrations** - create a new migration to fix issues
3. **Use descriptive names** that explain what the migration does
4. **Test migrations locally** before committing
5. **Include rollback logic** where possible (though Supabase doesn't auto-rollback)

## Creating a New Migration

```bash
# Check the current highest migration number
ls migrations/*.sql | tail -1

# Create your new migration with the next number
# Example: if 038_xxx.sql is the latest, create 039_yyy.sql
touch migrations/039_your_migration_name.sql
```

## Related Documentation

- [MIGRATIONS.md](./MIGRATIONS.md) - Alembic migrations guide
- [DATABASE_INITIALIZATION.md](./DATABASE_INITIALIZATION.md) - Database setup guide
- [migrations/README.md](./migrations/README.md) - Example migrations documentation
