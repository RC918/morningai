# Bundle Size Script Testing Documentation

This document explains the testing strategy, architecture, and maintenance guidelines for the bundle size measurement script (`scripts/measure-bundle-size.sh`).

## Architecture Overview

The bundle size measurement system uses a shared library pattern to ensure consistency between production code and tests:

```
scripts/
├── lib/
│   └── bundle-size-lib.sh      # Shared library (parse_vite_output, calculate_gzip_sizes_direct)
├── measure-bundle-size.sh       # Main script (sources lib/bundle-size-lib.sh)
└── tests/
    ├── measure-bundle-size.test.sh  # Unit tests (sources lib/bundle-size-lib.sh)
    └── BUNDLE_SIZE_TESTING.md       # This documentation
```

Both the main script and unit tests source the same `bundle-size-lib.sh` library, eliminating code duplication and ensuring that tests always validate the exact same functions used in production.

## What Is Tested

The unit tests focus on validating the **parsing logic, mathematical calculations, and fallback mechanisms** rather than end-to-end build processes.

### Test Coverage

The test suite covers the following areas:

**1. `calculate_gzip_sizes_direct()` function** validates the direct gzip calculation fallback that triggers when Vite output parsing fails or returns zero values. Tests include valid directories with JS/CSS files, missing directories, empty directories, no matching files, and multiple file scenarios.

**2. Zero-value detection regex** validates the pattern `^0?\.?0*$` that determines when to trigger the fallback mechanism. Tests cover various zero representations (`0`, `.0`, `0.0`) and confirm non-zero values (`1.5`, `0.1`) do not trigger fallback.

**3. `parse_vite_output()` function** validates parsing of Vite build output to extract gzip sizes. Tests cover single file parsing, multiple files, CSS files, missing gzip info, empty output, and mixed content with build logs.

**4. bc/awk fallback** validates that mathematical calculations work correctly when `bc` is unavailable and the script falls back to `awk`.

**5. Fallback trigger conditions** validates the integration logic that determines when to use direct gzip calculation instead of Vite output parsing.

## What Is NOT Tested

The unit tests intentionally do not cover certain areas:

**End-to-end build process**: Tests do not run actual `pnpm build` commands or validate real bundler output. This would be slow, flaky, and dependent on the full project setup.

**Actual bundle sizes**: Tests use synthetic fixtures rather than real application bundles. The goal is to validate parsing and calculation logic, not specific size values.

**CI workflow execution**: The workflow file (`.github/workflows/bundle-size-script-tests.yml`) is not tested directly. The unit tests validate the script logic that the workflow executes.

**Network operations**: Any operations that depend on external services or network connectivity are not covered.

## CI vs Local Environment Differences

When running tests in CI versus locally, several environmental factors can cause subtle differences:

### gzip Implementations

Different systems may have different gzip implementations (GNU gzip, BSD gzip, busybox gzip). While the core compression algorithm is the same, there can be minor differences in output size due to compression level defaults or header handling. Tests use **approximate ranges** rather than exact byte counts to accommodate these differences.

### Newline Handling

Line endings can differ between systems (LF vs CRLF). The test fixtures use explicit content creation to ensure consistent behavior, but edge cases may still arise when parsing real build output.

### `wc` Output Quirks

The `wc -c` command may include leading whitespace on some systems. The script handles this by using arithmetic expansion `$((value))` which strips whitespace.

### `find` Behavior

The `find` command with `-print0` is used for safe filename handling. While this is POSIX-compliant, some older or non-standard systems may behave differently. CI uses Ubuntu runners which have standard GNU find.

### `bc` / `awk` Availability

The script includes a fallback from `bc` to `awk` for mathematical calculations. CI environments typically have both available, but the bc-unavailable test job validates the awk fallback path.

**Note on bc output formatting**: The `bc` command may return `.1` instead of `0.1` for values less than 1. The shared library normalizes this using `sed 's/^\./0./'` to ensure consistent output format.

## Maintenance Contract

When modifying the bundle size measurement system, follow these guidelines:

### When Changing Fallback Logic

If you modify the fallback trigger conditions (the zero-value detection regex or the logic that decides when to use direct gzip calculation), update the corresponding tests in the "Fallback trigger conditions" test suite.

### When Changing Regex Patterns

If you modify the Vite output parsing regex or the zero-value detection regex, update the corresponding tests. The regex tests are designed to catch regressions in pattern matching.

### When Changing Vite Output Parsing

If you modify how `parse_vite_output()` extracts sizes from build output, update the parsing tests with new fixture data that reflects the expected format.

### When Adding New CLI Features

New command-line options or features should have tests for both the happy path (feature works correctly) and fallback path (feature degrades gracefully when dependencies are unavailable).

### When Modifying the Shared Library

Any changes to `scripts/lib/bundle-size-lib.sh` automatically affect both the main script and tests. Run the full test suite after any library changes:

```bash
bash scripts/tests/measure-bundle-size.test.sh
```

## Running Tests

### Local Execution

```bash
# Run all unit tests
bash scripts/tests/measure-bundle-size.test.sh

# Expected output: 22/22 tests passed
```

### CI Execution

The GitHub Actions workflow `.github/workflows/bundle-size-script-tests.yml` runs automatically on:
- Push to `main` branch
- Pull requests that modify relevant files
- Manual workflow dispatch

The CI workflow includes three jobs:

1. **unit-tests**: Runs the full test suite
2. **bc-unavailable-test**: Validates awk fallback when bc is not available
3. **script-syntax-check**: Validates bash syntax with `bash -n`

## Troubleshooting

### Test Failures Due to gzip Size Differences

If tests fail with messages about unexpected gzip sizes, check whether the test is using exact matching or range-based assertions. Prefer range-based assertions for gzip size comparisons.

### bc Not Found Errors

If you see "bc: command not found" errors locally, install bc or verify that the awk fallback is working correctly. The tests should pass with either bc or awk available.

### Library Sourcing Errors

If tests fail with "bundle-size-lib.sh: No such file or directory", ensure you're running tests from the repository root or that the `SCRIPT_DIR` variable is correctly resolving the library path.
