# Lint Configuration Recommendations

This document provides recommendations for improving dead code and unused imports detection in the MorningAI codebase.

## Current Configuration

The project uses `.flake8` for Python linting with the following key settings:

- **max-line-length**: 120
- **max-complexity**: 15
- **F401 ignored in `__init__.py`**: Allows re-exports without warnings
- **F403 ignored in `__init__.py`**: Allows wildcard imports for re-exports

## Recommendations

### 1. Add Unused Import Detection to CI

**Current Gap**: The `backend.yml` CI workflow runs tests but doesn't explicitly run flake8 lint checks.

**Recommendation**: Add a lint job to `backend.yml`:

```yaml
lint:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - name: Setup Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'
    - name: Install flake8
      run: pip install flake8
    - name: Run flake8
      run: flake8 handoff/20250928/40_App/api-backend/src
```

### 2. Consider Adding autoflake for Automatic Cleanup

**Tool**: [autoflake](https://github.com/PyCQA/autoflake)

**Purpose**: Automatically removes unused imports and unused variables.

**Installation**: `pip install autoflake`

**Usage**:
```bash
# Check for unused imports (dry-run)
autoflake --check --remove-all-unused-imports -r handoff/20250928/40_App/api-backend/src

# Auto-fix unused imports
autoflake --in-place --remove-all-unused-imports -r handoff/20250928/40_App/api-backend/src
```

**CI Integration**:
```yaml
- name: Check unused imports
  run: |
    pip install autoflake
    autoflake --check --remove-all-unused-imports -r handoff/20250928/40_App/api-backend/src
```

### 3. Consider Adding vulture for Dead Code Detection

**Tool**: [vulture](https://github.com/jendrikseipp/vulture)

**Purpose**: Finds unused code (functions, classes, variables) in Python programs.

**Installation**: `pip install vulture`

**Usage**:
```bash
# Scan for dead code
vulture handoff/20250928/40_App/api-backend/src --min-confidence 80
```

**Whitelist File**: Create `vulture_whitelist.py` for intentional unused code:
```python
# vulture_whitelist.py
# Flask route decorators are detected as unused
_.route  # unused attribute
_.before_request  # unused attribute
_.after_request  # unused attribute
_.errorhandler  # unused attribute

# Blueprint registration functions called dynamically
init_phase456_routes  # unused function
init_phase7_routes  # unused function
init_dashboard_reports_routes  # unused function
init_health_static_routes  # unused function
```

**CI Integration** (optional, as warning only):
```yaml
- name: Check dead code (warning only)
  continue-on-error: true
  run: |
    pip install vulture
    vulture handoff/20250928/40_App/api-backend/src --min-confidence 80
```

### 4. Consider Migrating to Ruff

**Tool**: [Ruff](https://github.com/astral-sh/ruff)

**Purpose**: An extremely fast Python linter that replaces flake8, isort, and more.

**Benefits**:
- 10-100x faster than flake8
- Includes unused import detection (F401)
- Includes unused variable detection (F841)
- Auto-fix capability
- Single tool replaces multiple linters

**Configuration** (`pyproject.toml` or `ruff.toml`):
```toml
[tool.ruff]
line-length = 120
target-version = "py312"

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # Pyflakes (includes F401 unused imports, F841 unused variables)
    "I",      # isort
    "B",      # flake8-bugbear
    "C4",     # flake8-comprehensions
    "UP",     # pyupgrade
]
ignore = [
    "E203",   # whitespace before ':'
    "E501",   # line too long (handled by formatter)
]

[tool.ruff.lint.per-file-ignores]
"__init__.py" = ["F401", "F403"]
"*/migrations/*.py" = ["E501"]
"*/tests/*.py" = ["E501"]
```

### 5. IDE Configuration (VS Code)

Add to `.vscode/settings.json`:
```json
{
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--config=.flake8"
  ],
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

## Implementation Priority

| Priority | Tool | Effort | Impact |
|----------|------|--------|--------|
| P1 | Add flake8 to CI | Low | High - catches unused imports in PRs |
| P2 | Add autoflake check | Low | Medium - automated cleanup |
| P3 | Migrate to Ruff | Medium | High - faster, more comprehensive |
| P4 | Add vulture | Medium | Medium - finds dead code |

## Related Issues

- Consider creating GitHub issues for each recommendation if approved
- Phase 1.7 cleanup removed `_register_inline_routes()` empty function - this type of dead code would be caught by vulture

## References

- [Flake8 Documentation](https://flake8.pycqa.org/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [autoflake GitHub](https://github.com/PyCQA/autoflake)
- [vulture GitHub](https://github.com/jendrikseipp/vulture)
