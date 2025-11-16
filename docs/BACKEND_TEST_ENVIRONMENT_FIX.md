# Backend Test Environment Fix

**Issue Date:** 2025-11-16  
**Status:** Documented (Fix Pending)  
**Priority:** P0 - BLOCKING

---

## Problem

Backend tests are failing due to wrong `jwt` package installed in virtual environment.

### Error Evidence

```
ModuleNotFoundError: No module named 'rq'
ModuleNotFoundError: No module named 'numpy'
RuntimeError: Wrong 'jwt' package detected! This project requires PyJWT, not jwt.
```

### Root Cause

The virtual environment has `jwt 1.4.0` installed instead of `PyJWT 2.8.0`.

**Verification:**
```bash
$ cd handoff/20250928/40_App/api-backend
$ source ../../../../.venv/bin/activate
$ pip list | grep jwt
jwt                1.4.0
```

**Expected:**
```bash
PyJWT              2.8.0
```

### Impact

- Cannot measure backend test coverage
- Cannot verify backend code quality
- Blocks AI agent development (needs reliable test suite)
- 28 test files fail to import

---

## Solution

### Step 1: Uninstall Wrong Package

```bash
cd /home/ubuntu/repos/morningai
source .venv/bin/activate
pip uninstall jwt -y
```

### Step 2: Install Correct Package

```bash
pip install PyJWT==2.8.0
```

### Step 3: Verify Installation

```bash
pip list | grep -i jwt
# Should show: PyJWT              2.8.0
```

### Step 4: Install Missing Dependencies

```bash
pip install rq numpy
```

### Step 5: Run Tests

```bash
cd handoff/20250928/40_App/api-backend
pytest --cov=src --cov-report=term-missing
```

### Step 6: Capture Coverage Baseline

```bash
pytest --cov=src --cov-report=json --cov-report=term-missing > coverage_baseline.txt
```

---

## Prevention

### Update requirements.txt

Ensure `requirements.txt` explicitly specifies `PyJWT` (not `jwt`):

```txt
# handoff/20250928/40_App/api-backend/requirements.txt
PyJWT==2.8.0  # ✅ Correct
# NOT: jwt==1.4.0  # ❌ Wrong package
```

### Add to CI

Add backend test coverage to CI workflow:

```yaml
# .github/workflows/backend-tests.yml
name: Backend Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install dependencies
        run: |
          cd handoff/20250928/40_App/api-backend
          pip install -r requirements.txt
      - name: Run tests with coverage
        run: |
          cd handoff/20250928/40_App/api-backend
          pytest --cov=src --cov-report=term-missing --cov-report=json
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./handoff/20250928/40_App/api-backend/coverage.json
```

---

## Timeline

- **Discovered:** 2025-11-16 10:15 UTC
- **Documented:** 2025-11-16 10:23 UTC
- **Fix ETA:** 1-2 days (requires venv rebuild)
- **Verification ETA:** 1-2 days (after fix)

---

## Related Documents

- [Strategic Roadmap Reality Comparison](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md) - Section "Critical Gaps Analysis"
- [CTO Strategic Plan](../CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) - Week 6 target: 50% coverage
- Backend requirements: `handoff/20250928/40_App/api-backend/requirements.txt:15`

---

## Owner

**Team:** Infrastructure  
**Assignee:** TBD  
**Reviewer:** TBD

---

**Document Version:** 1.0  
**Last Updated:** 2025-11-16
