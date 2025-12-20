# Simple Mode Guard CI

## Overview

The Simple Mode Guard is a CI workflow that prevents reintroduction of deprecated Simple Mode code after LangGraph reached 100% rollout. It scans pull requests for forbidden symbols and blocks merging if violations are detected.

## Background

Simple Mode was the original orchestrator execution path that ran tasks without the full LangGraph workflow. After LangGraph reached 100% rollout (Issue #2651), Simple Mode code was removed to simplify the codebase. This guard prevents accidental reintroduction of that deprecated code.

## Forbidden Symbols

The guard detects the following symbols in added/modified Python files:

| Symbol | Type | Description |
|--------|------|-------------|
| `record_simple_task` | Method | Removed method for tracking Simple Mode tasks |
| `"Simple Mode"` | String | Deprecated terminology (case insensitive) |
| `USE_LANGGRAPH_PERCENT` | Env var | Obsolete environment variable for rollout control |
| `use_langgraph_percent` | Setting | Obsolete configuration setting |

## Scanned Directories

The guard only scans Python files in these directories:

- `handoff/20250928/40_App/orchestrator/**/*.py`
- `handoff/20250928/40_App/api-backend/**/*.py`
- `common/**/*.py`

Files outside these directories are not scanned.

## Exceptions

The following patterns are excluded from violation detection:

1. **NOTE comments**: Lines containing `NOTE:` or `# NOTE`
2. **TODO comments**: Lines containing `# TODO:`
3. **Removal comments**: Lines containing `#.*removed`
4. **Deprecation comments**: Lines containing `deprecated`

This allows documentation and comments explaining the removal to exist without triggering violations.

### Example Excluded Lines

```python
# NOTE: record_simple_task was removed in Issue #2651
# TODO: Remove this comment after 2026-01-15
# record_simple_task was deprecated after LangGraph rollout
```

## Resource Limits

To prevent resource exhaustion on large PRs:

| Limit | Value | Description |
|-------|-------|-------------|
| `MAX_FILES` | 100 | Maximum files to scan per PR |
| `MAX_LINES_PER_FILE` | 10,000 | Maximum added lines to scan per file |

If these limits are exceeded, the guard will log a warning and continue with the scanned portion.

## Running Locally

### Run the guard script directly

```bash
# Get base and head SHAs
BASE_SHA=$(git merge-base origin/main HEAD)
HEAD_SHA=$(git rev-parse HEAD)

# Run the guard
./scripts/ci/simple-mode-guard.sh "$BASE_SHA" "$HEAD_SHA"
```

### Run the test suite

```bash
./scripts/tests/simple-mode-guard.test.sh
```

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | No violations found |
| 1 | Violations detected |
| 2 | Invalid arguments |
| 3 | Git error |

## Workflow Behavior

### On Pull Request

1. Triggered when PR modifies files in scanned directories
2. Compares base SHA to head SHA
3. Extracts added lines from Python files
4. Checks for forbidden symbols
5. Posts comment on PR with results
6. Fails the check if violations found

### PR Comments

The workflow posts a comment on the PR with the scan results:

- **No violations**: Green status, confirms no deprecated symbols found
- **Violations detected**: Red status, lists violations and how to fix

Comments are updated (not duplicated) on subsequent runs.

## Troubleshooting

### False Positives

If the guard flags legitimate code:

1. Check if the code is in a comment explaining removal (should be excluded)
2. Verify the pattern matches the exclusion rules
3. If needed, add appropriate exclusion comment (e.g., `# NOTE: ...`)

### Guard Not Triggering

The guard only runs when:

1. PR targets `main` branch
2. PR modifies files in scanned directories
3. PR is not from a fork

### Debug Output

The workflow logs:

- Base and head SHAs being compared
- Number of files scanned
- Violations found (file and symbol)

Check the GitHub Actions logs for detailed output.

## Related Documentation

- [ADR-005: Deprecate Simple Orchestrator Mode](../adr/005-deprecate-simple-orchestrator-mode.md)
- [Issue #2651: Remove Simple Mode code after LangGraph 100% rollout](https://github.com/RC918/morningai/issues/2651)

## Maintenance

### Adding New Forbidden Symbols

Edit `scripts/ci/simple-mode-guard.sh`:

1. Add to `FORBIDDEN_SYMBOLS` array
2. Add check in `check_line_for_violations()` function
3. Update tests in `scripts/tests/simple-mode-guard.test.sh`
4. Update this documentation

### Removing the Guard

After sufficient time has passed (recommended: 6+ months after LangGraph 100% rollout):

1. Delete `.github/workflows/simple-mode-guard.yml`
2. Delete `scripts/ci/simple-mode-guard.sh`
3. Delete `scripts/tests/simple-mode-guard.test.sh`
4. Delete this documentation
5. Update ADR-005 to note guard removal
