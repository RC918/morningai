# Common Test Utilities

This directory contains shared test utilities and configurations used across the MorningAI codebase (api-backend, orchestrator, and agents).

## Contents

- **`tests/lint_helpers.py`**: Reusable AST scanning functions for detecting deprecated module imports
- **`tests/test_config.py`**: Centralized configuration for deprecated module lists
- **`tests/test_lint_helpers.py`**: Unit tests for the lint helper functions

## Usage

### Running Tests Locally

To use the shared test utilities, you need to add the `common` directory to your `PYTHONPATH`:

```bash
# From the repository root
export PYTHONPATH=/path/to/morningai/common:$PYTHONPATH

# Then run tests as usual
cd handoff/20250928/40_App/api-backend
pytest tests/
```

### In CI

The `PYTHONPATH` is automatically configured in the GitHub Actions workflow (`.github/workflows/test-apps.yml`), so no additional setup is required.

### Importing Shared Utilities

```python
# In your test files
from common.tests.lint_helpers import (
    check_file_for_deprecated_imports,
    find_python_files,
    format_violations_message
)
from common.tests.test_config import (
    API_BACKEND_DEPRECATED_MODULES,
    PREAUTH_TOKEN_MIGRATION_GUIDE
)
```

## Architecture

### Lint Helpers

The `lint_helpers.py` module provides three main functions:

1. **`check_file_for_deprecated_imports(file_path, deprecated_modules)`**
   - Scans a Python file for deprecated module imports using AST parsing
   - Detects both direct and aliased imports
   - Skips relative imports (by design)
   - Returns list of violations: `[(line_no, import_stmt, deprecated_module), ...]`

2. **`find_python_files(root, include_pattern, exclude_patterns)`**
   - Finds Python files matching glob patterns
   - Supports exclusion patterns for tests, migrations, etc.
   - Returns list of matching file paths

3. **`format_violations_message(all_violations, root, migration_guide)`**
   - Formats violations into human-readable error messages
   - Includes optional migration guide
   - Returns formatted string for test assertions

### Test Configuration

The `test_config.py` module centralizes deprecated module lists:

- **`BASE_DEPRECATED_MODULES`**: Core deprecated modules (e.g., `utils.preauth_token`)
- **`API_BACKEND_DEPRECATED_MODULES`**: API backend specific deprecated modules
- **`ORCHESTRATOR_DEPRECATED_MODULES`**: Orchestrator specific deprecated modules
- **`AGENTS_DEPRECATED_MODULES`**: Agents specific deprecated modules
- **`PREAUTH_TOKEN_MIGRATION_GUIDE`**: Migration instructions for deprecated modules

## Known Limitations

- **Relative imports**: Skipped by design (e.g., `from .module import something`)
- **Dynamic imports**: Not detected (e.g., `importlib.import_module()`)
- **TYPE_CHECKING imports**: Currently flagged (may be refined in future)

## Development

### Running Unit Tests

```bash
# Set PYTHONPATH
export PYTHONPATH=/path/to/morningai/common:$PYTHONPATH

# Run unit tests for lint helpers
cd common/tests
pytest test_lint_helpers.py -v
```

### Adding New Deprecated Modules

1. Add the module to the appropriate list in `test_config.py`
2. Update the migration guide if needed
3. Run tests to verify detection works

## Expansion Plan

This shared infrastructure is part of a 5-phase plan to expand lint checks across the entire codebase:

- **Phase 1** (Current): Create shared infrastructure in `common/tests/`
- **Phase 2**: Extend to orchestrator
- **Phase 3**: Extend to dev_agent
- **Phase 4**: Extend to faq_agent and ops_agent
- **Phase 5**: Add CI enforcement and documentation

See `docs/lint_scanner_expansion_plan.md` for full details.

## Troubleshooting

### ImportError: No module named 'common'

**Problem**: Tests fail with `ImportError: No module named 'common'`

**Solution**: Set `PYTHONPATH` to include the `common` directory:
```bash
export PYTHONPATH=/path/to/morningai/common:$PYTHONPATH
```

### Tests pass locally but fail in CI

**Problem**: Tests work on your machine but fail in GitHub Actions

**Solution**: Verify that `.github/workflows/test-apps.yml` includes `${{ github.workspace }}/common` in the `PYTHONPATH` environment variable for the relevant test job.

## Contributing

When adding new shared test utilities:

1. Add the utility function to the appropriate module in `common/tests/`
2. Add comprehensive unit tests in `common/tests/test_*.py`
3. Update this README with usage examples
4. Ensure PYTHONPATH is documented for local development
