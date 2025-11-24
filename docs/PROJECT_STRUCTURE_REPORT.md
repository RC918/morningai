# MorningAI Project Structure Report

> 📚 **相關文件**: 
> - [術語對照表](./TERMINOLOGY.md) - 標準化的應用名稱和用戶類型定義
> - [Onboarding Guide](./ONBOARDING_GUIDE.md) - 新人入職指南和環境設置
> - [README](../README.md) - 專案概覽和快速導航
> - [環境變數 Schema](../config/env.schema.yaml) - 環境變數配置的單一真源

**Document Version**: 1.7.0  
**Last Updated**: 2025-11-23  
**Project Phase**: Phase 1-2 實施中 (LLM Planner + Code Generation Workflow)  
**Test Coverage**: 59.89% (Owner Console), 74%+ (Backend)  
**Recent Activity**: 192 commits on main (2025-11-12 至 2025-11-23，快照值截至 2025-11-23)  
**Strategic Roadmap**: [Reality Comparison Report](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md) (Nov 16, 2025)

**Recent PRs (Nov 18-23, 2025)**:
- **PR #1350** (Merged): E2E Testing Infrastructure - 32 Playwright tests, route handler isolation, API mocking
- **PR #1398** (Merged): Production Path Discovery - `MORNINGAI_REPO_PATH` env var, 4-layer fallback
- **PR #1399** (Merged): Backend Test Environment - Python 3.12, Redis service, PyJWT conflict resolution
- **PR #1480** (Merged): Pydantic Alias System - 23 critical environment variable aliases (Nov 23)
- **PR #1452** (Merged): Redis Mapping Sanitization - Prevent NoneType DataError (Nov 23)
- **PR #1455** (Merged): AgentExecutionLogs Accessibility - 6 critical a11y violations resolved (Nov 23)
- **PR #1437** (Merged): i18n Error Fixes - 10 i18n errors fixed in owner-console (Nov 23)

---

## Executive Summary

This document provides a comprehensive overview of the MorningAI project structure, including directory organization, key files, architecture patterns, and deployment configurations. This report is updated to reflect the latest staging environment setup completed on 2025-10-28.

---

## Table of Contents

1. [Repository Overview](#repository-overview)
2. [Directory Structure](#directory-structure)
3. [Core Systems](#core-systems)
4. [Environment Configuration](#environment-configuration)
5. [Deployment Architecture](#deployment-architecture)
6. [Key Files Reference](#key-files-reference)
7. [Development Workflows](#development-workflows)
8. [Testing Infrastructure](#testing-infrastructure)
9. [Documentation Structure](#documentation-structure)
10. [Maintenance Guidelines](#maintenance-guidelines)

---

## Repository Overview

### Basic Information

- **Repository**: https://github.com/RC918/morningai
- **Primary Language**: Python (Backend), TypeScript (Frontend)
- **Package Manager**: pnpm 9.15.1 (Frontend), pip (Backend)
- **Monorepo**: Yes (using pnpm workspaces + Turbo 2.5.8)
- **License**: Proprietary
- **Team Size**: Small (1-3 developers)

### Repository Statistics

- **Total Lines of Code**: ~100,000+
- **Documentation Files**: 50+
- **GitHub Actions Workflows**: 15+
- **Test Coverage**: 
  - **Owner Console**: 59.89% lines, 45.76% branches (32 E2E tests, 218 unit tests)
  - **Backend**: 74%+ (超過目標，CI 環境已修復)
  - **Target**: 80% by Q2 2026
- **Active Branches**: `main` (production), `develop` (staging)
- **Recent Activity**: 116 commits in past 9 days (2025-11-12 至 2025-11-21)
- **CI Status**: All workflows passing (backend.yml, test-apps.yml unified)

### Technology Stack

**Backend**:
- Python 3.12 (unified across all CI workflows as of PR #1399)
- Flask
- SQLAlchemy
- PostgreSQL (Supabase)
- Redis (Upstash, with health checks in CI)
- RQ (Redis Queue)
- pytest + pytest-cov (74%+ coverage)

**Frontend**:
- React 19.1.0
- TypeScript 5.9
- Vite 6
- Tailwind CSS 4.1.7
- Custom Design System
- Playwright (E2E testing, 32 tests passing)
- Vitest + React Testing Library (unit testing)

**Infrastructure**:
- Render (Backend hosting)
- Vercel (Frontend hosting)
- Fly.io (Agent sandboxes)
- Supabase (Database)
- Upstash (Redis)
- GitHub Actions (CI/CD)

---

## Directory Structure

### Root Level

```
morningai/
├── .github/                    # GitHub configuration
├── .fly-web/                   # Fly.io deployment config
├── agents/                     # AI agent implementations
├── orchestrator/               # Task orchestration system (FastAPI)
├── handoff/                    # Handoff deliverables (⚠️ DO NOT IMPORT - vendor/design only)
├── docs/                       # Documentation
├── config/                     # Configuration files (env.schema.yaml is SSOT)
├── scripts/                    # Utility scripts (env generation, drift check, secret verification, system state verification)
├── packages/                   # Shared packages (shared-ui for cross-app components)
├── tests/                      # Root-level tests
├── tools/                      # Development tools
│   └── agent_eval/            # Agent evaluation harness (NEW: 2025-11-16)
├── phase4_meta_agent_api.py   # Phase 4 API module (imported by backend)
├── phase5_data_intelligence_api.py  # Phase 5 API module (imported by backend)
├── phase6_security_governance_api.py  # Phase 6 API module (imported by backend)
├── phase6_startup.py          # Phase 6 initialization (imported by backend)
├── phase7_startup.py          # Phase 7 initialization (imported by backend)
├── .env.example               # Environment variables template
├── .gitignore                 # Git ignore rules
├── package.json               # Root package.json (pnpm workspace)
├── pnpm-workspace.yaml        # pnpm workspace configuration
├── requirements.txt           # Python dependencies
├── README.md                  # Project overview
└── turbo.json                 # Turbo configuration
```

### Phase API Modules (Root Directory)

**Location**: Root directory (`/`)

**Status**: ✅ **Intentional Cross-Cutting Architecture - Actively Used**

The following 18 production backend modules are located in the root directory as cross-cutting concerns shared across multiple services:

**Core Managers** (Shared Infrastructure):
- **`persistent_state_manager.py`** (495 lines): State management across services
  - Location: `/persistent_state_manager.py`
  - Imported by: `handoff/20250928/40_App/api-backend/src/main.py`, multiple test files
  
- **`security_manager.py`** (364 lines): Security operations and governance
  - Location: `/security_manager.py`
  - Imported by: `handoff/20250928/40_App/api-backend/tests/`, orchestrator services
  
- **`knowledge_graph_manager.py`** (1,018 lines): Knowledge graph operations
  - Location: `/knowledge_graph_manager.py`
  - Imported by: agent services, test files

**Phase API Modules** (Feature Implementations):
- **`phase4_meta_agent_api.py`** (16,874 bytes): Meta-agent coordination API
  - Implements OODA loop (Observe, Orient, Decide, Act)
  - LangGraph workflow engine integration
  - AI governance console
  - Imported by: `main.py`, test files
  
- **`phase5_data_intelligence_api.py`** (21,472 bytes): Data intelligence and BI API
  - QuickSight integration
  - Growth marketing engine
  - Referral programs
  - Business intelligence dashboards
  - Imported by: `main.py`, test files
  
- **`phase6_security_governance_api.py`** (18,234 bytes): Security and governance API
  - Zero Trust security model
  - SecurityReviewer Agent
  - HITL (Human-in-the-Loop) security analysis
  - Security audit system
  - Imported by: `main.py`, test files
  
- **`phase6_startup.py`**: Phase 6 initialization script
  - Imported by: test files, initialization sequences
  
- **`phase7_startup.py`**: Phase 7 initialization script
  - Imported by: `main.py:450`, test files

**Import Evidence** (16+ locations):
- `handoff/20250928/40_App/api-backend/src/main.py` - Main application imports
- `handoff/20250928/40_App/api-backend/tests/test_*.py` - 16+ test files import these modules
- `handoff/20250928/40_App/orchestrator/` - Orchestrator services use managers

**Architecture Rationale**: Root-level placement enables shared access across multiple services (api-backend, orchestrator, agents) without circular dependencies. This is an intentional design pattern for cross-cutting concerns that need to be imported by multiple independent services. Moving these to a subdirectory would require complex PYTHONPATH management or package restructuring.

**Verification**: Run `grep -r "from persistent_state_manager\|from security_manager\|from phase[4-7]" handoff/20250928/40_App/` to see active imports.

### GitHub Configuration (`.github/`)

```
.github/
├── workflows/                 # CI/CD workflows
│   ├── backend.yml           # Backend CI (pytest + coverage, Python 3.12, Redis service)
│   ├── test-apps.yml         # App Tests (API Backend, Orchestrator, Frontend - unified with backend.yml as of PR #1399)
│   ├── frontend.yml          # Frontend CI (build + lint + E2E tests)
│   ├── staging-deploy.yml    # Staging deployment
│   ├── agent-mvp-e2e.yml     # Agent E2E tests
│   ├── ops-agent-sandbox-e2e.yml  # Ops agent E2E tests
│   ├── post-deploy-health-assertions.yml  # Health checks
│   ├── auto-merge-faq.yml    # Auto-merge FAQ PRs
│   ├── pr-guard.yml          # Design/Engineering PR separation
│   ├── dependency-check.yml  # Dependency validation
│   └── ...                   # 15+ workflows total
│
├── ISSUE_TEMPLATE/           # Issue templates
│   ├── rfc.md               # RFC template for API changes
│   ├── phase1-session-state-ooda.md
│   ├── phase2-ops-agent-enhancement.md
│   └── phase3-security-documentation.md
│
├── projects/                 # GitHub Projects
│   ├── phase9-10-mvp.yml    # Phase 9-10 roadmap
│   └── cto-strategic-roadmap-q4-2025-q2-2026.yml
│
└── scripts/                  # Automation scripts
    ├── audit_workflows.sh    # Workflow security audit
    └── check_heartbeat.py    # Redis worker health check
```

### Agents Directory (`agents/`)

```
agents/
├── dev_agent/               # Development agent
│   ├── __init__.py
│   ├── dev_agent.py        # Bug fixing and PR creation
│   └── README.md           # Dev agent documentation
│
├── ops_agent/              # Operations agent
│   ├── __init__.py
│   ├── ops_agent.py        # Incident response and monitoring
│   └── README.md           # Ops agent documentation
│
├── pm_agent.py             # Project management agent
├── growth_strategist.py    # Business strategy agent
└── meta_agent_decision_hub.py  # Agent orchestration (OODA loop)
```

### Orchestrator Directory (`orchestrator/`)

```
orchestrator/
├── api/                    # FastAPI application
│   ├── __init__.py
│   ├── main.py            # Application entry point
│   └── auth.py            # JWT authentication
│
├── task_queue/            # Task queue management
│   ├── __init__.py
│   └── redis_queue.py     # Redis queue implementation
│
├── sandbox/               # Agent sandbox
│   └── ops_agent_sandbox.py
│
├── mcp/                   # Management Control Plane
│   ├── server.py          # MCP server
│   └── mcp_client.py      # MCP client
│
├── graph.py               # Task graph orchestration
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
└── .env.example          # Environment variables template
```

### Handoff Directory (`handoff/20250928/40_App/`)

⚠️ **IMPORTANT**: The `handoff/` directory contains vendor deliverables and design assets from the initial project handoff. **DO NOT import or run code from this directory**. It is excluded from CI paths-ignore and should be treated as reference/archive material only.

The production applications are located within this directory but are the only active code:

```
handoff/20250928/40_App/
├── api-backend/           # Backend API
│   ├── src/              # Source code
│   │   ├── main.py       # Flask application
│   │   ├── database.py   # Database connection
│   │   ├── models/       # SQLAlchemy models
│   │   ├── routers/      # API routers
│   │   └── ...           # Other modules
│   │
│   ├── alembic/          # Database migrations (Alembic 1.13.1)
│   │   ├── versions/     # Migration files
│   │   │   └── 91b9a61fcafa_initial_baseline_migration.py
│   │   ├── env.py        # Alembic environment config
│   │   ├── script.py.mako  # Migration template
│   │   └── README        # Alembic documentation
│   │
│   ├── scripts/          # Utility scripts
│   │   ├── run_alembic_migrations.sh  # Migration helper
│   │   └── test_migration_data_insertion.py  # Integration test
│   │
│   ├── tests/            # Test suite
│   │   ├── test_database_connection.py
│   │   ├── test_phase4_6_comprehensive.py
│   │   └── ...           # 20+ test files
│   │
│   ├── alembic.ini       # Alembic configuration
│   ├── requirements.txt  # Python dependencies (includes Alembic==1.13.1)
│   ├── pytest.ini        # pytest configuration
│   └── .env.example      # Environment variables
│
├── frontend-dashboard/    # Frontend application
│   ├── src/              # Source code
│   │   ├── App.tsx       # Main application
│   │   ├── components/   # React components
│   │   │   ├── apple/    # Apple-inspired components
│   │   │   ├── ui/       # UI components
│   │   │   └── ...       # Other components
│   │   ├── pages/        # Page components
│   │   ├── hooks/        # Custom hooks
│   │   ├── utils/        # Utility functions
│   │   └── ...           # Other modules
│   │
│   ├── public/           # Static assets
│   ├── docs/             # Frontend documentation
│   ├── package.json      # Node.js dependencies
│   ├── vite.config.ts    # Vite configuration
│   ├── tsconfig.json     # TypeScript configuration
│   └── tailwind.config.js  # Tailwind CSS configuration
│
├── owner-console/        # Owner management console
│   ├── src/             # Source code
│   ├── e2e/             # E2E tests (Playwright, 32 tests - added PR #1350)
│   │   ├── auth.setup.ts           # Authentication setup
│   │   ├── agent-execution-logs.spec.ts  # 10 test cases
│   │   ├── system-monitoring.spec.ts     # 8 test cases
│   │   ├── trace-link-integration.spec.ts
│   │   └── utils/fixtures.ts       # API mocking and test utilities
│   ├── public/          # Static assets
│   ├── package.json     # Node.js dependencies
│   └── README.md        # Owner console documentation
│
└── orchestrator/        # Legacy orchestrator (⚠️ STILL USED BY WORKERS)
    └── ...              # Contains LangGraph implementation, used by RQ workers
```

### Tools Directory (`tools/`)

**NEW: 2025-11-16** - Development and evaluation tools

```
tools/
└── agent_eval/          # Agent evaluation harness
    ├── README.md        # Evaluation harness documentation
    ├── __init__.py      # Package initialization
    ├── dataset.jsonl    # Test cases (10 tasks: bug_fix, feature, refactor, test)
    ├── runner.py        # Evaluation runner (executable)
    ├── metrics.py       # Metrics calculator (executable)
    └── results/         # Evaluation results (gitignored)
```

**Purpose**: Provides measurable success rates for AI agent performance:
- **Task Completion Rate**: Percentage of tasks completed
- **Correctness Rate**: Percentage of correct solutions
- **CI Pass Rate**: Percentage of PRs passing CI
- **Time Efficiency**: Actual vs estimated time
- **Overall Success Rate**: Weighted combination

**Status**: ✅ Framework created, ✅ Dashboard integrated (Phase 1.5 #1337)
**Path**: `/home/ubuntu/repos/morningai/tools/agent_eval/`
**Dashboard**: `handoff/20250928/40_App/owner-console/src/pages/AgentEvaluationDashboard.jsx`

**Usage**:
```bash
# Run evaluation
cd tools/agent_eval
python runner.py --dataset dataset.jsonl --output results/latest.json

# View metrics
python metrics.py --results results/latest.json
```

**Integration**: Planned for Milestone 1 (Nov 23 - Dec 6, 2025). See [Strategic Roadmap Reality Comparison](./STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md).

### Documentation Directory (`docs/`)

```
docs/
├── ops/                  # Operations documentation
│   ├── STAGING_SETUP_GUIDE.md  # Staging setup guide
│   ├── staging-environment-plan.md
│   └── staging-backend-env-template.txt
│
├── architecture/         # Architecture documentation
│   └── decisions/       # Architecture Decision Records (ADRs)
│       ├── ADR-001-frontend-of-record.md
│       ├── ADR-002-orchestrator-roles.md
│       └── ADR-003-database-of-record.md
│
├── UX/                  # UI/UX documentation
│   ├── TYPOGRAPHY_SYSTEM.md
│   ├── COLOR_SYSTEM.md
│   ├── MATERIAL_SYSTEM.md
│   ├── SHADOW_SYSTEM.md
│   ├── SPACING_SYSTEM.md
│   └── ...              # 30+ UX documents
│
├── config/              # Configuration documentation
│   └── env_schema.md    # Environment variables schema
│
├── database/            # Database documentation
│   ├── MIGRATIONS.md    # Alembic migration guide (comprehensive)
│   └── migrations/      # Legacy migration documentation
│
├── faq/                 # FAQ documentation
├── coverage/            # Coverage reports
├── adr/                 # Architecture Decision Records
├── rfcs/                # Request for Comments
├── sandbox/             # Sandbox documentation
├── policy/              # Policy documentation
│
├── STRATEGIC_ROADMAP_REALITY_COMPARE_2025_11_16.md  # Strategic roadmap comparison (2025-11-16)
├── BACKEND_TEST_ENVIRONMENT_FIX.md  # Backend test fix documentation (2025-11-16)
├── ENVIRONMENTS.md      # Environment architecture (Updated: 2025-11-19)
├── PROJECT_STRUCTURE_REPORT.md  # Project structure report (Updated: 2025-11-19)
├── PROJECT_DEEP_ANALYSIS.md  # Deep analysis report (Updated: 2025-11-19)
├── ONBOARDING_GUIDE.md  # Onboarding guide (Updated: 2025-11-19)
├── ARCHITECTURE.md      # System architecture
├── CONTRIBUTING.md      # Contribution guidelines
├── GOVERNANCE_FRAMEWORK.md  # Agent governance
├── MONITORING_SETUP.md  # Monitoring setup
├── TESTING.md           # Testing documentation
├── setup_local.md       # Local setup guide
├── ci_matrix.md         # CI/CD workflows
└── ...                  # 50+ documentation files
```

### Configuration Directory (`config/`)

```
config/
└── env.schema.yaml      # Environment variables schema
```

---

## Core Systems

### 1. Agent System

**Location**: `agents/`

**Components**:
- **Dev_Agent** (`agents/dev_agent/dev_agent.py`)
  - Auto-reproduces bugs via LSP
  - Generates code fixes
  - Creates pull requests
  - Target: >85% fix success rate

- **Ops_Agent** (`agents/ops_agent/ops_agent.py`)
  - Handles incidents via runbooks
  - Performs log analysis
  - Root cause analysis
  - Predictive scaling
  - Target: >70% self-healing

- **PM_Agent** (`agents/pm_agent.py`)
  - Task tracking
  - Priority management
  - Agent coordination

- **Growth_Strategist** (`agents/growth_strategist.py`)
  - Business strategy
  - Growth metrics analysis

- **Meta_Agent** (`agents/meta_agent_decision_hub.py`)
  - Orchestrates all agents
  - Implements OODA loop
  - Routes tasks to appropriate agents

**Key Concepts**:
- **OODA Loop**: Observe → Orient → Decide → Act
- **Session State**: Long-term memory in PostgreSQL
- **Knowledge Graph**: Semantic search with pgvector embeddings (dimension 1536)
- **Learned Patterns**: Coding styles, bug patterns, fix patterns

**Vector Storage (pgvector)**: ✅ **IMPLEMENTED**
- **Location**: 
  - `migrations/010_create_embeddings_tables.sql` - Main embeddings tables
  - `agents/dev_agent/migrations/001_create_knowledge_graph_tables.sql` - Dev agent knowledge graph (136 lines)
  - `agents/faq_agent/migrations/001_create_faq_tables.sql` - FAQ agent embeddings (136 lines)
- **Migration Execution**:
  - **dev_agent**: Python runner at `agents/dev_agent/migrations/run_migration.py` with pre-checks and validation
  - **faq_agent**: Shell script at `agents/faq_agent/deploy.sh:32` executes `psql -f migrations/001_create_faq_tables.sql`
- **Runtime Usage**: `src/routes/vectors.py` - Vector visualization API (t-SNE, PCA, clustering, drift detection)
- **Dimension**: 1536 (OpenAI text-embedding-ada-002)
- **Status**: Production-ready with full API implementation

### 2. Backend API System

**Location**: `handoff/20250928/40_App/api-backend/`

**Architecture**: Phase-based API structure (Phases 4-8)

**Key Files**:
- `src/main.py`: Flask application entry point
- `src/database.py`: Database connection and session management
- `src/models/`: SQLAlchemy models
- `src/routers/`: API route handlers

**API Phases**:
- **Phase 4**: Meta-agent coordination
- **Phase 5**: Data intelligence and BI
- **Phase 6**: Security and governance
- **Phase 7**: Startup initialization
- **Phase 8**: Current production backend (v8.0.0)

**Endpoints**:
- `/healthz`: Health check with phase/version validation
- `/api/agent/faq`: FAQ generation (async task)
- `/api/agent/tasks/{task_id}`: Task status polling
- `/api/billing/plans`: Payment tier management
- `/api/security/reviews/pending`: JWT-protected security reviews
- `/api/phase7/monitoring/dashboard`: Real-time monitoring dashboard (public, no auth)
- `/api/dashboard/data`: Legacy dashboard endpoint (⚠️ deprecated)

**Monitoring API Surface**:
- **Primary Handler**: `src/main.py:574` (`get_monitoring_dashboard`) - Public endpoint registration
- **Core Logic**: `src/routes/dashboard.py:35` (`get_dashboard_data`) - Metrics collection with degradation
- **Test Seam**: `src/routes/dashboard.py:17` (`check_db_health`) - Mockable DB health check
- **Degradation Semantics**: 
  - Redis failure → 200 with fallback metrics (`available: false`, `source: 'fallback'`)
  - DB failure → 200 with degraded status + critical alert
  - Both failures → 503 ServiceUnavailableError
- **Integration Tests**: `tests/test_dashboard_503_integration.py` - Dual failure and degradation scenarios
- **OpenAPI Contract**: `owner-console/src/lib/openapi.yaml` (canonical API schema)
- **Generated Types**: `owner-console/src/lib/generated/owner-console-api.ts` (auto-generated via orval)

### 3. Orchestrator System

⚠️ **DUAL-MODE ORCHESTRATOR ARCHITECTURE** - Critical for understanding code organization

**Current State**: Single worker orchestrator with two execution modes sharing a common core.

#### Architecture Overview

The orchestrator uses a **dual-mode architecture** with a shared core executor:

```
API Backend → Redis Queue → Worker (Routing) → [Simple Mode | LangGraph Mode]
                                                       ↓              ↓
                                                  graph.execute (Shared Core)
```

**Key Insight**: `graph.py` is NOT just "legacy code" - it's the **shared execution engine** used by both modes.

| Component | Role | Traffic | Status | Path |
|-----------|------|---------|--------|------|
| **Simple Mode** | Direct execution | ~95% | Feature-frozen | `handoff/20250928/40_App/orchestrator/graph.py` |
| **LangGraph Mode** | Stateful workflows | ~5% | Active development | `handoff/20250928/40_App/orchestrator/langgraph_orchestrator.py` |
| **Shared Core** | Execution engine | 100% | Both modes | `handoff/20250928/40_App/orchestrator/graph.py:30-155` |
| **Routing Logic** | Mode selection | 100% | Canary deployment | `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-400` |

**Architecture**: Producer-consumer pattern with canary routing. API Backend enqueues tasks to Redis. Worker polls Redis and routes to Simple or LangGraph mode based on MD5 hash of task_id.

**Phase 1 參考配置**（實際配置請查看 Render Dashboard）:

| 服務 | USE_LANGGRAPH | USE_LANGGRAPH_PERCENT | USE_LLM_PLANNER |
|------|---------------|----------------------|-----------------|
| Staging Worker | `false` | `5` | `true` |
| Production Worker | `false` | `5` | `true` |

⚠️ **注意**：本文檔描述架構設計和政策。實際環境變數配置可能因運維需求調整。請以 Render Dashboard 的實際配置為準。

**Key Documentation**:
- [ONBOARDING_GUIDE.md - Orchestrator Architecture](./ONBOARDING_GUIDE.md#orchestrator-architecture) - Comprehensive guide for developers
- [ADR-001: Dual Orchestrator Architecture](./adr/001-dual-orchestrator-architecture.md) - Historical context
- [ADR-002: Producer-Consumer Architecture](./adr/002-producer-consumer-architecture.md) - Technical architecture
- [ADR-004: Shared Core Executor Pattern](./adr/004-shared-core-executor-pattern.md) - Design decision for shared execution engine
- [render.yaml](../render.yaml) - Deployment configuration

**Migration Roadmap**:
- **Phase 1** (Current): 5% LangGraph canary validation
- **Phase 2** (Q1 2026): Gradually increase to 100% LangGraph
- **Phase 3** (Q2 2026): Refactor `graph.py` to `core_executor.py` (Option A - Recommended)

#### 3.1 Mode 1: Simple Mode (Feature-Frozen, ~95% Traffic)

**Location**: `handoff/20250928/40_App/orchestrator/`

**Entry Point**: `redis_queue/worker.py:399` → `graph.py:execute()`

**Characteristics**:
- ✅ **Fast**: Direct execution, no state machine overhead
- ✅ **Stable**: Battle-tested, production-proven since 2025-Q3
- ✅ **Stateless**: No retry logic, no CI monitoring
- ❌ **Feature-frozen**: Only bug fixes accepted

**When Used**:
- `USE_LANGGRAPH=false` (default)
- Task's MD5 hash % 100 >= `USE_LANGGRAPH_PERCENT`

**Key Files**:
```
handoff/20250928/40_App/orchestrator/
├── redis_queue/worker.py:399        # Entry point: from graph import execute
├── graph.py:30-155                  # Shared executor (used by both modes!)
└── tests/test_graph.py              # Simple mode tests
```

**Development Policy**: **No new features**. All new orchestrator features must be implemented in LangGraph mode.

#### 3.2 Mode 2: LangGraph Mode (Active Development, ~5% Traffic)

**Location**: `handoff/20250928/40_App/orchestrator/`

**Entry Point**: `redis_queue/worker.py:396` → `langgraph_orchestrator.py:run_orchestrator()`

**Characteristics**:
- ✅ **Stateful**: Full state machine with LangGraph
- ✅ **Intelligent**: LLM-powered planning (when `USE_LLM_PLANNER=true`)
- ✅ **Resilient**: Retry logic, error handling, CI monitoring
- ✅ **Active Development**: New features go here

**When Used**:
- `USE_LANGGRAPH=true` (100% routing), OR
- `USE_LANGGRAPH=false` + Task's MD5 hash % 100 < `USE_LANGGRAPH_PERCENT`

**Workflow**:
```
Worker → langgraph_orchestrator.run_orchestrator()
  → planner_node (LLM or static)
  → executor_node → graph.execute()  # ← Uses shared core!
  → ci_monitor_node
  → fixer_node (if needed)
  → finalizer_node
```

**Key Files**:
```
handoff/20250928/40_App/orchestrator/
├── redis_queue/worker.py:396        # Entry point: from langgraph_orchestrator import run_orchestrator
├── langgraph_orchestrator.py        # LangGraph state machine
│   ├── planner_node (lines 76-104)  # LLM/static planner selection
│   └── executor_node (line 143)     # Calls graph.execute()
├── graph.py:30-155                  # Shared executor (used by both modes!)
└── tests/test_langgraph_ci.py       # LangGraph tests
```

**Development Policy**: **All new orchestrator features go here**. This is the active development path.

#### 3.3 Shared Core: graph.execute()

**Location**: `handoff/20250928/40_App/orchestrator/graph.py:30-155`

**Critical Understanding**: This is **NOT** just the "old Simple orchestrator" - it's the **shared execution engine** for both modes!

**Used By**:
1. **Simple Mode**: Direct call from `worker.py:399`
   ```python
   from graph import execute
   pr_url, state, trace_id = execute(goal, repo, trace_id)
   ```

2. **LangGraph Mode**: Called by `executor_node` in `langgraph_orchestrator.py:143`
   ```python
   def executor_node(state: AgentState) -> AgentState:
       from graph import execute
       pr_url, ci_state, trace_id = execute(goal, repo, trace_id=trace_id)
       # ...
   ```

**What It Does**:
- Cost tracking and budget enforcement (`cost_tracker.py`)
- Rate limiting (10 PRs/hour via `rate_limit.py`)
- FAQ content generation with GPT-4 (`llm/faq_generator.py`)
- Git branch creation and PR opening (`tools/github_api.py`)
- CI check monitoring (`get_pr_checks()`)
- Test mode auto-cleanup (draft PR cleanup)

**⚠️ Critical Development Rule**: Changes to `graph.execute()` affect **BOTH** modes. Always:
1. Test with both Simple and LangGraph modes
2. Add tests in `test_graph.py` AND `test_langgraph_ci.py`
3. State in PR description: "This change affects both orchestrator modes"

#### 3.4 Routing Logic (Canary Deployment)

**Location**: `handoff/20250928/40_App/orchestrator/redis_queue/worker.py:366-400`

**Algorithm**:
```python
use_langgraph = settings.use_langgraph or False
use_langgraph_percent = getattr(settings, 'use_langgraph_percent', 0)

if not use_langgraph and use_langgraph_percent > 0:
    # Canary logic: MD5 hash for deterministic routing
    task_hash = int(hashlib.md5(task_id.encode()).hexdigest(), 16)
    task_percent = task_hash % 100  # 0-99 bucket
    use_langgraph = task_percent < use_langgraph_percent
    
    logger.info(f"Canary deployment: task_percent={task_percent}, "
                f"threshold={use_langgraph_percent}, use_langgraph={use_langgraph}")

if use_langgraph:
    from langgraph_orchestrator import run_orchestrator
    logger.info(f"Using LangGraph orchestrator for task {task_id}")
else:
    from graph import execute
    logger.info(f"Using simple orchestrator for task {task_id}")
```

**Properties**:
- **Deterministic**: Same task_id always routes to same mode
- **Uniform**: MD5 ensures even distribution across 0-99 buckets
- **Controllable**: Adjust `USE_LANGGRAPH_PERCENT` to change traffic split
- **Observable**: Logs routing decision with structured logging

**Monitoring**:
```bash
# Search in Render Dashboard → morningai-backend-v2-stg-worker → Logs
"Canary deployment"           # Routing decision
"Using LangGraph orchestrator" # LangGraph execution
"Using simple orchestrator"    # Simple execution
```

#### 3.5 Deployment Configuration

**Worker Service** (Render):
- Service: `morningai-agent-worker` (Production), `morningai-backend-v2-stg-worker` (Staging)
- Runtime: Python (not Docker)
- Path: `handoff/20250928/40_App/orchestrator`
- Start Command: `python redis_queue/worker.py`

**Environment Variables**:

⚠️ **注意**：以下為參考配置。實際環境變數請查看 Render Dashboard。

```bash
# Phase 1 Reference Configuration
USE_LANGGRAPH=false              # Allow canary (not 100%)
USE_LANGGRAPH_PERCENT=5          # 5% to LangGraph
USE_LLM_PLANNER=true             # LangGraph uses LLM planner

# Kill Switch (Emergency)
USE_LANGGRAPH=false
USE_LANGGRAPH_PERCENT=0          # 0% to LangGraph (100% Simple)

# Full LangGraph (Future)
USE_LANGGRAPH=true               # 100% to LangGraph
```

**Dependencies** (`handoff/20250928/40_App/orchestrator/requirements.txt`):
- LangGraph + LangChain (for LangGraph mode)
- OpenAI SDK (for LLM planner)
- Redis Queue (RQ) for worker
- All dependencies for both modes (shared environment)

### 4. Frontend System

MorningAI has two separate frontend applications with distinct purposes and boundaries:

#### 4.1 Frontend Dashboard (End-User Application)

**Location**: `handoff/20250928/40_App/frontend-dashboard/`

**Purpose**: End-user analytics and monitoring interface

**Architecture**: React 19.1.0 + Vite 6 + TypeScript 5.9

**Key Components**:
- **Design System**: Apple-inspired components
- **Components**: 12 Apple components (Button, Input, Toast, Modal, etc.)
- **Pages**: Dashboard, Strategies, Approvals, History, Costs
- **Hooks**: Custom React hooks for state management
- **Utils**: Utility functions and helpers

**Design System**:
- Typography: 13 sizes, 5 weights, 3 line heights
- Colors: 5 emotional colors, semantic colors, dark mode
- Material: 5 levels of glass effects
- Shadows: 5 levels, colored shadows
- Spacing: 8 levels, 8px grid

**Testing**:
- Unit Tests: Vitest + React Testing Library
- E2E Tests: Playwright (planned)
- Accessibility: WCAG AAA compliance

**Deployment**:
- Production: https://app.gm365.me
- Vercel deployment

#### 4.2 Owner Console (Admin/Governance Application)

**Location**: `handoff/20250928/40_App/owner-console/`

**Purpose**: Owner management, governance, and system administration

**Architecture**: React 19.1.0 + Vite 6 + TypeScript 5.9

**Styling**: Tailwind CSS 4.1.7 with custom design system
- Design tokens: `packages/shared-ui/src/tokens.json` (single source of truth)
- Theme configuration: `src/styles/theme.css` (Tailwind v4 @theme syntax)
- Container width tokens: `--max-width-*` (separate from spacing tokens)
- Regression test: `e2e/max-width-regression.spec.ts` (prevents layout collapse)

**Development Status** (Updated 2025-11-15):
- ✅ **P0 (Week 1)**: Token security (credentials + CSRF + 401 retry) - COMPLETE
- ✅ **P1 (Week 2)**: 2FA system (10 components + 11 tests + enforcement), Test coverage 59.89% lines (as reported) - COMPLETE
- 🟡 **P1 (Week 3)**: Mock cleanup (complete), Agent Logs (60% - missing Trace links/drawer/skeleton), SystemMonitoring (60% - missing skeleton/empty states/charts) - PARTIAL
- 🔴 **P2 (Week 4)**: Billing/Subscription/Alerting - NOT STARTED
- ✅ **P2 (Design System)**: Tailwind v4 theme integration + design token replacement - COMPLETE

**Key Features**:
- ✅ System Monitoring (health checks, metrics, logs, real API integration)
- ✅ Agent Governance (agent management, execution tracking, reputation)
- ✅ Tenant Management (real API integration)
- ✅ 2FA Settings (enrollment, challenge, backup codes, trusted devices)
- ✅ Admin controls with enhanced security
- 🟡 Agent Execution Logs (filtering, pagination, sorting - missing Trace ID links, detail drawer, skeleton loading)
- 🔴 Billing Dashboard (not started)
- 🔴 Subscription Management (not started)
- 🔴 Alerting System (not started)

**Test Coverage**:
- 59.89% lines, 45.76% branches (as reported in CI on 2025-11-16; exceeds 30% target)
- 47 tests passing
- Key test files: `auth-2fa.test.tsx` (11 tests), `2fa-api.test.ts` (7 tests)

**Security Features**:
- ✅ HttpOnly cookies with credentials: 'include'
- ✅ CSRF token protection (automatic injection)
- ✅ 401 automatic refresh retry mechanism
- ✅ 403 CSRF failure automatic retry
- ✅ Open redirect prevention (sanitizeRedirect)
- ✅ Mandatory 2FA for owner role
- ✅ Generated clients use secured apiClient

**Deployment**:
- Production: https://admin.gm365.me
- Vercel deployment

**Related Documentation**:
- Phase Plan: `docs/OWNER_CONSOLE_PHASE_PLAN.md`
- Investigation Report: `docs/WEEK_3_4_INVESTIGATION_REPORT.md`

⚠️ **Cross-Import Restrictions**: ESLint enforces `no-restricted-imports` to prevent accidental imports between frontend-dashboard and owner-console. Use `packages/shared-ui` for shared components.

#### 4.3 Frontend Boundaries and Separation

**IMPORTANT**: The two frontend applications are completely separate and should NOT share code or cross-import from each other.

**Boundary Rules**:
1. **No Cross-Imports**: `frontend-dashboard` MUST NOT import from `owner-console` and vice versa
2. **Shared Code**: Common code should be extracted to `packages/shared-ui` or `packages/*`
3. **API Clients**: Each app has its own API client configuration
4. **Authentication**: Each app has its own auth flow (though both use the same backend)
5. **Deployment**: Each app deploys independently to different domains

**Enforcement**:
- ESLint `no-restricted-imports` rules enforce boundaries
- CI checks prevent cross-imports
- Separate package.json dependencies

**Why Separate Apps?**
- **frontend-dashboard**: End-user facing, analytics focus, public access
- **owner-console**: Admin facing, governance focus, restricted access
- Different user personas, different security requirements, different deployment cadences

---

## Environment Configuration

### Environment Schema (Single Source of Truth)

**Location**: `config/env.schema.yaml`

**Purpose**: Canonical definition of all environment variables across the entire application

**Key Features**:
- 56 total variables (19 required, 37 optional)
- Categorized by purpose (Authentication, Security, Database, Cloud Services, etc.)
- Type validation (secret, url, string, boolean, integer)
- Security level classification (critical, secret, public)
- Comprehensive descriptions and examples

**Generator Script**: `scripts/generate-env-examples.py`
- Generates `.env.example` files from schema
- Ensures consistency across all components
- Run after modifying `config/env.schema.yaml`

**Drift Checker**: `scripts/check-env-drift.py`
- Validates `.env.example` files match schema
- Runs in CI to prevent drift
- Exit code 1 if drift detected

**Workflow**:
1. Modify `config/env.schema.yaml` (single source of truth)
2. Run `python scripts/generate-env-examples.py` to regenerate `.env.example` files
3. Run `python scripts/check-env-drift.py` to verify no drift
4. Commit all changes together
### Production URLs

**Frontend Applications** (see [TERMINOLOGY.md](./TERMINOLOGY.md#域名映射-domain-mapping) for domain mapping details):
- **Tenant Dashboard**: https://app.gm365.me (租戶用戶)
- **Owner Console**: https://admin.gm365.me (平台所有者)
- **Legacy URL**: https://morningai.vercel.app (still active, redirects to app.gm365.me)

**Backend Services**:
- Backend API: https://morningai-backend-v2.onrender.com
- Orchestrator API: https://morningai-orchestrator-api.onrender.com

### Production Environment

**Services**:
- Backend: https://morningai-backend-v2.onrender.com
- Orchestrator: https://morningai-orchestrator-api.onrender.com
- Tenant Dashboard: https://app.gm365.me
- Owner Console: https://admin.gm365.me

**Infrastructure**:
- Database: Supabase PostgreSQL (production)
- Redis: Upstash (TLS enabled)
- Monitoring: Sentry (environment: production)

**Branch**: `main`

**Environment Variables** (`.env.example`):
```bash
ENVIRONMENT=production
DATABASE_URL=postgresql://...
REDIS_URL=rediss://...
JWT_SECRET_KEY=<production-secret>
SECRET_KEY=<production-secret>
MASTER_ENCRYPTION_KEY=<production-secret>
ORCHESTRATOR_JWT_SECRET=<production-secret>
SENTRY_DSN=<production-dsn>
SENTRY_ENVIRONMENT=production
```

### Staging Environment

**Services**:
- Backend: https://morningai-backend-v2-stg.onrender.com
- Orchestrator: https://morningai-orchestrator-api-stg.onrender.com
- Frontend (Dashboard): https://staging.morningai.me
- Frontend (Owner Console): https://staging-owner.morningai.me

**Infrastructure**:
- Database: Supabase PostgreSQL (staging: dckisglnlemvpvmyvnut)
- Redis: Upstash (shared, key prefix: `stg:`)
- Monitoring: Sentry (environment: staging)

**Branch**: `develop`

**Status**: ✅ Fully Operational (as of 2025-11-04)

**Environment Variables**:
```bash
ENVIRONMENT=staging
DATABASE_URL=postgresql://postgres.[PROJECT_ID]:[PASSWORD]@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
REDIS_URL=rediss://default:[PASSWORD]@[HOST].upstash.io:6379
REDIS_KEY_PREFIX=stg:
RQ_QUEUE_NAME=orchestrator-staging
ORCHESTRATOR_JWT_SECRET=<staging-secret-48-chars>
SENTRY_ENVIRONMENT=staging
```

**Documentation**: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)

### Local Development

**Services**:
- Backend: http://localhost:8000
- Orchestrator: http://localhost:8001
- Frontend: http://localhost:5173

**Infrastructure**:
- Database: Local PostgreSQL or Staging Supabase
- Redis: Local Redis or Staging Redis

**Environment Variables**:
```bash
ENVIRONMENT=development
DATABASE_URL=postgresql://localhost:5432/morningai
REDIS_URL=redis://localhost:6379/0
TESTING=false
```

---

## Deployment Architecture

### Deployment Platforms

**Render** (Backend + Orchestrator):
- **Production Backend**: `morningai-backend-v2`
- **Production Orchestrator**: `morningai-orchestrator-api`
- **Staging Backend**: `morningai-backend-v2-stg`
- **Staging Orchestrator**: `morningai-orchestrator-api-stg`
- **Cost**: $7/month per service (Starter plan)

**Vercel** (Frontend):
- **Production**: `app.gm365.me` (dashboard), `admin.gm365.me` (owner console)
- **Staging**: `staging.morningai.me` (dashboard), `staging-owner.morningai.me` (owner console)
- **Preview**: Auto-deploy for `feature/*`, `fix/*`, `devin/*` branches
- **Branch Policy**: `develop` → staging, `main` → production
- **Ignore Script**: `scripts/vercel-ignore.sh` (skips docs-only changes)
- **Documentation**: [docs/deployment/VERCEL_DEPLOYMENT_STRATEGY.md](deployment/VERCEL_DEPLOYMENT_STRATEGY.md)
- **Cost**: $0/month (Free tier)

**Fly.io** (Agent Sandboxes):
- **Dev Agent Sandbox**: `morningai-sandbox-dev-agent`
- **Ops Agent Sandbox**: `morningai-sandbox-ops-agent`
- **Cost**: ~$4/month (auto-scale to $0 when idle)

**Supabase** (Database):
- **Production**: Production project
- **Staging**: `dckisglnlemvpvmyvnut`
- **Cost**: $0/month (Free tier) or $25/month (Pro)

**Upstash** (Redis):
- **Shared**: Same Redis for all environments
- **Isolation**: Key prefixes (`stg:` for staging)
- **Cost**: $0/month (Free tier) or $10/month (Pay-as-you-go)

### Deployment Workflow

```mermaid
graph LR
    A[Feature Branch] -->|PR| B[develop]
    B -->|Auto-deploy| C[Staging Environment]
    C -->|Manual Test| D{Tests Pass?}
    D -->|Yes| E[PR to main]
    E -->|Manual Approval| F[Production]
    D -->|No| A
```

**CI/CD Workflows**:
1. **Staging CI** (`.github/workflows/staging-deploy.yml`)
   - Trigger: Push/PR to `develop`
   - Tests: Backend (pytest + coverage), Frontend (build)
   - Deploy: Auto-deploy to Render staging services

2. **Production CI** (`.github/workflows/backend.yml`, etc.)
   - Trigger: Push to `main`
   - Tests: Full test suite, E2E tests
   - Deploy: Auto-deploy to production services
   - Validation: Post-deploy health checks (90% SLA)

### Docker Configuration

**Orchestrator Dockerfile** (`orchestrator/Dockerfile`):
```dockerfile
FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
COPY orchestrator/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY orchestrator/ ./orchestrator/
RUN pip install --no-cache-dir -e ./orchestrator
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)"
CMD ["uvicorn", "orchestrator.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Fly.io Configuration** (`.fly-web/fly.toml`):
```toml
app = "morningai-web"
primary_region = "nrt"

[http_service]
  internal_port = 3000
  force_https = true
  auto_stop_machines = true
  auto_start_machines = true
  min_machines_running = 0

[[services.ports]]
  port = 80
  handlers = ["http"]
  force_https = true

[[services.ports]]
  port = 443
  handlers = ["tls", "http"]
```

---

## Key Files Reference

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `.env.example` | Environment variables template | Root |
| `config/env.schema.yaml` | Environment variables schema | `config/` |
| `package.json` | Root Node.js configuration | Root |
| `pnpm-workspace.yaml` | pnpm workspace configuration | Root |
| `turbo.json` | Turbo build configuration | Root |
| `requirements.txt` | Root Python dependencies | Root |

### Backend Files

| File | Purpose | Location |
|------|---------|----------|
| `src/main.py` | Flask application | `handoff/.../api-backend/src/` |
| `src/database.py` | Database connection | `handoff/.../api-backend/src/` |
| `requirements.txt` | Python dependencies | `handoff/.../api-backend/` |
| `pytest.ini` | pytest configuration | `handoff/.../api-backend/` |

### Orchestrator Files

| File | Purpose | Location |
|------|---------|----------|
| `api/main.py` | FastAPI application | `orchestrator/api/` |
| `api/auth.py` | JWT authentication | `orchestrator/api/` |
| `task_queue/redis_queue.py` | Redis queue | `orchestrator/task_queue/` |
| `Dockerfile` | Docker configuration | `orchestrator/` |
| `requirements.txt` | Python dependencies | `orchestrator/` |

### Frontend Files

| File | Purpose | Location |
|------|---------|----------|
| `src/App.tsx` | Main application | `handoff/.../frontend-dashboard/src/` |
| `package.json` | Node.js dependencies | `handoff/.../frontend-dashboard/` |
| `vite.config.ts` | Vite configuration | `handoff/.../frontend-dashboard/` |
| `tsconfig.json` | TypeScript configuration | `handoff/.../frontend-dashboard/` |
| `tailwind.config.js` | Tailwind CSS configuration | `handoff/.../frontend-dashboard/` |

### Documentation Files

| File | Purpose | Location |
|------|---------|----------|
| `README.md` | Project overview | Root |
| `ENVIRONMENTS.md` | Environment architecture | `docs/` |
| `ONBOARDING_GUIDE.md` | Onboarding guide | `docs/` |
| `STAGING_SETUP_GUIDE.md` | Staging setup | `docs/ops/` |
| `ARCHITECTURE.md` | System architecture | `docs/` |
| `CONTRIBUTING.md` | Contribution guidelines | `docs/` |

---

## Development Workflows

### Git Workflow

**Branches**:
- `main`: Production branch
- `develop`: Staging branch
- `feature/*`: Feature branches
- `fix/*`: Bug fix branches
- `hotfix/*`: Hotfix branches

**Workflow**:
1. Create feature branch from `develop`
2. Develop and commit changes
3. Create PR to `develop`
4. Auto-deploy to staging
5. Test on staging
6. Create PR to `main` (after staging validation)
7. Manual approval required
8. Auto-deploy to production

### PR Guidelines

**Design PRs**:
- UI/copy/styles only
- Cannot include API/logic changes
- Enforced by `pr-guard.yml`

**Engineering PRs**:
- API/logic only
- Cannot include UI/copy/styles changes
- Enforced by `pr-guard.yml`

**RFC Required**:
- OpenAPI/schema changes
- Database schema changes
- Breaking changes
- Template: `.github/ISSUE_TEMPLATE/rfc.md`

### Code Review Process

1. **Self-Review**: Review your own code before requesting review
2. **Automated Checks**: Ensure CI passes
3. **Peer Review**: Request review from team members
4. **Address Feedback**: Make requested changes
5. **Approval**: Get approval from reviewers
6. **Merge**: Merge to target branch

---

## Testing Infrastructure

### Test Coverage

**Current**: 41%  
**Target**: 80% by Q2 2026

**Coverage Database**: `.coverage` (SQLite)

### Test Suites

**Backend Tests** (`handoff/.../api-backend/tests/`):
- `test_database_connection.py`: Database connection tests
- `test_phase4_6_comprehensive.py`: Phase 4-6 API tests
- `test_unit_comprehensive.py`: Unit tests
- `test_zero_coverage_modules.py`: Targets uncovered code
- `test_ops_agent_sandbox.py`: E2E tests

**Frontend Tests** (`handoff/.../frontend-dashboard/src/`):
- Unit tests: Vitest + React Testing Library
- Component tests: Storybook stories (26 stories in `handoff/20250928/40_App/frontend-dashboard/.storybook/`)
- Accessibility tests: axe-core integration

**Storybook Architecture**:
- **Location**: 
  - Application Layer: `handoff/20250928/40_App/frontend-dashboard/.storybook/`
  - Owner Console: `handoff/20250928/40_App/owner-console/.storybook/` (added November 2025)
  - Shared UI: `packages/shared-ui/.storybook/` (added November 2025)
- **Configuration**: 
  - Frontend Dashboard: `handoff/20250928/40_App/frontend-dashboard/.storybook/main.ts:1-53`
  - Owner Console: `handoff/20250928/40_App/owner-console/.storybook/main.ts` (Storybook 8.6.14)
    - **P1 Improvements** (November 2025): MSW addon, dark mode, test runner
    - MSW Config: `.storybook/msw-config.ts` - Wildcard host matching (`*/api/...`)
    - Preview Config: `.storybook/preview.tsx` - MSW initialization, dark mode sync
    - Test Runner: `.storybook/test-runner.ts` - a11y checks with axe-playwright
  - Shared UI: `packages/shared-ui/.storybook/main.ts` (Storybook 8.6.14)
- **Stories**: 52+ total (26 in frontend-dashboard, 13 in owner-console, 13 in shared-ui, 5 in tools/frontend-lab)
  - Owner Console Stories:
    - `src/pages/SystemMonitoring.stories.jsx` - 7 variants (Loading, Healthy, Degraded, Unhealthy, Empty states, Error)
    - `src/components/AgentExecutionLogs.stories.tsx` - 6 variants (Loading, Successful, Mixed statuses, Empty, Error, Pagination)
- **Components Documented**: Apple-style components, design system showcase, color/spacing/typography systems, shared UI components (Card, Button, Badge, Alert, Avatar, Progress, Tabs, Dialog), Owner Console pages (SystemMonitoring, AgentExecutionLogs)
- **Running Storybook**:
  - Owner Console: `cd handoff/20250928/40_App/owner-console && pnpm storybook` (port 6007)
  - Shared UI: `pnpm --filter @morningai/shared-ui storybook` (port 6006)
  - Frontend Dashboard: `pnpm --filter frontend-dashboard storybook` (port 6006)
- **Testing Storybook**:
  - Owner Console: `cd handoff/20250928/40_App/owner-console && pnpm test-storybook` (a11y checks)
  - Shared UI: `pnpm --filter @morningai/shared-ui test-storybook:ci`
- **Design Tokens**: Single source of truth at `packages/shared-ui/src/tokens.json`

### CI/CD Testing

**Staging CI** (`.github/workflows/staging-deploy.yml`):
- Backend: pytest + coverage (74%+ required)
- Frontend: build + lint
- Smoke tests

**Production CI**:
- Full test suite
- E2E tests
- Post-deploy health checks (90% SLA)

### Test Commands

**Backend**:
```bash
cd handoff/20250928/40_App/api-backend
pytest -v
pytest --cov=src --cov-report=html
```

**Frontend**:
```bash
cd handoff/20250928/40_App/frontend-dashboard
pnpm test
pnpm test:coverage
```

---

## Documentation Structure

### Documentation Categories

**Getting Started**:
- `README.md`: Project overview
- `docs/ONBOARDING_GUIDE.md`: Onboarding guide
- `docs/setup_local.md`: Local setup guide

**Architecture**:
- `docs/ARCHITECTURE.md`: System architecture
- `docs/ENVIRONMENTS.md`: Environment architecture
- `docs/agent-sandbox-architecture.md`: Sandbox architecture
- `docs/architecture/decisions/`: ADRs

**Development**:
- `docs/CONTRIBUTING.md`: Contribution guidelines
- `docs/ci_matrix.md`: CI/CD workflows
- `docs/config/env_schema.md`: Environment variables

**Operations**:
- `docs/ops/STAGING_SETUP_GUIDE.md`: Staging setup
- `docs/ops/staging-environment-plan.md`: Staging plan
- `docs/MONITORING_SETUP.md`: Monitoring setup

**UI/UX**:
- `docs/UI_UX_QUICKSTART.md`: Quick start
- `docs/UI_UX_CHEATSHEET.md`: Cheat sheet
- `docs/UI_UX_RESOURCES.md`: Resources
- `docs/UX/`: Design system documentation

**Security**:
- `docs/REDIS_SECURITY.md`: Redis security
- `docs/RLS_IMPLEMENTATION_GUIDE.md`: Row-level security
- `docs/SECRET_SCANNING_GUIDE.md`: Secret management

**Testing**:
- `docs/TESTING.md`: Testing documentation
- `docs/PHASE3_TESTING_GUIDE.md`: Phase 3 testing

### Documentation Standards

**Format**: Markdown (`.md`)

**Structure**:
- Clear headings (H1, H2, H3)
- Table of contents for long documents
- Code examples with syntax highlighting
- Links to related documentation
- Last updated date

**Maintenance**:
- Update documentation with code changes
- Review documentation quarterly
- Archive outdated documentation

---

## Maintenance Guidelines

### Regular Maintenance Tasks

**Weekly**:
- Check staging service health
- Review CI/CD failures
- Monitor test coverage

**Monthly**:
- Clean up staging database
- Review and update documentation
- Check dependency updates
- Review Sentry errors

**Quarterly**:
- Rotate production secrets
- Review and update ADRs
- Audit GitHub Actions workflows
- Review cost optimization

### Code Quality Standards

**Python**:
- Follow PEP 8 style guide
- Use type hints
- Write docstrings
- Maintain test coverage >40%

**TypeScript**:
- Follow ESLint rules
- Use strict TypeScript
- Write JSDoc comments
- Maintain test coverage >40%

**Git Commits**:
- Use conventional commits
- Write clear commit messages
- Reference issues/PRs

### Security Best Practices

**Secrets**:
- Never commit secrets to repository
- Use different secrets for each environment
- Rotate secrets quarterly (production)
- Use strong secrets (32+ characters)

**Dependencies**:
- Keep dependencies up to date
- Review security advisories
- Use dependency scanning

**Access Control**:
- Use principle of least privilege
- Review access permissions regularly
- Enable 2FA for all accounts

---

## Appendix

### Quick Reference

**Service URLs**:
- Production Backend: https://morningai-backend-v2.onrender.com
- Production Orchestrator: https://morningai-orchestrator-api.onrender.com
- Production Frontend: https://morningai.vercel.app
- Staging Backend: https://morningai-backend-v2-stg.onrender.com
- Staging Orchestrator: https://morningai-orchestrator-api-stg.onrender.com

**Dashboards**:
- Render: https://dashboard.render.com/
- Vercel: https://vercel.com/dashboard
- Supabase: https://supabase.com/dashboard
- Sentry: https://sentry.io/organizations/morningai/issues/
- GitHub: https://github.com/RC918/morningai

**Documentation**:
- Environments: [docs/ENVIRONMENTS.md](ENVIRONMENTS.md)
- Onboarding: [docs/ONBOARDING_GUIDE.md](ONBOARDING_GUIDE.md)
- Staging Setup: [docs/ops/STAGING_SETUP_GUIDE.md](ops/STAGING_SETUP_GUIDE.md)
- Architecture: [docs/ARCHITECTURE.md](ARCHITECTURE.md)
- Contributing: [docs/CONTRIBUTING.md](CONTRIBUTING.md)

### Glossary

**ADR**: Architecture Decision Record  
**CI/CD**: Continuous Integration/Continuous Deployment  
**E2E**: End-to-End  
**JWT**: JSON Web Token  
**LSP**: Language Server Protocol  
**MCP**: Management Control Plane  
**OODA**: Observe, Orient, Decide, Act  
**PR**: Pull Request  
**RFC**: Request for Comments  
**RLS**: Row-Level Security  
**SLA**: Service Level Agreement  
**TLS**: Transport Layer Security

---

**Document Version**: 1.4.0  
**Last Updated**: 2025-11-16  
**Maintained By**: CTO / DevOps Team  
**Status**: ✅ Complete and Current

**Changelog**:
- 2025-11-16 (v1.4.0): Added agent evaluation harness, strategic roadmap comparison, backend test fix documentation
- 2025-11-15 (v1.3.0): Updated Owner Console status
- 2025-10-28 (v1.0.0): Initial version
