# Parallel Development Strategy
**MorningAI MVP Development - Three Squad Coordination**

## 📋 Overview

This document outlines the strategy for parallel development across three squads working simultaneously on MVP features, Owner Console, and Platform improvements. The goal is to enable safe, efficient parallel development while minimizing conflicts and maintaining code quality.

**Document Version:** 1.0.0  
**Last Updated:** 2025-10-30  
**Status:** Active

---

## 🎯 Objectives

1. **Enable Parallel Development**: Allow three squads to work simultaneously without blocking each other
2. **Minimize Conflicts**: Reduce merge conflicts through clear ownership and coordination
3. **Maintain Quality**: Ensure code quality and type safety through automated checks
4. **Accelerate Delivery**: Ship MVP features faster through parallel workstreams

---

## 👥 Squad Structure

### Platform Squad
**Focus**: Shared components, design system, TypeScript infrastructure

**Current Work**:
- ✅ Issue #855: Fix component Props type mismatches (10 components)
- 📋 Issue #851: Restore Storybook type safety
- ⏸️ Issue #935: Enable strict mode (DELAYED until MVP/Owner Console skeleton complete)
- ⏸️ Issue #936: Tighten spring-animation types (DELAYED)

**Responsibilities**:
- Maintain shared UI components (`/packages/shared-ui/`, `/src/components/ui/`)
- Manage design system and tokens (`/docs/UX/tokens.json`)
- Ensure TypeScript type safety across the codebase
- Review all changes to shared components (via CODEOWNERS)

### MVP Squad
**Focus**: Agent Registry, Monitoring, Metrics Dashboard

**Roadmap**:
1. **Issue #760: Agent Registry & Task Router** (Week 1-2)
   - Define OpenAPI contract ✅
   - Generate typed clients
   - Build scaffolding
   - Use feature flags for isolation

2. **Issue #768: Monitoring Foundation** (Week 1-2)
   - Establish monitoring infrastructure ✅
   - Define metrics schema ✅
   - Integrate with Sentry

3. **Issue #762: Metrics & Dashboard** (Week 2-3)
   - Use #768 metrics schema
   - Design visualization interface
   - Use feature flags for isolation

4. **Issue #761: Closed-loop Scenarios** (Week 3-4, DELAYED)
   - Wait for #760 contract stability
   - Or use mocks with feature flags

**Responsibilities**:
- Agent system implementation (`/agents/`, `/handoff/20250928/40_App/orchestrator/`)
- API endpoints for agent operations
- Metrics collection and visualization
- Closed-loop automation workflows

### Owner Console Squad
**Focus**: Admin interface, API connection, PWA

**Roadmap**:
1. **Issue #767: API Connection** (Week 1-2)
   - Build API connection scaffolding
   - Implement JWT + Refresh Token mechanism
   - Use feature flags for isolation

2. **Issue #774: PWA Implementation** (Week 1-2)
   - Service Worker setup
   - manifest.json configuration
   - Push Notifications
   - Use feature flags for isolation

3. **Issue #768: Monitoring Foundation** (Week 1-2, SHARED with MVP Squad)
   - Establish monitoring infrastructure

4. **Other Issues (#769-773)** (Week 3-4)
   - Agent Governance Dashboard
   - Tenant Management
   - System Monitoring
   - Platform Settings
   - Security & Audit

**Responsibilities**:
- Owner Console application (`/handoff/20250928/40_App/owner-console/`)
- Admin-specific API endpoints
- PWA features and offline support
- Governance and compliance interfaces

---

## 🛡️ Protection Mechanisms

### 1. Feature Flags

**Implementation**: `/handoff/20250928/40_App/frontend-dashboard/src/lib/feature-flags.ts`

All new features MUST be behind feature flags with default value `false`:

```typescript
import { isFeatureEnabled } from '@/lib/feature-flags';

// MVP Squad
if (isFeatureEnabled('MVP_AGENT_REGISTRY')) {
  // New agent registry code
}

// Owner Console Squad
if (isFeatureEnabled('OWNER_CONSOLE_API')) {
  // New owner console code
}
```

**Benefits**:
- Merge to main anytime without affecting production
- Early merge, frequent merge = fewer conflicts
- Easy rollback if issues arise
- A/B testing capabilities

**Available Flags**:
- `MVP_AGENT_REGISTRY` - Agent Registry & Task Router (Issue #760)
- `MVP_CLOSED_LOOP` - Closed-loop Scenarios (Issue #761)
- `MVP_METRICS_DASHBOARD` - Metrics & Dashboard (Issue #762)
- `MVP_MONITORING_FOUNDATION` - Monitoring Foundation (Issue #768)
- `OWNER_CONSOLE_API` - API Connection (Issue #767)
- `OWNER_CONSOLE_GOVERNANCE` - Agent Governance Dashboard (Issue #769)
- `OWNER_CONSOLE_TENANTS` - Tenant Management (Issue #770)
- `OWNER_CONSOLE_MONITORING` - System Monitoring (Issue #771)
- `OWNER_CONSOLE_SETTINGS` - Platform Settings (Issue #772)
- `OWNER_CONSOLE_SECURITY` - Security & Audit (Issue #773)
- `OWNER_CONSOLE_PWA` - PWA Implementation (Issue #774)

**Enabling Flags** (for testing):
```bash
# Environment variable (production)
VITE_FEATURE_MVP_AGENT_REGISTRY=true

# localStorage (local development)
localStorage.setItem('feature_flag_MVP_AGENT_REGISTRY', 'true')

# URL parameter (testing)
?feature_MVP_AGENT_REGISTRY=true

# DevTools console
window.__FEATURE_FLAGS__.enable('MVP_AGENT_REGISTRY')
```

### 2. API-Contract-First Development

**Implementation**: `/handoff/20250928/30_API/openapi/agent-registry-v1.yaml`

**Process**:
1. Define OpenAPI contract FIRST
2. Generate typed clients for frontend
3. Backend and frontend develop in parallel
4. Use mocks for frontend development if backend not ready

**Example**:
```yaml
# OpenAPI Contract
/api/v1/agents:
  get:
    summary: List all agents
    responses:
      200:
        schema:
          $ref: '#/components/schemas/AgentListResponse'
```

```typescript
// Generated typed client (auto-generated)
import { AgentListResponse } from '@/api/generated';

const agents: AgentListResponse = await api.agents.list();
```

**Benefits**:
- Frontend and backend can develop in parallel
- Type safety across the stack
- Clear API boundaries
- Easy to mock for testing

### 3. CODEOWNERS Protection

**Implementation**: `/CODEOWNERS`

Shared components require Platform Squad review:

```
# Shared UI Components
/packages/shared-ui/ @RC918
/handoff/20250928/40_App/frontend-dashboard/src/components/ui/ @RC918

# Design System
/docs/UX/tokens.json @RC918

# Core Types
/handoff/20250928/40_App/frontend-dashboard/src/types/ @RC918
```

**Benefits**:
- Prevents accidental breaking changes to shared components
- Ensures shared interfaces remain stable
- Platform Squad can coordinate changes across squads

**Protocol**:
1. Any PR modifying shared components automatically requests Platform Squad review
2. Breaking changes MUST include migration guide or codemod
3. Notify all squads in #engineering channel before merging

### 4. Branch Protection Rules

**Current CI Checks** (`.github/workflows/frontend.yml`):
- ✅ Lint
- ✅ Test
- ✅ Typecheck (Issue #932)
- ✅ Build

**Required Status Checks**:
- `backend-ci` - Backend tests and coverage (74% minimum)
- `frontend-ci` - Frontend build, lint, typecheck
- `openapi-verify` - OpenAPI spec validation
- `post-deploy-health-assertions` - Production health checks
- `orchestrator-e2e` - Orchestrator E2E tests

**Benefits**:
- Any PR breaking type safety will fail CI
- Protects main branch quality
- Automated enforcement of standards

---

## 📅 Development Timeline

### Sprint 1 (Week 1-2)

**Platform Squad**:
- ✅ Complete Issue #855 (Fix 10 component type mismatches)
- 📋 Start Issue #851 (Restore Storybook type safety)

**MVP Squad**:
- 🚀 Start Issue #760 (Define OpenAPI contract + scaffolding)
- 🚀 Start Issue #768 (Monitoring foundation)
- 📊 Design Issue #762 (Metrics schema)

**Owner Console Squad**:
- 🚀 Start Issue #767 (API Connection scaffolding)
- 🚀 Start Issue #774 (PWA shell)
- 📊 Use Issue #768 (Shared Monitoring foundation)

### Sprint 2 (Week 3-4)

**Platform Squad**:
- ✅ Complete Issue #851 (Storybook type safety)
- ⏸️ Pause #935/#936 (Wait for MVP/Owner Console skeleton)

**MVP Squad**:
- ✅ Complete Issue #760 (Agent Registry skeleton)
- 🚀 Start Issue #761 (Use #760 contract or mocks)
- ✅ Complete Issue #762 (Metrics Dashboard skeleton)

**Owner Console Squad**:
- ✅ Complete Issue #767 (API Connection)
- ✅ Complete Issue #774 (PWA)
- 🚀 Start other Owner Console features (#769-773)

### Sprint 3+ (Week 5+)

**Platform Squad**:
- 🚀 Resume #935 (Enable strict mode) - after MVP/Owner Console skeleton complete
- 🚀 Resume #936 (Tighten spring-animation types)

**MVP Squad**:
- 🚀 Complete Issue #761 (Closed-loop scenarios)
- 🚀 Iterate on #760, #762 based on feedback

**Owner Console Squad**:
- 🚀 Complete remaining features (#769-773)
- 🚀 Iterate based on feedback

---

## ⚠️ Risk Management

### Risk 1: Shared Component Conflicts

**Impact**: apple-button, apple-input, apple-modal, etc.

**Mitigation**:
- ✅ Issue #855 modifies these components (id: required → optional)
- ✅ Create compatibility wrappers or codemod plan before changes
- ✅ Notify all squads of upcoming interface changes
- ✅ CODEOWNERS ensures Platform Squad reviews all changes

**Action Plan**:
1. Platform Squad announces planned changes in #engineering
2. All squads review impact on their work
3. Platform Squad provides migration guide
4. Squads update their code before/after merge

### Risk 2: TypeScript Strict Mode Changes

**Impact**: Issue #935 (strict: true) and #936 (tighten types) cause large-scale changes

**Mitigation**:
- ⏸️ **DELAYED until MVP/Owner Console skeleton complete**
- 📅 Schedule a "refactoring window" where all squads pause new features
- 🔄 Concentrate on fixing all type errors together
- 📋 Create comprehensive migration guide

**Action Plan**:
1. Wait for MVP/Owner Console skeleton (Sprint 2 end)
2. Announce 1-week refactoring window
3. All squads pause new feature work
4. Platform Squad leads strict mode migration
5. All squads fix type errors in their areas
6. Resume normal development after migration

### Risk 3: CI Capacity and Test Stability

**Impact**: Multiple PRs running simultaneously may cause CI queuing or instability

**Mitigation**:
- ✅ Typecheck step already added (Issue #932)
- 📊 Monitor CI execution time
- 🔧 Enable test sharding if needed
- 💾 Enable build caching (Turborepo)

**Action Plan**:
1. Monitor CI queue depth daily
2. If queue > 5 PRs, investigate bottlenecks
3. Enable Turborepo remote caching if needed
4. Consider GitHub Actions matrix builds for parallelization

### Risk 4: API Contract Drift

**Impact**: Frontend and backend implementations diverge from OpenAPI contract

**Mitigation**:
- ✅ OpenAPI validation in CI (`openapi-verify` workflow)
- ✅ Generate typed clients from OpenAPI spec
- 📋 Backend validates requests against OpenAPI schema

**Action Plan**:
1. Backend MUST implement exactly what OpenAPI spec defines
2. Frontend MUST use generated typed clients
3. Any contract changes require RFC (Request for Comments)
4. Use API versioning for breaking changes

---

## 🔄 Coordination Workflows

### Daily Standup (Async)

**Format**: Post in #engineering channel

**Template**:
```
**Squad**: [Platform/MVP/Owner Console]
**Yesterday**: [What you completed]
**Today**: [What you're working on]
**Blockers**: [Any blockers or dependencies]
**Shared Component Changes**: [Any changes affecting other squads]
```

### Weekly Sync (30 minutes)

**Agenda**:
1. Review progress against sprint goals (10 min)
2. Discuss upcoming shared component changes (10 min)
3. Identify cross-squad dependencies (5 min)
4. Plan next week's priorities (5 min)

**Attendees**: Squad leads + Platform Squad

### Shared Component Change Protocol

**When**: Before modifying any shared component

**Steps**:
1. Post RFC in #engineering channel
2. Tag all squad leads
3. Wait 24 hours for feedback
4. Address concerns or adjust plan
5. Proceed with change
6. Provide migration guide if breaking

**Example RFC**:
```
**RFC: Change apple-button `id` prop from required to optional**

**Motivation**: Many use cases don't need explicit IDs

**Impact**: 
- Breaking change for components passing `id` as required
- Affects: apple-button, apple-input, apple-modal

**Migration**:
- Remove `id` prop if not needed
- Or keep passing `id` (still supported)

**Timeline**: Merge in 48 hours if no objections

**Feedback**: Reply in thread
```

---

## 📊 Success Metrics

### Development Velocity
- **Sprint Velocity**: Story points completed per sprint
- **PR Merge Time**: Time from PR open to merge (target: < 24 hours)
- **CI Pass Rate**: Percentage of PRs passing CI on first try (target: > 90%)

### Code Quality
- **Test Coverage**: Maintain or improve coverage (current: 74%, target: 80%+)
- **TypeScript Errors**: Zero type errors in production code
- **Lint Errors**: Zero lint errors

### Collaboration
- **Merge Conflicts**: Number of merge conflicts per PR (target: < 1)
- **Shared Component Changes**: Number of breaking changes to shared components (target: minimize)
- **Cross-Squad Dependencies**: Number of blocked tasks due to dependencies (target: < 5%)

### Feature Delivery
- **Feature Completion Rate**: Percentage of planned features completed on time (target: > 85%)
- **Bug Rate**: Number of bugs introduced per feature (target: < 2)
- **Rollback Rate**: Percentage of features requiring rollback (target: < 5%)

---

## 🛠️ Tools and Resources

### Feature Flags
- **File**: `/handoff/20250928/40_App/frontend-dashboard/src/lib/feature-flags.ts`
- **DevTools**: `window.__FEATURE_FLAGS__.list()`
- **Docs**: See "Feature Flags" section above

### OpenAPI Contracts
- **Directory**: `/handoff/20250928/30_API/openapi/`
- **Agent Registry**: `agent-registry-v1.yaml`
- **Validation**: `.github/workflows/openapi-verify.yml`

### Monitoring Schema
- **File**: `/config/monitoring/metrics-schema.yaml`
- **Docs**: See Issue #768

### CODEOWNERS
- **File**: `/CODEOWNERS`
- **Docs**: https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners

### CI/CD Workflows
- **Directory**: `.github/workflows/`
- **Key Workflows**:
  - `backend.yml` - Backend CI
  - `frontend.yml` - Frontend CI
  - `openapi-verify.yml` - OpenAPI validation
  - `pr-guard.yml` - Design vs Engineering PR separation

---

## 📚 Additional Resources

### Documentation
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Contribution guidelines
- [ARCHITECTURE.md](../ARCHITECTURE.md) - System architecture
- [CTO_COMPREHENSIVE_TECHNICAL_DEEP_DIVE_2025.md](../CTO_COMPREHENSIVE_TECHNICAL_DEEP_DIVE_2025.md) - Technical assessment

### Issue Templates
- [RFC Template](.github/ISSUE_TEMPLATE/rfc.md) - For API/schema changes

### Communication Channels
- **#engineering** - General engineering discussion
- **#platform-squad** - Platform Squad coordination
- **#mvp-squad** - MVP Squad coordination
- **#owner-console-squad** - Owner Console Squad coordination

---

## ❓ FAQ

### Q: Can I modify a shared component for my feature?

**A**: Yes, but follow the Shared Component Change Protocol:
1. Post RFC in #engineering
2. Wait 24 hours for feedback
3. Get Platform Squad approval (via CODEOWNERS)
4. Provide migration guide if breaking

### Q: My PR is blocked by another squad's work. What should I do?

**A**: 
1. Check if you can use feature flags to isolate your work
2. Check if you can use mocks or stubs temporarily
3. If truly blocked, raise in daily standup
4. Consider pairing with the other squad to unblock

### Q: How do I enable a feature flag for testing?

**A**:
```typescript
// In DevTools console
window.__FEATURE_FLAGS__.enable('MVP_AGENT_REGISTRY')

// Or via URL
?feature_MVP_AGENT_REGISTRY=true

// Or via localStorage
localStorage.setItem('feature_flag_MVP_AGENT_REGISTRY', 'true')
```

### Q: When should I create an RFC?

**A**: Create an RFC for:
- OpenAPI/API contract changes
- Database schema changes
- Breaking changes to shared components
- Major architectural decisions

### Q: What if CI is failing due to another squad's changes?

**A**:
1. Check if it's a real conflict or flaky test
2. Rebase your branch on latest main
3. If still failing, contact the squad that made the change
4. If urgent, revert the breaking change and notify the squad

### Q: How do I know if my change affects other squads?

**A**: Your change affects other squads if it modifies:
- `/packages/shared-ui/` - Shared UI components
- `/src/components/ui/` - UI components
- `/src/types/` - Type definitions
- `/docs/UX/tokens.json` - Design tokens
- OpenAPI contracts
- Database schemas

---

## 📝 Changelog

### Version 1.0.0 (2025-10-30)
- Initial version
- Defined three-squad structure
- Established protection mechanisms
- Created coordination workflows
- Documented risk management strategies

---

**Document Owner**: Platform Squad  
**Last Review**: 2025-10-30  
**Next Review**: 2025-11-13 (2 weeks)
