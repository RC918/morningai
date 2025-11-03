# Test Coverage Improvement Plan

**Status**: Active  
**Target**: Achieve >60% test coverage across all components  
**Timeline**: Q1 2026 (3 months)  
**Owner**: Engineering Team  
**Last Updated**: 2025-11-03

---

## Executive Summary

This document outlines a strategic plan to improve test coverage across the MorningAI platform from current baselines to >60% coverage. The plan focuses on incremental improvements, prioritizing critical paths and high-risk areas while establishing sustainable testing practices.

**Current State**:
- Backend API: 74% coverage (✅ Above target)
- Orchestrator: ~40% estimated coverage
- Frontend Dashboard: <10% estimated coverage
- Owner Console: <10% estimated coverage
- Shared UI: 0% coverage (no tests)

**Target State** (3 months):
- Backend API: Maintain 74%+ coverage
- Orchestrator: 60%+ coverage
- Frontend Dashboard: 60%+ coverage
- Owner Console: 60%+ coverage
- Shared UI: 60%+ coverage

---

## 1. Current State Analysis

### 1.1 Backend API (`handoff/20250928/40_App/api-backend`)

**Coverage**: 74% (enforced in CI via `--cov-fail-under=74`)

**Test Infrastructure**:
- Framework: pytest + pytest-cov + pytest-asyncio
- Test Files: 159 Python test files
- Configuration: `pytest.ini` at repo root
- CI Integration: `.github/workflows/backend.yml` runs tests with coverage
- Coverage Report: XML format uploaded as artifact

**Strengths**:
- ✅ Comprehensive test suite (30+ test files in `tests/` directory)
- ✅ Good fixture organization (`tests/fixtures/`)
- ✅ Integration tests (`tests/integration/`)
- ✅ Unit tests for middleware, services, routes
- ✅ CI enforcement of coverage baseline
- ✅ Coverage reports in GitHub Actions summary

**Test Categories**:
- Authentication & Authorization: `test_auth_*.py` (5 files)
- API Routes: `test_*_routes.py`, `test_dashboard*.py`
- Governance & Multi-tenancy: `test_governance_*.py` (4 files)
- Agent System: `test_agent_*.py` (4 files)
- E2E Integration: `test_e2e_integration.py`
- Infrastructure: `test_redis_*.py`, `test_db_writer.py`

**Gaps**:
- Some edge cases in error handling
- Limited performance/load testing
- Missing tests for some utility modules

### 1.2 Orchestrator (`orchestrator/`)

**Coverage**: ~40% estimated (no CI enforcement)

**Test Infrastructure**:
- Framework: pytest
- Test Files: 8 test files in `orchestrator/tests/`
- Configuration: Uses repo-root `pytest.ini`
- CI Integration: No dedicated coverage tracking

**Existing Tests**:
- `test_api_auth.py`: API authentication
- `test_api_endpoints.py`: API endpoints (20KB file, comprehensive)
- `test_api_rate_limiting.py`: Rate limiting
- `test_event_schema.py`: Event validation
- `test_hitl_gate.py`: Human-in-the-loop approval
- `test_redis_queue_mock.py`: Queue operations
- `test_router.py`: Task routing
- `test_task_schema.py`: Task validation

**Strengths**:
- ✅ Core API endpoints tested
- ✅ Authentication & rate limiting covered
- ✅ Schema validation tests

**Gaps**:
- ❌ No coverage tracking in CI
- ❌ Missing tests for worker processes
- ❌ Limited error path coverage
- ❌ No integration tests with real Redis
- ❌ Missing tests for deployment/health checks

### 1.3 Frontend Dashboard (`handoff/20250928/40_App/frontend-dashboard`)

**Coverage**: <10% estimated

**Test Infrastructure**:
- Framework: Vitest + @testing-library/react + @vitest/coverage-v8
- Test Files: 20 test files (mostly UI component tests)
- Configuration: Vitest config in package.json scripts
- CI Integration: No coverage enforcement

**Existing Tests**:
- Page Components: `LoginPage.test.tsx`, `SignupPage.test.tsx`, `LandingPage.test.tsx`
- UI Components: 17 Apple Design System component tests
- Accessibility: 4 a11y-specific tests (`.a11y.test.tsx`)
- Utilities: `i18n/config.test.js`

**Strengths**:
- ✅ Vitest + coverage-v8 installed
- ✅ Testing Library setup
- ✅ Accessibility testing with vitest-axe
- ✅ Storybook for component development

**Gaps**:
- ❌ No coverage tracking in CI
- ❌ Missing tests for business logic
- ❌ No API integration tests
- ❌ Missing tests for state management (Zustand stores)
- ❌ No tests for routing/navigation
- ❌ Limited form validation tests

### 1.4 Owner Console (`handoff/20250928/40_App/owner-console`)

**Coverage**: <10% estimated

**Test Infrastructure**:
- Framework: Vitest + @testing-library/react + @vitest/coverage-v8
- Test Files: 5 test files
- Configuration: Vitest config in package.json scripts
- CI Integration: No coverage enforcement

**Existing Tests**:
- Components: `MetricsDashboard.test.tsx`
- Pages: `TenantManagement.test.jsx`
- API Client: `api-client.test.ts`, `auth.test.ts`, `2fa-api.test.ts`

**Strengths**:
- ✅ Vitest + coverage-v8 installed (recently added in PR #1067)
- ✅ Testing Library setup
- ✅ API client tests exist

**Gaps**:
- ❌ No coverage tracking in CI
- ❌ Very limited test coverage (5 files total)
- ❌ Missing tests for most components
- ❌ No state management tests
- ❌ No routing tests
- ❌ Limited form/validation tests

### 1.5 Shared UI (`packages/shared-ui`)

**Coverage**: 0% (no tests exist)

**Test Infrastructure**:
- Framework: Vitest (configured in workspace)
- Test Files: 0
- CI Integration: Coverage baseline check exists but reports 0%

**Gaps**:
- ❌ No tests at all
- ❌ Design system components untested
- ❌ Accessibility untested
- ❌ No visual regression tests

---

## 2. Strategic Priorities

### Priority 1: Establish Frontend Coverage Baselines (Weeks 1-4)

**Goal**: Get frontend apps to 30% coverage with CI enforcement

**Rationale**: Frontend currently has minimal coverage and no CI enforcement. Establishing baselines will prevent regression.

**Actions**:
1. Add coverage tracking to CI for both frontend apps
2. Write tests for critical user flows:
   - Authentication (login, signup, 2FA)
   - Dashboard data fetching and display
   - Tenant management (owner console)
3. Test all API client functions
4. Test form validation logic
5. Set CI baseline at 30% with `--coverage.thresholds.lines=30`

**Success Metrics**:
- Frontend Dashboard: 30% coverage enforced in CI
- Owner Console: 30% coverage enforced in CI
- All critical user flows have test coverage
- CI fails on coverage regression

### Priority 2: Improve Orchestrator Coverage (Weeks 3-6)

**Goal**: Increase orchestrator coverage from ~40% to 60%

**Rationale**: Orchestrator is critical infrastructure with moderate coverage but no CI enforcement.

**Actions**:
1. Add coverage tracking to CI with 60% threshold
2. Write tests for:
   - Worker process lifecycle
   - Task queue operations (enqueue, dequeue, retry)
   - Error handling and recovery
   - Health check endpoints
   - Redis connection handling
3. Add integration tests with real Redis (using Docker in CI)
4. Test deployment scenarios

**Success Metrics**:
- Orchestrator: 60% coverage enforced in CI
- All worker processes tested
- Integration tests with Redis passing

### Priority 3: Expand Frontend Coverage (Weeks 5-8)

**Goal**: Increase frontend coverage from 30% to 60%

**Rationale**: Build on baseline to achieve target coverage.

**Actions**:
1. Test all Zustand stores (state management)
2. Test routing and navigation
3. Test error boundaries and error handling
4. Test data transformation utilities
5. Add integration tests for API interactions
6. Test i18n functionality
7. Increase CI threshold to 60%

**Success Metrics**:
- Frontend Dashboard: 60% coverage enforced in CI
- Owner Console: 60% coverage enforced in CI
- All state management tested
- All routes tested

### Priority 4: Shared UI Component Testing (Weeks 7-10)

**Goal**: Achieve 60% coverage for shared UI library

**Rationale**: Shared components are used across apps and need comprehensive testing.

**Actions**:
1. Set up Vitest for shared-ui package
2. Write unit tests for all components:
   - Render tests (basic smoke tests)
   - Props validation
   - Event handlers
   - Accessibility (using vitest-axe)
3. Add visual regression tests (Storybook + Playwright)
4. Test design tokens and theme system
5. Add coverage to CI with 60% threshold

**Success Metrics**:
- Shared UI: 60% coverage enforced in CI
- All components have basic tests
- Accessibility tests passing
- Visual regression tests in place

### Priority 5: Maintain Backend Coverage (Ongoing)

**Goal**: Maintain 74%+ coverage, improve to 80%

**Rationale**: Backend already meets target; focus on maintaining and incremental improvement.

**Actions**:
1. Continue enforcing 74% baseline in CI
2. Add tests for new features as they're developed
3. Gradually increase threshold to 80% over 3 months
4. Focus on edge cases and error paths

**Success Metrics**:
- Backend: 80% coverage by end of Q1 2026
- No coverage regressions
- All new code has tests

---

## 3. Implementation Roadmap

### Week 1-2: Foundation & Quick Wins
- [ ] Add Vitest coverage config for frontend-dashboard
- [ ] Add Vitest coverage config for owner-console
- [ ] Add coverage reporting to CI workflows
- [ ] Write tests for authentication flows (both frontends)
- [ ] Write tests for API client modules
- [ ] Set 30% baseline for frontends in CI

### Week 3-4: Critical Paths
- [ ] Test dashboard data fetching (frontend-dashboard)
- [ ] Test tenant management (owner-console)
- [ ] Test form validation across apps
- [ ] Add orchestrator coverage tracking to CI
- [ ] Write orchestrator worker tests

### Week 5-6: Orchestrator Deep Dive
- [ ] Test orchestrator task queue operations
- [ ] Add Redis integration tests
- [ ] Test error handling and recovery
- [ ] Test health check endpoints
- [ ] Increase orchestrator CI threshold to 60%

### Week 7-8: Frontend Expansion
- [ ] Test all Zustand stores
- [ ] Test routing and navigation
- [ ] Test error boundaries
- [ ] Add API integration tests
- [ ] Increase frontend CI thresholds to 50%

### Week 9-10: Shared UI
- [ ] Set up Vitest for shared-ui
- [ ] Write component unit tests
- [ ] Add accessibility tests
- [ ] Set up visual regression tests
- [ ] Add 60% CI threshold for shared-ui

### Week 11-12: Polish & Optimization
- [ ] Increase frontend thresholds to 60%
- [ ] Increase backend threshold to 80%
- [ ] Add performance tests
- [ ] Document testing best practices
- [ ] Team training on testing patterns

---

## 4. Technical Implementation Details

### 4.1 Frontend Coverage Configuration

**Vitest Config** (add to `vite.config.ts`):
```typescript
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: './src/test/setup.ts',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html', 'lcov'],
      exclude: [
        'node_modules/',
        'src/test/',
        '**/*.d.ts',
        '**/*.config.*',
        '**/mockData',
        'dist/'
      ],
      thresholds: {
        lines: 60,
        functions: 60,
        branches: 60,
        statements: 60
      }
    }
  }
})
```

**CI Workflow Update** (`.github/workflows/frontend.yml`):
```yaml
- name: Run tests with coverage
  run: |
    cd handoff/20250928/40_App/frontend-dashboard
    pnpm test:coverage
    
- name: Check coverage thresholds
  run: |
    cd handoff/20250928/40_App/frontend-dashboard
    pnpm vitest run --coverage --coverage.thresholds.lines=60
```

### 4.2 Orchestrator Coverage Configuration

**CI Workflow Update** (`.github/workflows/backend.yml`):
```yaml
- name: Run orchestrator tests with coverage
  env:
    REDIS_URL: redis://localhost:6379/0
  run: |
    cd orchestrator
    python -m pytest --cov=orchestrator --cov-report=term-missing --cov-report=xml --cov-fail-under=60 -v
```

### 4.3 Shared UI Coverage Configuration

**New Workflow** (`.github/workflows/shared-ui.yml`):
```yaml
name: shared-ui-tests
on:
  pull_request:
    paths:
      - 'packages/shared-ui/**'
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v2
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'pnpm'
      - run: pnpm install
      - name: Run tests with coverage
        run: |
          cd packages/shared-ui
          pnpm test:coverage
      - name: Check coverage thresholds
        run: |
          cd packages/shared-ui
          pnpm vitest run --coverage --coverage.thresholds.lines=60
```

---

## 5. Testing Best Practices

### 5.1 Test Organization

**Backend (Python)**:
```
tests/
├── unit/              # Unit tests (isolated, fast)
│   ├── services/
│   ├── middleware/
│   └── routes/
├── integration/       # Integration tests (with DB/Redis)
├── fixtures/          # Shared test fixtures
└── conftest.py        # Pytest configuration
```

**Frontend (TypeScript)**:
```
src/
├── components/
│   ├── Button.tsx
│   └── __tests__/
│       ├── Button.test.tsx
│       └── Button.a11y.test.tsx
├── lib/
│   ├── api.ts
│   └── __tests__/
│       └── api.test.ts
└── test/
    ├── setup.ts       # Test setup
    └── utils.tsx      # Test utilities
```

### 5.2 What to Test

**High Priority**:
- ✅ User-facing features (authentication, data display, forms)
- ✅ Business logic (calculations, validations, transformations)
- ✅ API integrations (request/response handling, error cases)
- ✅ State management (stores, reducers, actions)
- ✅ Error handling (error boundaries, fallbacks)
- ✅ Accessibility (keyboard navigation, screen readers)

**Medium Priority**:
- ⚠️ Utility functions (formatters, validators, helpers)
- ⚠️ Routing and navigation
- ⚠️ i18n translations
- ⚠️ Component props and variants

**Low Priority** (can skip):
- ❌ Third-party library wrappers (trust the library)
- ❌ Simple presentational components (if no logic)
- ❌ Configuration files
- ❌ Type definitions

### 5.3 Test Patterns

**Backend API Tests**:
```python
def test_user_login_success(client, test_user):
    """Test successful user login returns JWT token"""
    response = client.post('/api/auth/login', json={
        'email': test_user.email,
        'password': 'password123'
    })
    assert response.status_code == 200
    assert 'access_token' in response.json()
```

**Frontend Component Tests**:
```typescript
import { render, screen, userEvent } from '@testing-library/react'
import { LoginForm } from './LoginForm'

describe('LoginForm', () => {
  it('submits form with email and password', async () => {
    const onSubmit = vi.fn()
    render(<LoginForm onSubmit={onSubmit} />)
    
    await userEvent.type(screen.getByLabelText(/email/i), 'test@example.com')
    await userEvent.type(screen.getByLabelText(/password/i), 'password123')
    await userEvent.click(screen.getByRole('button', { name: /log in/i }))
    
    expect(onSubmit).toHaveBeenCalledWith({
      email: 'test@example.com',
      password: 'password123'
    })
  })
})
```

**API Client Tests**:
```typescript
import { vi } from 'vitest'
import { apiClient } from './api-client'

describe('apiClient', () => {
  it('fetches user data', async () => {
    global.fetch = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ id: 1, name: 'Test User' })
    })
    
    const user = await apiClient.getUser(1)
    
    expect(user).toEqual({ id: 1, name: 'Test User' })
    expect(fetch).toHaveBeenCalledWith('/api/users/1')
  })
})
```

---

## 6. Success Metrics & Monitoring

### 6.1 Coverage Metrics

**Track in CI**:
- Line coverage %
- Branch coverage %
- Function coverage %
- Statement coverage %

**Dashboards**:
- GitHub Actions summary (already implemented for backend)
- Coverage trend over time
- Per-component coverage breakdown

### 6.2 Quality Metrics

**Track**:
- Test execution time (keep under 5 minutes for unit tests)
- Test flakiness rate (target: <1%)
- Number of tests (track growth)
- Code-to-test ratio (target: 1:1 or better)

### 6.3 Process Metrics

**Track**:
- PRs blocked by coverage failures
- Time to fix coverage failures
- Coverage improvement velocity (% per week)

---

## 7. Risks & Mitigation

### Risk 1: Testing Slows Down Development

**Mitigation**:
- Focus on high-value tests first
- Use test generators and templates
- Provide clear testing guidelines
- Invest in fast test infrastructure

### Risk 2: Flaky Tests

**Mitigation**:
- Use deterministic test data
- Mock external dependencies
- Avoid time-based assertions
- Retry flaky tests in CI (max 2 retries)

### Risk 3: Coverage Without Quality

**Mitigation**:
- Code review for test quality
- Require meaningful assertions
- Test behavior, not implementation
- Use mutation testing to verify test effectiveness

### Risk 4: Maintenance Burden

**Mitigation**:
- Keep tests simple and focused
- Use shared fixtures and utilities
- Refactor tests alongside code
- Delete obsolete tests promptly

---

## 8. Resources & Training

### 8.1 Documentation

- [ ] Create testing style guide
- [ ] Document common patterns
- [ ] Provide test templates
- [ ] Create troubleshooting guide

### 8.2 Tools

**Backend**:
- pytest: https://docs.pytest.org/
- pytest-cov: https://pytest-cov.readthedocs.io/
- pytest-asyncio: https://pytest-asyncio.readthedocs.io/

**Frontend**:
- Vitest: https://vitest.dev/
- Testing Library: https://testing-library.com/
- vitest-axe: https://github.com/chaance/vitest-axe

### 8.3 Training

- [ ] Team workshop on testing best practices
- [ ] Pair programming sessions
- [ ] Code review focus on tests
- [ ] Share testing wins in team meetings

---

## 9. Appendix

### 9.1 Current Test File Inventory

**Backend API**: 159 Python test files
**Orchestrator**: 8 Python test files
**Frontend Dashboard**: 20 TypeScript test files
**Owner Console**: 5 TypeScript test files
**Shared UI**: 0 test files

**Total**: 192 test files

### 9.2 CI Configuration Files

- `.github/workflows/backend.yml`: Backend tests with 74% coverage enforcement
- `.github/workflows/design-system-audit.yml`: Shared UI coverage (currently 0%)
- `pytest.ini`: Python test configuration
- `package.json` (frontend apps): Vitest scripts

### 9.3 Related Issues

- Issue #1059: Test Coverage Improvement Plan (this document)
- PR #1067: Install @vitest/coverage-v8 for owner-console

---

## 10. Approval & Sign-off

**Prepared by**: Engineering Team  
**Review Date**: 2025-11-03  
**Approved by**: _Pending_  
**Next Review**: 2025-12-03 (monthly review)

**Stakeholders**:
- Engineering Team: Implementation
- CTO: Strategic oversight
- QA Team: Test quality review
