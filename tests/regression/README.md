# Regression Tests

This directory contains auto-generated regression tests from the H-2 Regression Pipeline (Blueprint Section 5.4).

## Purpose

Regression tests are automatically generated when:
1. Production errors are captured by the Diagnostic Agent
2. CI failures are analyzed and root causes identified
3. Simulation failures reveal edge cases

## CI Enforcement (H-4)

The H-4 CI Enforcement workflow ensures:

1. **PR Blocking**: PRs that fail regression tests are blocked from merging
2. **Protected Tests**: Tests with `REGRESSION_METADATA` marker cannot be deleted without Safety Governor override
3. **Modification Approval**: Modifying protected tests requires explicit reviewer approval
4. **Bypass Mechanism**: Add `skip-regression` label for emergency fixes (requires justification)

## File Structure

```
tests/regression/
├── __init__.py
├── README.md
└── test_*.py          # Auto-generated regression tests
```

## Test Markers

Protected regression tests contain a `REGRESSION_METADATA` dictionary:

```python
REGRESSION_METADATA = {
    "candidate_id": "abc12345",
    "error_type": "TypeError",
    "priority": "p0",
    "source": "ci_failure",
    "generated_at": "2026-01-18T00:00:00Z",
    "protected": True,
}
```

## Adding Tests Manually

While tests are typically auto-generated, you can add manual regression tests:

1. Create a test file: `test_regression_<description>.py`
2. Include the `REGRESSION_METADATA` marker if you want protection
3. Document the original error and reproduction steps

## Bypassing Regression Tests

For emergency fixes only:

1. Add the `skip-regression` label to your PR
2. Document the justification in the PR description
3. Get explicit reviewer approval
4. Remove the label after the emergency is resolved

## Related

- Blueprint Section 5.4: Regression Pipeline v1
- EPIC H Roadmap: H-2 (Pipeline), H-4 (CI Enforcement)
- `.github/workflows/regression-tests.yml`: CI workflow
- `scripts/ci/check_protected_tests.py`: Protection checker
