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
2. **Error Counting**: Each package runs `tsc -p tsconfig.strict.json --noEmit` and counts `error TS` occurrences
3. **Regression Detection**: If current errors > baseline, the PR fails
4. **PR Comment**: A comment is added to PRs showing the current status

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

## Updating Baselines

Baselines should only be updated when:
1. **Errors are fixed**: After fixing strict mode errors, update the baseline to the new lower count
2. **Intentional increase**: In rare cases where new code legitimately increases errors (should be avoided)

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
      "error_count": 0,  // Update this number
      ...
    }
  }
}
```

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
