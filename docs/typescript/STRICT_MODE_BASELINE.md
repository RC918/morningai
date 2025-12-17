# TypeScript Strict Mode Baseline

This document explains the TypeScript strict mode baseline system used to prevent type debt accumulation.

## Overview

The project enforces TypeScript strict mode compliance through CI checks. Each package has a baseline error count, and PRs that increase the error count will fail CI.

## Current Baselines

Baselines are stored in `.strict-baseline.json` at the repository root:

| Package | Baseline | Path |
|---------|----------|------|
| frontend-dashboard | 0 | `handoff/20250928/40_App/frontend-dashboard` |
| owner-console | 0 | `handoff/20250928/40_App/owner-console` |
| shared-ui | 0 | `packages/shared-ui` |

## How It Works

1. **CI Check**: The `typecheck-strict` job in `.github/workflows/frontend.yml` runs on every PR
2. **Smoke Test**: CI validates script syntax and baseline file structure before running checks
3. **Error Counting**: Each package runs `tsc -p tsconfig.strict.json --noEmit` and counts `error TS` occurrences in `src/` files
4. **Regression Detection**: If current errors > baseline, the PR fails
5. **PR Comment**: A comment is added to PRs showing the current status

## Checking Locally

Run the helper script to check strict mode errors locally:

```bash
./scripts/count-strict-errors.sh
```

Example output:
```
TypeScript Strict Mode Error Count
===================================

frontend-dashboard  :   0 errors (baseline:   0) OK
owner-console       :   0 errors (baseline:   0) OK
shared-ui           :   0 errors (baseline:   0) OK

-----------------------------------
TOTAL               :   0 errors (baseline:   0)

All packages within baseline.
```

### Validate Baseline File

To validate the baseline file structure without running typechecks:

```bash
./scripts/count-strict-errors.sh --validate
```

This is useful for CI smoke testing and verifying the baseline file is correctly formatted.

## Updating Baselines

Baselines should only be updated when:
1. **Errors are fixed**: After fixing strict mode errors, update the baseline to the new lower count
2. **Intentional increase**: In rare cases where new code legitimately increases errors (should be avoided and requires justification)

### To Update Baselines

1. Run the script with `--update-baseline`:
   ```bash
   ./scripts/count-strict-errors.sh --update-baseline
   ```

2. Commit the updated `.strict-baseline.json`:
   ```bash
   git add .strict-baseline.json
   git commit -m "chore(typescript): update strict mode baseline"
   ```

3. The CI workflow will automatically use the new baselines

### Manual Update

You can also manually edit `.strict-baseline.json`:

```json
{
  "packages": {
    "frontend-dashboard": {
      "error_count": 0,
      "path": "handoff/20250928/40_App/frontend-dashboard",
      "tsconfig": "tsconfig.strict.json"
    }
  }
}
```

## Baseline Change Review Guidelines

The `.strict-baseline.json` file is protected by CODEOWNERS and requires review from @RC918.

### Baseline Decrease (Fixing Errors)

When fixing strict mode errors and decreasing the baseline:
- Include a summary of which errors were fixed in the PR description
- Run `./scripts/count-strict-errors.sh` locally to verify the new count
- Update baseline using `--update-baseline` flag

### Baseline Increase (Adding Errors)

Baseline increases should be rare and require explicit justification:
- **Must include** a detailed explanation in the PR description explaining why the increase is necessary
- **Common valid reasons**: Third-party library type issues, temporary workaround for urgent fix
- **Invalid reasons**: "Too hard to fix", "Will fix later" without a tracking issue
- Consider creating a tracking issue for the technical debt if increase is approved

## Edge Cases and Troubleshooting

### Missing Baseline File

If `.strict-baseline.json` is missing, CI will fail with an error:
```
ERROR: .strict-baseline.json not found! This file is required for TypeScript strict mode checks.
```

**Resolution**: Restore the file from `main` branch or create a new one:
```bash
git checkout main -- .strict-baseline.json
```

### Invalid JSON Structure

If the baseline file has invalid JSON or missing required fields:
```
ERROR: .strict-baseline.json is invalid or missing 'packages' key.
```

**Resolution**: Validate the file structure:
```bash
./scripts/count-strict-errors.sh --validate
```

### Adding a New Package

When adding a new TypeScript package to strict mode:

1. Create `tsconfig.strict.json` in the package directory:
   ```json
   {
     "extends": "./tsconfig.json",
     "compilerOptions": {
       "strict": true
     }
   }
   ```

2. Add `typecheck:strict` script to `package.json`:
   ```json
   {
     "scripts": {
       "typecheck:strict": "tsc -p tsconfig.strict.json --noEmit"
     }
   }
   ```

3. Add the package to `.strict-baseline.json`:
   ```json
   {
     "packages": {
       "new-package": {
         "error_count": 0,
         "path": "path/to/new-package",
         "tsconfig": "tsconfig.strict.json"
       }
     }
   }
   ```

4. Update the CI workflow in `.github/workflows/frontend.yml` to include the new package in the typecheck steps

5. Update this documentation to include the new package in the baselines table

### jq Not Found

The script requires `jq` for JSON parsing. If not installed:
```bash
# Ubuntu/Debian
sudo apt-get install jq

# macOS
brew install jq
```

### Path Does Not Exist

If a package path in the baseline file doesn't exist:
```
WARNING: Package 'package-name' path does not exist: path/to/package
```

This is a warning, not an error. The package will be skipped during counting. Update the path in `.strict-baseline.json` if the package was moved.

## Fixing Strict Mode Errors

Common strict mode errors and fixes:

### `noImplicitAny`
```typescript
// Before
function process(data) { ... }

// After
function process(data: DataType) { ... }
```

### `strictNullChecks`
```typescript
// Before
const value = obj.property.nested;

// After
const value = obj?.property?.nested;
// or
if (obj.property) {
  const value = obj.property.nested;
}
```

### `strictPropertyInitialization`
```typescript
// Before
class MyClass {
  property: string;
}

// After
class MyClass {
  property: string = '';
  // or
  property!: string; // if initialized elsewhere
}
```

## Related Issues

- Epic #2374: Technical Debt Optimization Plan
- Issue #2409: [TS-1] Build strict errors baseline
- Issue #2410: [TS-2] CI regression guard

## CI Workflow Reference

The strict mode check is defined in `.github/workflows/frontend.yml` under the `typecheck-strict` job.
