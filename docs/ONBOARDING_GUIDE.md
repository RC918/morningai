# MorningAI Onboarding Guide

**Welcome to MorningAI!** 🎉

> 📚 **相關文件**: 
> - [術語對照表](./TERMINOLOGY.md) - 標準化的應用名稱和用戶類型定義
> - [專案結構報告](./PROJECT_STRUCTURE_REPORT.md) - 詳細的目錄組織和架構模式
> - [README](../README.md) - 專案概覽和快速導航
> - [環境變數 Schema](../config/env.schema.yaml) - 環境變數配置的單一真源

This guide will help you get started with the MorningAI project, understand the architecture, set up your development environment, and start contributing.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Environment Architecture](#environment-architecture)
3. [Orchestrator Architecture](#orchestrator-architecture)
4. [Getting Started](#getting-started)
5. [Development Workflow](#development-workflow)
6. [Key Technologies](#key-technologies)
7. [Project Structure](#project-structure)
8. [Important Documentation](#important-documentation)
9. [Common Tasks](#common-tasks)
10. [Troubleshooting](#troubleshooting)
11. [Getting Help](#getting-help)

---

## Project Overview

### What is MorningAI?

MorningAI is an intelligent agent orchestration platform that automates software development, operations, and project management tasks. The system employs multiple specialized AI agents that work collaboratively to handle bug fixes, create pull requests, manage infrastructure, respond to incidents, and make strategic decisions.

### Vision

Building the world's most advanced autonomous AI agent orchestration platform that seamlessly integrates development, operations, and business intelligence with human-in-the-loop governance.

### Current Status (Updated: 2025-11-26)

- **Phase**: Phase 8 (v8.0.0) - MVP Foundation Complete
- **Test Coverage**: 
  - Owner Console: **59.89% lines, 45.76% branches** (32 E2E tests passing, 218 unit tests)
  - Backend: **74%+** (CI environment fixed, all tests passing)
  - Target: 80% by Q2 2026
- **Uptime**: 90% (Target: 99.9% by Q2 2026)
- **Transformation**: Q4 2025 - Q2 2026 (MVP to World-Class)
- **Latest Roadmap**: [Strategic Roadmap Reality Comparison](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md) (Nov 16, 2025)

**Recent Improvements (Nov 25-26, 2025)**:
- **PR #1548**: Frontend Dashboard Code Splitting - 20% bundle reduction + Lighthouse CI color-contrast fix
  - Path: `handoff/20250928/40_App/frontend-dashboard/`
  - Impact: Improved performance and accessibility compliance
- **PR #1562**: RQ Job Timeout Configuration - Added `RQ_JOB_TIMEOUT` environment variable
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Path: `config/env.schema.yaml`
  - Impact: Configurable job timeout for long-running tasks (default: 3600s)
- **PR #1547**: AppleButton Migration to shared-ui - Adapter pattern implementation
  - Path: `packages/shared-ui/`
  - Impact: Unified component library across frontend-dashboard and owner-console
- **PR #1546**: Phase 2 UI Completion - Emotional colors, AppleButton alignment, Spring animations
  - Path: `handoff/20250928/40_App/frontend-dashboard/src/`
  - Impact: Enhanced Apple design system consistency
- **PR #1545**: P1 Emotional Colors + AgentExecutionLogs Apple Design
  - Path: `handoff/20250928/40_App/owner-console/src/components/AgentExecutionLogs.tsx`
  - Impact: Consistent design language across Owner Console
- **PR #1544**: Apple Design System Global Application
  - Path: `handoff/20250928/40_App/frontend-dashboard/`, `handoff/20250928/40_App/owner-console/`
  - Impact: Unified UI/UX across all frontend applications
- **PR #1543**: Dark Mode Disable + PlatformSettings Card Styling
  - Path: `handoff/20250928/40_App/owner-console/`
  - Impact: Improved accessibility and visual consistency
- **UUID Normalization Fix**: Handle prefixed task IDs from external tools
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Impact: Improved compatibility with external task submission tools
- **LoginPage UX Improvements**: Comprehensive redesign using Apple design system
  - Path: `handoff/20250928/40_App/frontend-dashboard/src/components/LoginPage.tsx`
  - Impact: Fixed icon blur, added static labels, improved accessibility

**Previous Improvements (Nov 18-23, 2025)**:
- **PR #1350**: E2E Testing Infrastructure - Fixed 21 failing tests, implemented route handler isolation, added comprehensive API mocking
  - Path: `handoff/20250928/40_App/owner-console/e2e/`
  - Result: 32 E2E tests passing (11→32), 55/55 CI checks passing
- **PR #1398**: Production Path Discovery - Replaced hardcoded repo path with 4-layer fallback mechanism
  - Path: `handoff/20250928/40_App/orchestrator/context_manager.py`
  - Added: `MORNINGAI_REPO_PATH` environment variable for production/staging
- **PR #1399**: Backend Test Environment - Unified Python 3.12, added Redis service, fixed PyJWT conflicts
  - Path: `.github/workflows/test-apps.yml`
  - Result: Backend tests now consistent across all CI workflows
- **PR #1480**: Pydantic Alias System - Added 23 critical environment variable aliases (Nov 23)
  - Path: `common/config/settings.py`
  - Fixed: `FLASK_SECRET_KEY`, `ENCRYPTION_MASTER_KEY`, `STRIPE_WEBHOOK_SECRET_KEY` aliases
  - Impact: Backward compatibility improvements, standardized configuration naming
- **PR #1452**: Redis Mapping Sanitization - Prevent NoneType DataError (Nov 23)
  - Path: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py`
  - Added: `sanitize_redis_mapping()` function to filter None values
  - Impact: Improved worker heartbeat and task status update stability
- **PR #1455**: AgentExecutionLogs Accessibility Fixes - Resolved 6 critical a11y violations (Nov 23)
  - Path: `handoff/20250928/40_App/owner-console/src/components/AgentExecutionLogs.tsx`
  - Fixed: Pagination controls, table headers, ARIA labels
  - Impact: Enhanced Owner Console accessibility standards
- **PR #1437**: i18n Error Fixes - Fixed 10 i18n errors in owner-console (Nov 23)
  - Path: `handoff/20250928/40_App/owner-console/src/components/`
  - Enabled: ESLint blocking to prevent future i18n regressions
  - Impact: Improved internationalization quality and consistency

### Key Features

**Infrastructure & Security (Completed):**
- ✅ **RLS Implementation**: Row-level security with 70 policies across 6 migrations
- ✅ **Secret Scanning**: Gitleaks + TruffleHog in CI, blocks PRs with secrets
- ✅ **2FA**: Complete TOTP implementation with 10 components, enforced login
- ✅ **Storybook**: Owner Console with MSW, dark mode, a11y checks
- ✅ **E2E Testing**: 32 Playwright tests with route handler isolation and API mocking
- ✅ **CI/CD**: Unified backend test environment (Python 3.12, Redis service, 74%+ coverage)

**AI Agents (In Development):**
- **Dev_Agent**: Automated bug fixing and PR creation (target: >85% success rate)
- **Ops_Agent**: Automated incident response and self-healing (target: >70% automation)
- **PM_Agent**: Project management and task tracking
- **Growth_Strategist**: Business strategy and optimization
- **Meta_Agent**: Agent orchestration and OODA loop coordination

**Note**: Agent success rates are aspirational targets. Evaluation harness created but not yet integrated. See [Agent Evaluation Guide](../tools/agent_eval/README.md).

---

## Environment Architecture

MorningAI uses a multi-environment deployment architecture to ensure safe development, testing, and production workflows.

### 🚀 Production Environment

**Services**:
- **Backend API**: https://morningai-backend-v2.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api.onrender.com
- **Frontend**: https://morningai.vercel.app

⚠️ **Orchestrator Architecture (Dual System)**

MorningAI uses a producer-consumer architecture with two orchestrator implementations:

| Component | Role | Maturity | Service | Path |
|-----------|------|----------|---------|------|
| **API Orchestrator** | API Layer (FastAPI) | Beta | `morningai-orchestrator-api` | `orchestrator/` |
| **Worker Orchestrator** | Task Execution (RQ) | Production | `morningai-agent-worker` | `handoff/20250928/40_App/orchestrator/` |

**Dual Execution Modes**:
- **Simple Mode** (Production): `handoff/20250928/40_App/orchestrator/graph.py` - Fast, stateless execution (currently enabled via `USE_LANGGRAPH=false` in `render.yaml:48-49`)
- **LangGraph Mode** (Optional): `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py:1-422` - Full state machine with retry logic, CI monitoring (can be enabled via `USE_LANGGRAPH=true`)
- **Runtime Selection**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:303-307` conditionally imports orchestrator based on environment flag

**See**: [ADR-005](adr/005-dual-orchestrator-architecture.md), [ADR-002](adr/002-producer-consumer-architecture.md), [ADR-004](adr/004-shared-core-executor-pattern.md) • **Consolidation**: 2026 Q1

**Infrastructure**:
- **Database**: Supabase PostgreSQL (production)
- **Redis**: Upstash (TLS enabled)
- **Branch**: `main`
- **Auto-Deploy**: Yes

### 🧪 Staging Environment ✅

**Services**:
- **Backend API**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api-stg.onrender.com
- **Frontend (Dashboard)**: https://staging.morningai.me
- **Frontend (Owner Console)**: https://staging-owner.morningai.me

**Infrastructure**:
- **Database**: Supabase PostgreSQL (staging: dckisglnlemvpvmyvnut)
- **Redis**: Upstash (shared, key prefix: `stg:`)
- **Branch**: `develop`
- **Auto-Deploy**: Yes
- **Status**: ✅ Fully Operational

**Frontend Deployment** (Vercel):
- **Branch Policy**: `develop` → staging, `main` → production, `feature/*|fix/*|devin/*` → preview
- **Ignore Script**: Skips deployment for docs-only changes
- **Documentation**: [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](../deployment/VERCEL_DEPLOYMENT_STRATEGY.md)

**Purpose**:
- Pre-production testing
- Integration testing
- Feature validation before production

### 💻 Local Development

**Services**:
- **Backend**: `http://localhost:8000`
- **Orchestrator**: `http://localhost:8001`
- **Frontend**: `http://localhost:5173`

**Infrastructure**:
- **Database**: Local PostgreSQL or Staging Supabase
- **Redis**: Local Redis or Staging Redis

### Deployment Flow

```
Feature Branch → develop (Staging) → main (Production)
```

**Detailed Documentation**: [docs/ENVIRONMENTS.md](ENVIRONMENTS.md)

---

## Orchestrator Architecture

### Overview: Two Execution Modes

MorningAI's orchestrator uses a **dual-mode architecture** with a shared core executor. Understanding this architecture is critical for new contributors to avoid confusion and rework.

```
┌─────────────────────────────────────────────────────────────┐
│ HTTP Request: POST /faq                                      │
│ Body: {"question": "..."}                                    │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ API Backend (agent.py)                                       │
│ - Generate task_id = UUID()                                 │
│ - Enqueue: run_orchestrator_task(task_id, question, repo)  │
│ - Return 202 Accepted                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Redis Queue (orchestrator)                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ Worker (worker.py:366-400) - ROUTING DECISION               │
│                                                              │
│ if USE_LANGGRAPH=false and USE_LANGGRAPH_PERCENT > 0:      │
│     task_hash = MD5(task_id) % 100                          │
│     use_langgraph = (task_hash < USE_LANGGRAPH_PERCENT)    │
│                                                              │
│ Current: USE_LANGGRAPH=false, USE_LANGGRAPH_PERCENT=5      │
│ → ~5% tasks route to LangGraph                              │
│ → ~95% tasks route to Simple                                │
└────────────────────┬───────────────────┬────────────────────┘
                     │                   │
       use_langgraph=true    use_langgraph=false
                     │                   │
                     ▼                   ▼
        ┌─────────────────────┐  ┌──────────────────┐
        │ LangGraph Mode      │  │ Simple Mode      │
        │ (~5% tasks)         │  │ (~95% tasks)     │
        └──────────┬──────────┘  └────────┬─────────┘
                   │                      │
                   ▼                      ▼
        ┌──────────────────┐    ┌────────────────┐
        │ langgraph_       │    │ graph.execute  │
        │ orchestrator.py  │    │ (direct)       │
        │   ↓              │    └────────────────┘
        │ executor_node    │
        │   ↓              │
        │ graph.execute    │
        └──────────────────┘
```

### Mode 1: Simple Mode (Current: ~95% Traffic)

**Files**:
- Entry: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:399`
- Executor: `handoff/20250928/40_App/orchestrator/graph.py`

**Characteristics**:
- ✅ **Fast**: Direct execution, no state machine overhead
- ✅ **Stable**: Battle-tested, production-proven
- ✅ **Stateless**: No retry logic, no CI monitoring
- ❌ **Feature-frozen**: Only bug fixes accepted

**When Used**:
- `USE_LANGGRAPH=false` (default)
- Task's MD5 hash % 100 >= `USE_LANGGRAPH_PERCENT`

**Flow**:
```
Worker → graph.execute() → Create PR → Return result
```

### Mode 2: LangGraph Mode (Current: ~5% Traffic, Phase 1)

**Files**:
- Entry: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:396`
- Orchestrator: `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py`
- Executor: `handoff/20250928/40_App/orchestrator/graph.py:30` (shared!)

**Characteristics**:
- ✅ **Stateful**: Full state machine with LangGraph
- ✅ **Intelligent**: LLM-powered planning (when `USE_LLM_PLANNER=true`)
- ✅ **Resilient**: Retry logic, error handling, CI monitoring
- ✅ **Active Development**: New features go here

**When Used**:
- `USE_LANGGRAPH=true` (100% routing), OR
- `USE_LANGGRAPH=false` + Task's MD5 hash % 100 < `USE_LANGGRAPH_PERCENT`

**Flow**:
```
Worker → langgraph_orchestrator.run_orchestrator()
  → planner_node (LLM or static)
  → executor_node → graph.execute()
  → ci_monitor_node
  → fixer_node (if needed)
  → finalizer_node
```

### Shared Core: graph.execute()

**Critical Understanding**: `graph.execute()` is **NOT** just the "old Simple orchestrator" - it's the **shared execution engine** for both modes!

**File**: `handoff/20250928/40_App/orchestrator/graph.py:30-155`

**Used By**:
1. **Simple Mode**: Direct call from `worker.py:399`
2. **LangGraph Mode**: Called by `executor_node` in `langgraph_orchestrator.py:143`

**What It Does**:
- Cost tracking and budget enforcement
- Rate limiting (10 PRs/hour)
- FAQ content generation with GPT-4
- Git branch creation and PR opening
- CI check monitoring
- Test mode auto-cleanup

**⚠️ Important**: Changes to `graph.execute()` affect **BOTH** modes. Always mention this in PR descriptions.

### Routing Logic (Canary Deployment)

**File**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-395`

**Algorithm**:
```python
use_langgraph = settings.use_langgraph or False
use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)

if not use_langgraph and use_langgraph_percent > 0:
    # Canary logic: MD5 hash for deterministic routing
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100  # 0-99 bucket
    use_langgraph = task_percent < use_langgraph_percent
```

**Properties**:
- **Deterministic**: Same task_id always routes to same mode
- **Uniform**: MD5 ensures even distribution across 0-99 buckets
- **Controllable**: Adjust `USE_LANGGRAPH_PERCENT` to change traffic split

**Current Configuration** (Staging/Production):
```
USE_LANGGRAPH = false              # Allow canary (not 100%)
USE_LANGGRAPH_PERCENT = 5          # 5% to LangGraph
USE_LLM_PLANNER = true             # LangGraph uses LLM planner
```

**Result**: ~5% of tasks use LangGraph + LLM Planner, ~95% use Simple mode.

### Environment Variables

| Variable | Default | Purpose | Affects |
|----------|---------|---------|---------|
| `USE_LANGGRAPH` | `false` | Force 100% LangGraph routing | Worker routing |
| `USE_LANGGRAPH_PERCENT` | `0` | Canary percentage (0-100) | Worker routing |
| `USE_LLM_PLANNER` | `false` | Use LLM vs static planner | LangGraph only |

**Override Behavior**:
- `USE_LANGGRAPH=true` → 100% LangGraph (overrides percent)
- `USE_LANGGRAPH=false` + `USE_LANGGRAPH_PERCENT=0` → 100% Simple (Kill Switch)
- `USE_LANGGRAPH=false` + `USE_LANGGRAPH_PERCENT=5` → 5% canary

### Development Guidelines

#### ✅ DO: Adding New Orchestrator Features

**Implement in LangGraph mode only**:
```python
# handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py

def new_feature_node(state: AgentState) -> AgentState:
    """New orchestrator feature"""
    # Your implementation here
    return state

# Add to workflow
workflow.add_node("new_feature", new_feature_node)
workflow.add_edge("planner", "new_feature")
```

**Why**: Simple mode is feature-frozen. All new orchestrator logic goes in LangGraph.

#### ✅ DO: Modifying Shared Executor

**When changing `graph.execute()`**:
1. Test with **both** Simple and LangGraph modes
2. Add tests in `test_graph.py` AND `test_langgraph_ci.py`
3. **Clearly state in PR description**: "This change affects both Simple and LangGraph modes"

**Example PR description**:
```markdown
## Changes to Shared Executor

This PR modifies `graph.execute()` which is used by both orchestrator modes:
- Simple mode: Direct call from worker
- LangGraph mode: Called by executor_node

**Testing**: Verified with both modes in staging.
```

#### ❌ DON'T: Adding Features to Simple Mode

**Never do this**:
```python
# handoff/20250928/40_App/orchestrator/graph.py

def execute(goal, repo, trace_id):
    # ❌ DON'T add new orchestrator features here
    new_fancy_feature()  # This is wrong!
```

**Why**: Simple mode is frozen. New features belong in LangGraph.

#### ❌ DON'T: Assume Only One Mode Exists

**Bad assumption**: "I'll just modify the orchestrator" (which one?)

**Good practice**: "I'll modify the LangGraph orchestrator's planner_node"

### Monitoring & Observability

**Canary Routing Logs** (search in Render Dashboard):
```
"Canary deployment"           # Routing decision
"Using LangGraph orchestrator" # LangGraph execution
"Using simple orchestrator"    # Simple execution
"Using LLM planner"           # LLM planner selection
```

**Metrics** (`worker.py:386-393`):
```python
_canary_metrics.incr_counter("decisions.langgraph")  # LangGraph count
_canary_metrics.incr_counter("decisions.simple")     # Simple count
_canary_metrics.observe_latency_ms(elapsed_ms)       # Latency
```

**Structured Logging**:
```json
{
  "operation": "canary_selection",
  "task_id": "...",
  "task_percent": 42,
  "use_langgraph_percent": 5,
  "use_langgraph": false
}
```

### Migration Roadmap

⚠️ **注意**：本文檔描述架構設計和政策。實際環境變數配置可能因運維需求調整。請以 Render Dashboard 的實際配置為準。

**Phase 1 參考狀態** (Nov 2025):
- ✅ Simple mode: ~95% traffic (stable baseline)
- ✅ LangGraph mode: ~5% traffic (validation)
- ✅ LLM Planner: Enabled for LangGraph tasks

**實際配置查詢**:
| 服務 | USE_LANGGRAPH | USE_LANGGRAPH_PERCENT | USE_LLM_PLANNER |
|------|---------------|----------------------|-----------------|
| Staging Worker | `false` | `5` | `true` |
| Production Worker | `false` | `5` | `true` |

查看位置: Render Dashboard → Service → Environment Tab

**Near-Term** (Phase 2 - Q1 2026):
- 🎯 Gradually increase `USE_LANGGRAPH_PERCENT`: 5% → 25% → 50% → 100%
- 🎯 Monitor success rates, costs, latency at each step
- 🎯 Keep Simple mode as Kill Switch

**Long-Term** (Phase 3 - Q2 2026):
- 🎯 100% LangGraph routing (`USE_LANGGRAPH=true`)
- 🎯 Refactor `graph.py`:
  - **Option A** (Recommended): Rename to `core_executor.py`, keep only `execute()` function
  - **Option B**: Integrate executor logic into `langgraph_orchestrator.py`, remove `graph.py`
- 🎯 Update all documentation and tests

### Testing Both Modes

**Local Testing**:
```bash
# Test Simple mode
export USE_LANGGRAPH=false
export USE_LANGGRAPH_PERCENT=0
python -m pytest tests/test_graph.py

# Test LangGraph mode
export USE_LANGGRAPH=true
export USE_LLM_PLANNER=false  # Use static planner for faster tests
python -m pytest tests/test_langgraph_ci.py

# Test canary routing
export USE_LANGGRAPH=false
export USE_LANGGRAPH_PERCENT=50
python -m pytest tests/test_worker.py::TestCanaryDeployment
```

**Staging Testing**:
```bash
# Check current routing distribution
# In Render Dashboard → Worker Logs (see STAGING_SETUP_GUIDE.md for service names)
# Search: "Canary deployment"

# Expected: ~5% show use_langgraph=True, ~95% show use_langgraph=False
```

### Common Pitfalls

1. **❌ "I'll just update the orchestrator"**
   - Which one? Be specific: Simple or LangGraph?

2. **❌ Modifying `graph.py` without testing LangGraph**
   - `graph.execute()` is used by both modes!

3. **❌ Adding features to Simple mode**
   - Simple mode is frozen. Use LangGraph.

4. **❌ Assuming 100% traffic uses one mode**
   - Current: 95% Simple, 5% LangGraph. Test both!

5. **❌ Searching for wrong log keywords**
   - Use "Canary deployment", not "canary_selection"

### Quick Reference

**Files to Know**:
```
handoff/20250928/40_App/orchestrator/
├── redis_queue/worker.py:366-400    # Routing logic
├── graph.py:30-155                  # Shared executor (BOTH modes)
├── langgraph_orchestrator.py        # LangGraph mode
└── tests/
    ├── test_graph.py                # Simple mode tests
    ├── test_langgraph_ci.py         # LangGraph tests
    └── test_worker.py               # Routing tests
```

**When to Use Which Mode**:
- **Simple Mode**: Production baseline, feature-frozen
- **LangGraph Mode**: New features, active development
- **Shared Executor**: Core execution logic (both modes)

**Questions?** See Orchestrator ADRs ([ADR-005](adr/005-dual-orchestrator-architecture.md), [ADR-002](adr/002-producer-consumer-architecture.md), [ADR-004](adr/004-shared-core-executor-pattern.md)) or ask in #engineering.

---

## Getting Started

### Prerequisites

**Required**:
- **Git**: Version control
- **Python**: 3.12+ (for backend and orchestrator)
- **Node.js**: 20+ (for frontend)
- **pnpm**: 9.15.1+ (package manager)
- **Docker**: For orchestrator development (optional)

**Recommended**:
- **VS Code**: IDE with Python and TypeScript extensions
- **PostgreSQL**: Local database (or use staging)
- **Redis**: Local cache (or use staging)

### Step 1: Clone Repository

```bash
git clone https://github.com/RC918/morningai.git
cd morningai
```

### Step 2: Set Up Python Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Set Up Frontend Environment

```bash
cd handoff/20250928/40_App/frontend-dashboard

# Install dependencies
pnpm install

# Return to root
cd ../../../..
```

### Step 4: Configure Environment Variables

**Environment Schema Workflow** (Single Source of Truth):

MorningAI uses `config/env.schema.yaml` as the canonical source for all environment variables. This ensures consistency across all services and environments.

```bash
# 1. View canonical environment variable definitions
cat config/env.schema.yaml

# 2. Generate .env.example files from schema (auto-updates all services)
python scripts/generate-env-examples.py

# 3. Check for drift between schema and .env.example files
python scripts/check-env-drift.py

# 4. Verify secret inventory matches schema (security operations)
python scripts/verify_secret_inventory.py  # (Added in PR #1084)
```

**Key Points**:
- ✅ Always update `config/env.schema.yaml` first when adding/changing variables
- ✅ Run `generate-env-examples.py` to propagate changes to all `.env.example` files
- ✅ CI automatically checks for drift on every PR
- ✅ See [Secret Rotation Policy](./SECRET_ROTATION_POLICY.md) for security operations

**Recent Additions (PR #1398)**:
- `MORNINGAI_REPO_PATH`: Repository root path for production/staging environments
  - Required in Render.com deployments: `/opt/render/project/src`
  - Falls back to git detection or marker-based discovery in development
  - Path: `config/env.schema.yaml` (Deployment category)

**Backend** (`handoff/20250928/40_App/api-backend/.env`):
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0

# Or use staging infrastructure (recommended)
DATABASE_URL=<staging-database-url>
REDIS_URL=<staging-redis-url>
REDIS_KEY_PREFIX=dev:
```

**Frontend Dashboard** (`handoff/20250928/40_App/frontend-dashboard/.env.local`):
```bash
VITE_API_URL=http://localhost:8000
VITE_ORCHESTRATOR_URL=http://localhost:8001
VITE_ENVIRONMENT=development

# Or point to staging backend (recommended)
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
VITE_ORCHESTRATOR_URL=https://morningai-orchestrator-api-stg.onrender.com
```

**Owner Console** (`handoff/20250928/40_App/owner-console/.env.local`):
```bash
VITE_API_URL=http://localhost:8000
VITE_ENVIRONMENT=development

# Or point to staging backend (recommended)
VITE_API_URL=https://morningai-backend-v2-stg.onrender.com
```

**Note**: Contact your team lead for staging credentials. See `config/env.schema.yaml` for complete list of all environment variables.

### Step 5: Run Services Locally

**Backend** (Flask):
```bash
cd handoff/20250928/40_App/api-backend
source ../../../../../../.venv/bin/activate

# Option 1: Flask CLI (recommended for development)
export FLASK_APP=src.main
flask run --port 8000

# Option 2: Gunicorn (production-like)
gunicorn "src.main:app" --bind 0.0.0.0:8000 --reload

# Access at http://localhost:8000
```

**Orchestrator**:
```bash
cd orchestrator
source ../.venv/bin/activate
uvicorn orchestrator.api.main:app --port 8001 --reload
# Access at http://localhost:8001
```

**Frontend**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm dev
# Access at http://localhost:5173
```

### Step 6: Verify Setup

**Test Backend**:
```bash
curl http://localhost:8000/healthz
# Should return: {"status": "healthy", ...}
```

**Test Orchestrator**:
```bash
curl http://localhost:8001/health
# Should return: {"status": "healthy", ...}
```

**Test Frontend**:
- Open http://localhost:5173 in browser
- Should see MorningAI dashboard

### Step 7: Run Storybook (Optional)

**Owner Console**:
```bash
cd handoff/20250928/40_App/owner-console
pnpm storybook
# Access at http://localhost:6007
```

**Features**:
- MSW addon for API mocking with wildcard host matching
- Dark mode toggle in toolbar (synced with next-themes)
- Test runner with a11y checks: `pnpm test-storybook`
- 13 stories covering SystemMonitoring and AgentExecutionLogs

**Adding MSW Handlers:**
```typescript
export const MyStory = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/your-endpoint', () => {
          return HttpResponse.json({ data: 'mock response' });
        }),
      ],
    },
  },
};
```

**Shared UI Components**:
```bash
cd packages/shared-ui
pnpm storybook
# Access at http://localhost:6006
```

**What is Storybook?**
- Interactive component documentation and testing environment
- View and test UI components in isolation
- Added November 2025 (Storybook 8.6.14)
- Core components documented in `packages/shared-ui` (Card, Button, Badge, Alert, Avatar, Progress, Tabs, Dialog, Input, Form, Table, Pagination, Select, StatusBadge)

**Adding New Stories:**
1. Create `*.stories.tsx` file next to your component
2. Follow existing patterns in `packages/shared-ui/src/components/ui/*.stories.tsx`
3. Stories are automatically discovered by Storybook

**Documentation:** See [Storybook Documentation](https://storybook.js.org/docs/react/get-started/introduction)

---

## Development Workflow

### Branch Strategy

```
main (production)
  ↑
develop (staging)
  ↑
feature/your-feature (development)
```

### Creating a Feature

```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/your-feature-name

# 3. Make changes and commit
git add .
git commit -m "feat: add your feature"

# 4. Push to remote
git push origin feature/your-feature-name

# 5. Create PR to develop
# Go to GitHub and create Pull Request to develop branch
```

### Testing on Staging

```bash
# 1. Merge PR to develop
# GitHub Actions will automatically deploy to staging

# 2. Test on staging
curl https://morningai-backend-v2-stg.onrender.com/healthz

# 3. Verify functionality on staging environment
```

### Deploying to Production

```bash
# 1. Create PR from develop to main
# Requires manual approval

# 2. After approval, merge to main
# GitHub Actions will automatically deploy to production

# 3. Monitor production deployment
curl https://morningai-backend-v2.onrender.com/healthz
```

### PR Guidelines

**Design PRs** (UI/copy/styles only):
- Cannot include API/logic changes
- Enforced by `pr-guard.yml` workflow

**Engineering PRs** (API/logic only):
- Cannot include UI/copy/styles changes
- Enforced by `pr-guard.yml` workflow

**RFC Required** for:
- OpenAPI/schema changes
- Database schema changes
- Breaking changes

**Template**: [.github/ISSUE_TEMPLATE/rfc.md](../.github/ISSUE_TEMPLATE/rfc.md)

---

## Key Technologies

### Backend

- **Framework**: Flask (Python 3.12)
- **Database**: PostgreSQL (Supabase)
- **ORM**: SQLAlchemy
- **Cache**: Redis (Upstash)
- **Task Queue**: RQ (Redis Queue)
- **Testing**: pytest, pytest-cov
- **Deployment**: Render (Web Services)

### Orchestrator

- **Framework**: FastAPI (Python 3.12)
- **Task Management**: Graph-based orchestration
- **Sandbox**: Docker containers on Fly.io
- **MCP**: Management Control Plane
- **Deployment**: Render (Docker)

### Frontend

- **Framework**: React 19.1.0 + Vite 6
- **Language**: TypeScript 5.9
- **Styling**: Tailwind CSS 4.1.7 + Custom Design System
- **State Management**: React Context + Hooks
- **UI Components**: Apple-inspired design system
- **Testing**: Vitest + React Testing Library (planned)
- **Deployment**: Vercel

### Infrastructure

- **Database**: Supabase PostgreSQL
- **Cache**: Upstash Redis
- **Hosting**: Render (backend), Vercel (frontend), Fly.io (sandboxes)
- **CI/CD**: GitHub Actions
- **Monitoring**: Sentry
- **Version Control**: Git + GitHub

---

## Project Structure

```
morningai/
├── .github/                          # GitHub configuration
│   ├── workflows/                    # CI/CD workflows
│   │   ├── backend.yml              # Backend CI
│   │   ├── frontend.yml             # Frontend CI
│   │   ├── staging-deploy.yml       # Staging deployment
│   │   └── ...                      # 15+ workflows
│   └── ISSUE_TEMPLATE/              # Issue templates (RFC, etc.)
│
├── agents/                          # AI Agent implementations
│   ├── dev_agent.py                # Bug fixing agent
│   ├── ops_agent.py                # Operations agent
│   ├── pm_agent.py                 # Project management agent
│   ├── growth_strategist.py        # Business strategy agent
│   └── meta_agent_decision_hub.py  # Agent orchestration
│
├── orchestrator/                    # Task orchestration system
│   ├── api/                        # FastAPI application
│   │   ├── main.py                 # Application entry point
│   │   └── auth.py                 # Authentication
│   ├── task_queue/                 # Redis queue management
│   │   └── redis_queue.py          # Queue implementation
│   ├── Dockerfile                  # Docker configuration
│   └── requirements.txt            # Python dependencies
│
├── phase4_meta_agent_api.py       # Phase 4 API (imported by backend)
├── phase5_data_intelligence_api.py # Phase 5 API (imported by backend)
├── phase6_security_governance_api.py # Phase 6 API (imported by backend)
├── phase6_startup.py              # Phase 6 initialization
├── phase7_startup.py              # Phase 7 initialization
│
├── handoff/20250928/40_App/
│   ├── api-backend/                # Backend API
│   │   ├── src/                    # Source code
│   │   │   ├── main.py            # Flask application (imports phase*.py)
│   │   │   ├── database.py        # Database connection
│   │   │   └── ...                # API modules
│   │   ├── tests/                 # Test suite
│   │   └── requirements.txt       # Python dependencies
│   │
│   ├── frontend-dashboard/         # Frontend application
│   │   ├── src/                   # Source code
│   │   │   ├── App.tsx           # Main application
│   │   │   ├── components/       # React components
│   │   │   └── ...               # Frontend modules
│   │   ├── package.json          # Node.js dependencies
│   │   └── vite.config.ts        # Vite configuration
│   │
│   └── owner-console/             # Owner management console
│       ├── src/components/AgentExecutionLogs.tsx  # Agent execution history (added Nov 2025)
│       ├── src/pages/AgentGovernance.jsx          # Agent governance dashboard
│       └── ...                    # Owner console files
│
**Owner Console Features** (Admin Interface):
- **Agent Governance** (`/governance`) - Agent reputation, permissions, violations
- **Agent Execution Logs** (`/governance` → Execution Logs tab) - **NEW Nov 2025**
  - Detailed task execution history with status, timestamps, and trace IDs
  - Filter by agent type, status, and time range
  - API endpoint: `GET /api/admin/agent-execution-logs`
- **Tenant Management** (`/tenants`) - Multi-tenant account management
- **System Monitoring** (`/monitoring`) - System health and metrics

├── docs/                           # Documentation
│   ├── ENVIRONMENTS.md            # Environment architecture
│   ├── ops/
│   │   └── STAGING_SETUP_GUIDE.md # Staging setup guide
│   ├── ARCHITECTURE.md            # System architecture
│   ├── CONTRIBUTING.md            # Contribution guidelines
│   ├── setup_local.md             # Local setup guide
│   └── ...                        # 50+ documentation files
│
├── config/
│   └── env.schema.yaml            # Environment variable schema
│
├── .env.example                   # Environment variables template
├── requirements.txt               # Root Python dependencies
├── package.json                   # Root Node.js configuration
└── README.md                      # Project overview
```

**Detailed Structure**: See [PROJECT_STRUCTURE_REPORT.md](PROJECT_STRUCTURE_REPORT.md)

### Phase API Modules (Root Directory)

**Status**: ✅ **Intentional Cross-Cutting Architecture**

The following 18 production backend modules are located in the root directory as cross-cutting concerns:

**Core Managers**:
- **`persistent_state_manager.py`** (495 lines): State management across services
- **`security_manager.py`** (364 lines): Security operations and governance
- **`knowledge_graph_manager.py`** (1,018 lines): Knowledge graph operations

**Phase API Modules**:
- **`phase4_meta_agent_api.py`** (16,874 bytes): Meta-agent coordination (OODA loop, AI governance)
- **`phase5_data_intelligence_api.py`** (21,472 bytes): Data intelligence (QuickSight, growth marketing, BI dashboards)
- **`phase6_security_governance_api.py`** (18,234 bytes): Security & governance (Zero Trust, SecurityReviewer Agent, HITL analysis)
- **`phase6_startup.py`**, **`phase7_startup.py`**: Phase initialization

**Import Evidence**: These modules are actively imported in:
- `handoff/20250928/40_App/api-backend/src/main.py` (main application)
- `handoff/20250928/40_App/api-backend/tests/` (16+ test files)
- `handoff/20250928/40_App/orchestrator/` (orchestrator services)

**Architecture Rationale**: Root-level placement enables shared access across multiple services (api-backend, orchestrator, agents) without circular dependencies. This is an intentional design pattern for cross-cutting concerns, not a code organization issue.

---

## Important Documentation

### Core Documentation

- **[Project Structure Report](./PROJECT_STRUCTURE_REPORT.md)**: Comprehensive overview of repository structure
- **[Environments Guide](./ENVIRONMENTS.md)**: Environment architecture and deployment
- **[Contributing Guide](./CONTRIBUTING.md)**: Contribution guidelines and workflows
- **[Terminology Standards](./TERMINOLOGY.md)**: Standardized application names and user types

### Security & Operations

- **[Secret Rotation Policy](./SECRET_ROTATION_POLICY.md)**: Quarterly secret rotation procedures, SLOs, and drills
- **[Secret Scanning Guide](./SECRET_SCANNING_GUIDE.md)**: Prevention of secret exposure in code
- **[Test Coverage Improvement Plan](./TEST_COVERAGE_IMPROVEMENT_PLAN.md)**: 12-week roadmap to 60%+ coverage

### Quick Reference

**Environment Schema Operations**:
```bash
# Generate .env.example files from schema
python scripts/generate-env-examples.py

# Check for drift
python scripts/check-env-drift.py

# Verify secret inventory
python scripts/verify_secret_inventory.py
```

**Testing & Coverage**:
```bash
# Backend tests with coverage
cd handoff/20250928/40_App/api-backend
pytest --cov=src --cov-report=term-missing

# Frontend tests with coverage
cd handoff/20250928/40_App/frontend-dashboard
pnpm test:coverage
```

### Getting Started
- **[Local Setup Guide](setup_local.md)** - Quick start and troubleshooting
- **[Environment Architecture](ENVIRONMENTS.md)** - Complete environment documentation
- **[Staging Setup Guide](ops/STAGING_SETUP_GUIDE.md)** - Staging environment setup

### Development
- **[Contributing Guidelines](CONTRIBUTING.md)** - Development rules and workflows
- **[CI/CD Matrix](ci_matrix.md)** - GitHub Actions workflows
- **[Environment Variables](config/env_schema.md)** - Configuration documentation

### Architecture
- **[System Architecture](ARCHITECTURE.md)** - Overall system design
- **[Agent Sandbox Architecture](agent-sandbox-architecture.md)** - Sandbox design
- **[Governance Framework](GOVERNANCE_FRAMEWORK.md)** - Multi-agent governance

### UI/UX
- **[UI/UX Quick Start](UI_UX_QUICKSTART.md)** - 5-minute quick start
- **[UI/UX Cheat Sheet](UI_UX_CHEATSHEET.md)** - One-page reference
- **[UI/UX Resources](UI_UX_RESOURCES.md)** - Design system resources

### Security
- **[Redis Security](REDIS_SECURITY.md)** - Redis security requirements
- **[RLS Implementation](RLS_IMPLEMENTATION_GUIDE.md)** - Row-level security
- **[Secret Scanning](SECRET_SCANNING_GUIDE.md)** - Secret management
- **[Authentication API](openapi.auth.yaml)** - 2FA/TOTP endpoints (OpenAPI 3.0.3)

### Testing
- **[Testing Guide](TESTING.md)** - Comprehensive testing documentation
- **[Phase 3 Testing](PHASE3_TESTING_GUIDE.md)** - Phase 3 testing guide

#### Visual Regression Testing (VRT)

**Status:** ✅ Re-enabled November 2025 (PR #1288; related: #1287 frontend tests, #1293 Storybook test-runner)

**What is VRT?**
- Automated visual comparison of UI screenshots
- Detects unintended visual changes
- Uses Playwright for browser automation

**Running VRT Tests:**
```bash
cd handoff/20250928/40_App/frontend-dashboard

# Run VRT tests
pnpm test:vrt

# Update snapshots (after intentional UI changes)
pnpm test:vrt --update-snapshots
```

**CI Integration:**
- VRT runs automatically on PRs via `.github/workflows/frontend.yml`
- Snapshots stored in `tests/vrt.spec.ts-snapshots/`
- Failures indicate visual regressions - review carefully before updating

**Configuration:** `playwright.config.ts` - VRT-specific settings

**Troubleshooting:**
- If VRT fails after intentional UI changes, update snapshots locally and commit
- Ensure consistent browser/OS for snapshot generation (CI uses Ubuntu + Chromium)

---

## Observability & Monitoring

### Monitoring Dashboard v2

MorningAI provides a real-time monitoring dashboard with intelligent degradation handling and graceful fallback behavior. The dashboard displays system health, metrics, and alerts with explicit markers when services are unavailable.

**Key Features**:
- Real-time metrics from Redis and Database
- Graceful degradation with explicit fallback markers
- 503 Service Unavailable when both Redis and DB fail
- Public endpoint (no authentication required)

### API Endpoints

#### Primary Endpoint (Recommended)
- **Path**: `/api/phase7/monitoring/dashboard`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ✅ Production Ready
- **Documentation**: [OpenAPI Schema](../handoff/20250928/40_App/owner-console/src/lib/openapi.yaml)

#### Legacy Endpoint (Deprecated)
- **Path**: `/api/dashboard/data`
- **Method**: GET
- **Auth**: Public (no JWT required)
- **Status**: ⚠️ **DEPRECATED** - Use `/api/phase7/monitoring/dashboard` instead
- **Migration**: Update API calls to use new endpoint for real-time metrics with degradation markers

### Degradation Behavior

The monitoring dashboard implements intelligent degradation semantics:

| Scenario | HTTP Status | Response Behavior |
|----------|-------------|-------------------|
| **All services healthy** | 200 OK | Full metrics with real data from Redis and DB |
| **Redis unavailable** | 200 OK | Fallback metrics with `available: false`, `source: 'fallback'`, `error: 'Redis unavailable'` |
| **Database unavailable** | 200 OK | `overall_status: 'degraded'` with critical alert |
| **Both Redis + DB unavailable** | 503 Service Unavailable | `ServiceUnavailableError` response |

**Example Response (Normal)**:
```json
{
  "system_health": {
    "overall_status": "healthy",
    "error_rate": 0.01,
    "avg_latency": 0.15,
    "open_circuit_breakers": 0
  },
  "metrics": {
    "queue_depth": {
      "current": 5,
      "unit": "tasks",
      "trend": "stable"
    }
  },
  "agents": [],
  "alerts": []
}
```

**Example Response (Redis Degraded)**:
```json
{
  "system_health": {
    "overall_status": "healthy"
  },
  "metrics": {
    "queue_depth": {
      "current": 0,
      "unit": "tasks",
      "trend": "unknown",
      "available": false,
      "source": "fallback",
      "error": "Redis unavailable"
    }
  },
  "alerts": [
    {
      "id": "redis_error",
      "severity": "warning",
      "message": "Redis connection unavailable",
      "timestamp": "2025-11-04T16:45:58.648953"
    }
  ]
}
```

**Example Response (503 Dual Failure)**:
```json
{
  "error": "Core services unavailable",
  "message": "Both Redis and Database connections failed",
  "status": "service_unavailable",
  "request_id": "optional-trace-id"
}
```

### Error Schema

**ServiceUnavailableError** (503 responses):
```typescript
{
  error: string;        // Error message
  message?: string;     // Detailed message
  status: 'service_unavailable';
  request_id?: string;  // Optional trace ID for observability
}
```

See [OpenAPI Schema](../handoff/20250928/40_App/owner-console/src/lib/openapi.yaml) for complete API contract.

### Code Locations

**Backend Implementation**:
- **Main Route**: `handoff/20250928/40_App/api-backend/src/main.py:574` (`get_monitoring_dashboard`)
- **Core Logic**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:35` (`get_dashboard_data`)
- **DB Health Check**: `handoff/20250928/40_App/api-backend/src/routes/dashboard.py:17` (`check_db_health`)

**Frontend & Types**:
- **OpenAPI Schema**: `handoff/20250928/40_App/owner-console/src/lib/openapi.yaml`
- **Generated Types**: `handoff/20250928/40_App/owner-console/src/lib/generated/owner-console-api.ts`
- **Type Generation**: `npm run generate:api` (uses orval)

**Tests**:
- **Integration Tests**: `handoff/20250928/40_App/api-backend/tests/test_dashboard_503_integration.py`
- **Test Seam**: `check_db_health()` function enables mocking DB failures without Flask app context issues

### Developer Workflows

**Regenerating TypeScript Types**:
```bash
cd handoff/20250928/40_App/owner-console
npm run generate:api
```

**Note**: The generated types include `@deprecated` markers for the legacy endpoint. These are manually added post-generation. If you regenerate types, ensure deprecated markers are preserved.

**Running Integration Tests**:
```bash
cd handoff/20250928/40_App/api-backend
pytest tests/test_dashboard_503_integration.py -v
```

### Environment Variables

The monitoring dashboard requires:
- `REDIS_URL`: Redis connection string (for queue metrics)
- `DATABASE_URL`: PostgreSQL connection string (for health checks)
- `BACKEND_SERVICES_AVAILABLE`: Gate flag (set by `src/main.py`)

See [Environment Variables Schema](../config/env.schema.yaml) for complete list.

### Troubleshooting

For monitoring-specific troubleshooting, see:
- **[Monitoring Troubleshooting Guide](deployment/troubleshooting-monitoring.md)** - 503 error diagnosis and recovery

**Quick Checks**:
```bash
# Test monitoring endpoint
curl https://morningai-backend-v2-stg.onrender.com/api/phase7/monitoring/dashboard

# Expected: 200 OK with metrics or 503 if both services down
```

---

## Testing

MorningAI 採用**雙層測試架構**，將單元測試和 API 整合測試分離。

### 測試架構概覽

| 層級 | 位置 | 目的 | 覆蓋率 | CI Workflow |
|------|------|------|--------|-------------|
| **層級 1** | `/tests/` | 單元測試（業務邏輯） | 21% | test-apps.yml |
| **層級 2** | `/handoff/.../api-backend/tests/` | API 整合測試 | 74% | backend.yml |

**詳細說明**: 見 [TESTING_ARCHITECTURE.md](./TESTING_ARCHITECTURE.md)

### 運行根目錄單元測試

```bash
# 在專案根目錄
pytest tests/ -v

# 帶覆蓋率
pytest tests/ --cov=src --cov-report=html

# 特定測試
pytest tests/test_utils_redis_client.py -v
```

### 運行後端 API 測試

```bash
# 1. 進入後端目錄
cd handoff/20250928/40_App/api-backend

# 2. 安裝依賴（如果還沒安裝）
pip install -r requirements.txt
pip install pytest pytest-cov

# 3. 設置環境變數
export TESTING=true
export JWT_SECRET_KEY=test-secret

# 4. 運行測試
python -m pytest tests/ -v

# 5. 帶覆蓋率
python -m pytest tests/ --cov=src --cov-report=html
```

### 為什麼測試分離？

1. **依賴隔離**: 根目錄只需最小依賴，後端需要完整依賴（Flask, rq, numpy 等）
2. **覆蓋率基準分離**: 21% 單元測試 vs 74% API 測試
3. **測試速度**: 單元測試快速（< 1 秒），API 測試較慢（1-5 秒）

**常見問題**: 見 [TESTING_ARCHITECTURE.md](./TESTING_ARCHITECTURE.md#常見問題)

---

## Common Tasks

### Running Tests

#### Backend Tests

**Prerequisites**:

The project uses **PyJWT** for JWT token handling. Make sure you have the correct package installed:

```bash
# Install PyJWT (NOT jwt==1.4.0)
pip install PyJWT
```

**Important:** Do NOT install `jwt==1.4.0` as it conflicts with PyJWT. If you have `jwt` installed, uninstall it first:

```bash
pip uninstall jwt
pip install PyJWT
```

**Running Unit Tests**:

```bash
cd handoff/20250928/40_App/api-backend
source ../../../../.venv/bin/activate

# Run all unit tests
pytest -v

# Run specific test files
pytest tests/test_middleware_auth.py -v
pytest tests/test_middleware_auth_decorators.py -v

# Run with coverage
pytest tests/test_middleware_auth*.py --cov=handoff/20250928/40_App/api-backend/src/middleware/auth_middleware.py --cov-report=term

# Run all unit tests with coverage
pytest tests/test_middleware_auth*.py tests/test_scripts_*.py --cov=src --cov-report=term --cov-report=xml --cov-report=json
```

**Test Environment Variables**:

For unit tests, set:
```bash
export TESTING=true
```

For migration idempotency tests:
```bash
export IDEMPOTENCY_TESTS_ALLOWED=true
```

**Note:** RLS tests require Supabase credentials and should not be run by default. See [DATABASE_ARCHITECTURE.md](DATABASE_ARCHITECTURE.md) for details.

**Coverage Targets**:
- **Overall**: 74% (enforced by CI)
- **Security-critical modules** (auth_middleware.py): ≥70%

**Frontend Tests**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm test
```

**Coverage Report**:
```bash
pytest --cov=src --cov-report=html
# Open htmlcov/index.html in browser
```

### Linting and Formatting

**Backend**:
```bash
# Lint
flake8 .

# Format
black .
```

**Frontend**:
```bash
# Lint
pnpm lint

# Format
pnpm format
```

### Database Migrations

✅ **Alembic Migration Framework**: MorningAI uses Alembic for database schema version control and migrations.

**Quick Start**:
```bash
cd handoff/20250928/40_App/api-backend

# Run all pending migrations
alembic upgrade head

# Check current migration version
alembic current

# View migration history
alembic history --verbose

# Create new migration (auto-generate from model changes)
alembic revision --autogenerate -m "Description of changes"
```

**Helper Script**:
```bash
# Use the migration helper script
./scripts/run_alembic_migrations.sh upgrade    # Apply migrations
./scripts/run_alembic_migrations.sh current    # Check version
./scripts/run_alembic_migrations.sh history    # View history
./scripts/run_alembic_migrations.sh revision "Add new table"  # Create migration
```

**Configuration**:
- **Alembic Config**: `alembic.ini`
- **Environment Setup**: `alembic/env.py` (auto-loads DATABASE_URL from environment)
- **Migrations Directory**: `alembic/versions/`
- **Models**: `src/models/` (SQLAlchemy models)

**CI/CD Integration**:
- Migrations are automatically validated in CI against PostgreSQL
- GitHub Actions workflow: `.github/workflows/alembic-check.yml`
- Both PostgreSQL and SQLite migrations are tested

**Legacy Migrations**:
Manual SQL files in `migrations/` directory are for historical reference only. All new schema changes should use Alembic.

### Checking Service Health

**Production**:
```bash
curl https://morningai-backend-v2.onrender.com/healthz
curl https://morningai-orchestrator-api.onrender.com/health
```

**Staging**:
```bash
curl https://morningai-backend-v2-stg.onrender.com/healthz
curl https://morningai-orchestrator-api-stg.onrender.com/health
```

**Local**:
```bash
curl http://localhost:8000/healthz
curl http://localhost:8001/health
```

### Viewing Logs

**Render Logs**:
- Go to https://dashboard.render.com/
- Select service
- Click "Logs" tab

**Sentry Errors**:
- Go to https://sentry.io/organizations/morningai/issues/
- Filter by environment (production/staging)

**Local Logs**:
- Check terminal output where services are running

---

## Troubleshooting

### Issue: Backend won't start

**Symptoms**: `ModuleNotFoundError`, `ImportError`

**Solutions**:
```bash
# Ensure virtual environment is activated
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt

# Check Python version
python --version  # Should be 3.12+
```

### Issue: Frontend won't start

**Symptoms**: `Cannot find module`, build errors

**Solutions**:
```bash
# Reinstall dependencies
pnpm install

# Clear cache
rm -rf node_modules .next
pnpm install

# Check Node version
node --version  # Should be 20+
```

### Issue: Database connection fails

**Symptoms**: `Connection refused`, `Authentication failed`

**Solutions**:
```bash
# Check DATABASE_URL format
echo $DATABASE_URL
# Should be: postgresql://user:pass@host:port/db

# Test connection
python -c "from sqlalchemy import create_engine; engine = create_engine('$DATABASE_URL'); print(engine.connect())"

# Use staging database instead
# Get DATABASE_URL from team lead
```

### Issue: Redis connection fails

**Symptoms**: `Connection refused`, `WRONGPASS`

**Solutions**:
```bash
# Check REDIS_URL format
echo $REDIS_URL
# Should be: redis://localhost:6379/0 or rediss://...

# Test connection
python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"

# Use staging Redis instead
# Get REDIS_URL from team lead
```

### Issue: Tests failing

**Symptoms**: Test failures, coverage below threshold

**Solutions**:
```bash
# Run tests with verbose output
pytest -v

# Check specific test
pytest tests/test_specific.py -v

# Update test data/fixtures
# Check test documentation
```

### Issue: CI/CD failing

**Symptoms**: GitHub Actions workflow fails

**Solutions**:
1. Check workflow logs in GitHub Actions tab
2. Verify all required secrets are set in repository settings
3. Check if tests pass locally
4. Review recent commits for breaking changes

### Issue: Tailwind v4 max-w-* utilities not working correctly

**Symptoms**: 
- Container widths collapse to 16px instead of expected rem values (e.g., max-w-md should be 28rem/448px but renders as 16px)
- All `max-w-*` utilities affected (sm, md, lg, xl, 2xl, 3xl, 4xl, 5xl, 6xl, 7xl)
- Layout appears vertically compressed and unusable
- Issue only appears on Vercel preview deployments (not local dev due to different build optimizations)

**Root Cause**: Tailwind v4's `@theme` syntax incorrectly maps `max-w-*` utilities to `--spacing-*` tokens which are intended for padding/margin, not container widths.

**Technical Details**:
In `theme.css`, we defined:
```css
--spacing-md: var(--space-md);  /* 16px from shared-ui */
```

Tailwind v4 then incorrectly generated:
```css
.max-w-md { max-width: var(--spacing-md); }  /* 16px - WRONG! */
```

But `max-w-md` should be:
```css
.max-w-md { max-width: 28rem; }  /* 448px - CORRECT */
```

**Solution**: The fix is already implemented in `owner-console/src/styles/theme.css`:
- Separate `--max-width-*` tokens are defined (lines 24-35)
- These tokens use correct rem values:
  - `--max-width-sm: 24rem` (384px)
  - `--max-width-md: 28rem` (448px)
  - `--max-width-lg: 32rem` (512px)
  - `--max-width-xl: 36rem` (576px)
  - `--max-width-2xl: 42rem` (672px)
  - `--max-width-3xl: 48rem` (768px)
  - `--max-width-4xl: 56rem` (896px)
  - `--max-width-5xl: 64rem` (1024px)
  - `--max-width-6xl: 72rem` (1152px)
  - `--max-width-7xl: 80rem` (1280px)
- Tailwind v4 now uses these dedicated tokens instead of spacing tokens
- Clean separation of concerns: spacing tokens (padding/margin) vs. container width tokens

**Verification**:
```bash
# 1. Run the regression test
cd handoff/20250928/40_App/owner-console
npm run test:e2e -- max-width-regression.spec.ts

# 2. Build and check compiled CSS
npm run build
grep "max-w-md" dist/assets/index-*.css
# Should show: .max-w-md{max-width:var(--max-width-md)}

# 3. Check computed styles in browser DevTools
# Open login page, inspect element with max-w-md class
# Computed maxWidth should be 448px (not 16px)
```

**If Issue Persists**:
1. Clear build cache: `rm -rf dist node_modules/.vite`
2. Reinstall dependencies: `pnpm install`
3. Rebuild: `pnpm build`
4. Check that `theme.css` contains `--max-width-*` tokens
5. Verify no CSS overrides in `index.css` (hotfix was removed in PR #1308)

**Related Documentation**:
- **Detailed tracking doc**: `docs/TAILWIND_V4_MAX_WIDTH_ISSUE.md` (comprehensive 259-line analysis)
- **PR #1303**: Initial hotfix with CSS overrides
- **PR #1308**: Root cause fix with dedicated --max-width-* tokens
- **Regression test**: `e2e/max-width-regression.spec.ts`

**Risk Note**: Tailwind v4 token resolution behavior is based on observation, not official documentation. Future Tailwind v4 versions may change this behavior. Monitor for updates when upgrading Tailwind.

---

## Getting Help

### Internal Resources

**Documentation**:
- Check the `docs/` directory for comprehensive documentation
- Search for specific topics in documentation

**Team Communication**:
- **Slack**: #morningai-dev channel
- **GitHub Issues**: Report bugs or request features
- **GitHub Discussions**: Ask questions or share ideas

**Code Review**:
- Request review from team members on PRs
- Tag specific reviewers for domain expertise

### External Resources

**Technologies**:
- **Flask**: https://flask.palletsprojects.com/
- **React**: https://react.dev/
- **Supabase**: https://supabase.com/docs
- **Render**: https://render.com/docs

**Learning**:
- **Python**: https://docs.python.org/3/
- **TypeScript**: https://www.typescriptlang.org/docs/
- **PostgreSQL**: https://www.postgresql.org/docs/

### Contact

**Team Lead**: Ryan Chen (@RC918)
**Email**: ryan2939z@gmail.com
**GitHub**: https://github.com/RC918/morningai

---

## Next Steps

After completing this onboarding guide, you should:

1. ✅ **Set up your local development environment**
2. ✅ **Run all services locally and verify they work**
3. ✅ **Read the key documentation** (ENVIRONMENTS.md, CONTRIBUTING.md)
4. ✅ **Create your first feature branch**
5. ✅ **Make a small change and create a PR to develop**
6. ✅ **Test your change on staging**
7. ✅ **Join team communication channels**
8. ✅ **Review open issues and pick your first task**

**Welcome to the team! Happy coding!** 🚀

---

**Last Updated**: 2025-11-16  
**Version**: 1.2.0  
**Maintained By**: CTO / DevOps Team

**Changelog**:
- 2025-11-16 (v1.2.0): Updated current status with test coverage numbers, added agent evaluation harness documentation, linked to strategic roadmap reality comparison
- 2025-11-03 (v1.1.0): Previous update
