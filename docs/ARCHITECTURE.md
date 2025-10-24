# MorningAI Architecture - World-Class AI Agent Ecosystem

## Vision & Design Philosophy

MorningAI is evolving from an MVP to a **world-class autonomous AI agent orchestration platform**. Our architecture is designed around these core principles:

1. **AI-First**: Every component leverages LLM intelligence for autonomous decision-making
2. **Multi-Agent Collaboration**: Specialized agents (Dev, Ops, PM, Growth) work together seamlessly
3. **Production-Grade**: 99.9% uptime, <100ms latency, enterprise security
4. **Multi-Tenant SaaS**: Complete data isolation with RLS (Row Level Security)
5. **Human-in-the-Loop**: Governance framework with cost tracking and reputation scoring

## Current State (Phase 8 - v8.0.0)

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  Owner Console          │  Tenant Dashboard    │  Future Apps   │
│  (admin.morningai.com)  │  (app.morningai.com) │                │
│  - Agent Governance     │  - Strategies        │                │
│  - Tenant Management    │  - Approvals         │                │
│  - System Monitoring    │  - History & Costs   │                │
│  Vite + React + PWA     │  Vite + React + PWA  │                │
└─────────────────────────────────────────────────────────────────┘
                              ↓ HTTPS/JWT
┌─────────────────────────────────────────────────────────────────┐
│                      API Backend Layer                           │
├─────────────────────────────────────────────────────────────────┤
│  FastAPI Backend (Render)                                        │
│  - JWT Authentication + RBAC                                     │
│  - Multi-tenant RLS enforcement                                  │
│  - RESTful API endpoints                                         │
│  - Health checks & monitoring                                    │
│                                                                   │
│  Endpoints:                                                       │
│  - /api/governance/* (Owner only)                                │
│  - /api/tenants/* (Owner only)                                   │
│  - /api/strategies/* (Tenant + Owner)                            │
│  - /api/agent/* (Agent orchestration)                            │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    Data & State Layer                            │
├─────────────────────────────────────────────────────────────────┤
│  Supabase PostgreSQL                                             │
│  - Multi-tenant tables with RLS                                  │
│  - pgvector for semantic search                                  │
│  - Audit logging                                                 │
│                                                                   │
│  Upstash Redis                                                   │
│  - Session state                                                 │
│  - Rate limiting                                                 │
│  - Task queues (RQ)                                              │
│  - Caching layer                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                  Agent Orchestration Layer                       │
├─────────────────────────────────────────────────────────────────┤
│  LangGraph Orchestrator                                          │
│  - Stateful agent workflows                                      │
│  - Task planning & decomposition                                 │
│  - CI monitoring & auto-fixing                                   │
│  - Cost tracking & budget enforcement                            │
│  - Reputation engine                                             │
│                                                                   │
│  Agent Sandboxes (Fly.io)                                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Dev_Agent    │  │ Ops_Agent    │  │ PM_Agent     │          │
│  │ - VSCode     │  │ - Monitoring │  │ - Planning   │          │
│  │ - LSP Tools  │  │ - Logs       │  │ - Backlog    │          │
│  │ - Git        │  │ - Incidents  │  │ - Roadmap    │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                   │
│  Governance Framework                                            │
│  - Cost Tracker (daily/hourly budgets)                           │
│  - Reputation Engine (success/failure scoring)                   │
│  - Rate Limiter (max 10 PRs/hour)                                │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    External Integrations                         │
├─────────────────────────────────────────────────────────────────┤
│  GitHub API          │  OpenAI GPT-4      │  Stripe (Phase 9)  │
│  - PR automation     │  - Content gen     │  - Subscriptions   │
│  - CI monitoring     │  - Task planning   │  - Billing         │
│  - Code review       │  - Bug analysis    │  - Usage tracking  │
└─────────────────────────────────────────────────────────────────┘
```

## Three-Layer Separation Architecture

### 1. Owner Console (Platform Management)
**URL**: `admin.morningai.com` or `owner.morningai.com`  
**Access**: Owner role only  
**Purpose**: Platform-wide management and governance

**Features**:
- **Agent Governance**: Monitor agent performance, reputation scores, cost tracking
- **Tenant Management**: Create/manage tenants, view usage, billing
- **System Monitoring**: Platform health, performance metrics, incident management
- **Platform Settings**: Global configuration, feature flags, compliance settings

**Tech Stack**:
- Vite + React + TypeScript
- PWA (Progressive Web App)
- Deployed on Vercel
- Independent authentication flow

### 2. Tenant Dashboard (User Interface)
**URL**: `app.morningai.com` or `dashboard.morningai.com`  
**Access**: Tenant users (with RBAC)  
**Purpose**: Tenant-specific operations and insights

**Features**:
- **Dashboard**: Overview of strategies, agent executions, costs
- **Strategies**: Create and manage automation strategies
- **Approvals**: Review and approve agent actions
- **History**: Audit log of all agent activities
- **Costs**: Usage tracking and billing information

**Tech Stack**:
- Vite + React + TypeScript
- PWA (Progressive Web App)
- Deployed on Vercel
- Tenant-scoped authentication

### 3. API Backend (Shared Services)
**URL**: `api.morningai.com` (Render deployment)  
**Access**: Role-based with RLS enforcement  
**Purpose**: Unified backend for all frontends

**Features**:
- **Authentication**: JWT-based with role verification
- **Authorization**: RBAC + RLS for data isolation
- **Multi-Tenancy**: Complete tenant data isolation
- **Agent Orchestration**: Trigger and monitor agent workflows
- **Governance**: Cost tracking, reputation scoring, rate limiting

**Tech Stack**:
- FastAPI (Python)
- Supabase PostgreSQL (with RLS)
- Upstash Redis (caching + queues)
- Deployed on Render

## Security Architecture

### Authentication & Authorization

**JWT Token Structure**:
```json
{
  "sub": "user_id",
  "role": "owner|admin|user",
  "tenant_id": "tenant_uuid",
  "permissions": ["read:strategies", "write:approvals"],
  "exp": 1234567890
}
```

**Role Hierarchy**:
- **Owner**: Full platform access, can manage all tenants
- **Admin**: Tenant-level admin, can manage tenant users
- **User**: Standard tenant user, limited permissions

### Row Level Security (RLS)

**Current State**: Partially implemented  
**Target State (P0)**: Full RLS on all tenant tables

**RLS Policy Pattern**:
```sql
-- Tenant isolation
CREATE POLICY tenant_isolation ON strategies
  FOR ALL
  USING (tenant_id = current_setting('app.current_tenant_id')::uuid);

-- Owner bypass
CREATE POLICY owner_access ON strategies
  FOR ALL
  USING (
    current_setting('app.current_role') = 'owner'
    OR tenant_id = current_setting('app.current_tenant_id')::uuid
  );
```

**Protected Tables**:
- `tenants` - Tenant metadata
- `users` - User accounts
- `strategies` - Automation strategies
- `decisions` - Agent decisions
- `costs` - Usage tracking
- `audit_logs` - Compliance logs

### Data Encryption

- **In Transit**: TLS 1.3 for all connections
- **At Rest**: Supabase encryption for database
- **Secrets**: Environment variables, never committed to git
- **API Keys**: Rotated quarterly, stored in secret manager

## Agent Orchestration Architecture

### LangGraph Workflow

**State Machine**:
```
┌─────────┐     ┌──────────┐     ┌────────────┐     ┌─────────┐
│ Planner │────▶│ Executor │────▶│ CI Monitor │────▶│ Fixer   │
└─────────┘     └──────────┘     └────────────┘     └─────────┘
     │               │                  │                 │
     └───────────────┴──────────────────┴─────────────────┘
                            │
                      ┌──────────┐
                      │Finalizer │
                      └──────────┘
```

**Workflow Steps**:
1. **Planner**: Decompose goal into actionable steps
2. **Executor**: Execute steps (create PR, update FAQ, etc.)
3. **CI Monitor**: Wait for CI checks, analyze results
4. **Fixer**: Auto-fix failures if possible
5. **Finalizer**: Record results, update reputation

### Agent Sandboxes

**Dev_Agent** (Fly.io):
- **URL**: https://morningai-sandbox-dev-agent.fly.dev/
- **Tools**: VSCode Server, LSP, Git, FileSystem
- **Use Cases**: Bug fixing, PR creation, code refactoring
- **Cost**: ~$2/month (auto-scales to $0 when idle)

**Ops_Agent** (Fly.io):
- **URL**: https://morningai-sandbox-ops-agent.fly.dev/
- **Tools**: Shell, Browser, Render API, Sentry
- **Use Cases**: Performance monitoring, incident response
- **Cost**: ~$2/month (auto-scales to $0 when idle)

**PM_Agent** (Planned - Q1 2026):
- **Tools**: GitHub Issues, Linear, Notion
- **Use Cases**: Sprint planning, backlog prioritization, roadmap generation

### Governance Framework

**Cost Tracker**:
- Daily budget: $10 (configurable)
- Hourly budget: $2 (configurable)
- Tracks: API calls, compute time, storage
- Action: Block execution if budget exceeded

**Reputation Engine**:
- Success events: +10 points
- Failure events: -5 points
- Cost overrun: -20 points
- Reputation threshold: 50 (below = restricted)

**Rate Limiter**:
- Max PRs per hour: 10
- Max agent executions per day: 100
- Prevents infinite loops and abuse

## Deployment Architecture

### Current Deployment (Phase 8)

**Frontend**:
- **Vercel** (2 apps: Owner Console, Tenant Dashboard)
- Auto-deploy on push to `main`
- Preview deployments for PRs
- CDN: Cloudflare (planned Q2 2026)

**Backend**:
- **Render** (1 instance, 512MB RAM)
- Auto-deploy on push to `main`
- Health checks: `/healthz`
- Scaling: Manual (target: 3 instances in Q4 2025)

**Database**:
- **Supabase** (PostgreSQL + pgvector)
- Connection pooling: PgBouncer
- Backups: Daily automated

**Cache/Queue**:
- **Upstash Redis** (Serverless)
- Session storage
- Rate limiting
- Task queues (RQ)

**Agent Sandboxes**:
- **Fly.io** (2 apps: Dev_Agent, Ops_Agent)
- Docker isolation
- Auto-scaling (min: 0, max: 1)
- Cost: ~$4/month total

### Target Deployment (Q2 2026)

**Multi-Region Architecture**:
```
┌──────────────────────────────────────────────────────────────┐
│                   Cloudflare Global CDN                       │
│              (Load Balancing + WAF + DDoS)                    │
└──────────────────────────────────────────────────────────────┘
         │                  │                  │
    ┌────▼────┐        ┌────▼────┐       ┌────▼────┐
    │ US-East │        │ EU-West │       │ APAC    │
    │ (Primary)│       │ (Replica)│      │(Replica)│
    └─────────┘        └─────────┘       └─────────┘
         │                  │                  │
    ┌────▼────────────────────────────────────▼────┐
    │      PostgreSQL Multi-Region Replication      │
    │      (Supabase + Read Replicas)               │
    └───────────────────────────────────────────────┘
```

**High Availability**:
- 3 backend instances per region
- Auto-scaling: min 2, max 10
- Health checks every 30s
- Automatic failover <30s
- Target uptime: 99.9%

**Performance Targets**:
- API latency (p95): <100ms
- Database query time (p95): <50ms
- Cache hit rate: >80%
- Page load time: <2s

## Monitoring & Observability

### Current Monitoring

**GitHub Actions**:
- CI/CD workflows (16 workflows)
- Test coverage tracking (41% → target 80%)
- OpenAPI validation
- Post-deploy health checks

**Basic Metrics**:
- Uptime: ~90%
- Test coverage: 41%
- API response time: ~500ms

### Target Monitoring (Q1 2026)

**Metrics Collection**:
- **Prometheus**: System metrics, API metrics, agent metrics
- **Grafana**: Dashboards for visualization
- **CloudWatch**: Centralized logging
- **Datadog**: APM and distributed tracing

**Dashboards**:
1. **System Health**: CPU, memory, disk, network
2. **API Performance**: Latency, throughput, error rates
3. **Agent Performance**: Success rate, cost, reputation
4. **Business Metrics**: MRR, active users, agent executions

**Alerting**:
- PagerDuty integration
- Slack notifications
- On-call rotation
- Incident response runbook

## Scalability Considerations

### Current Limitations
- Single backend instance (512MB RAM)
- No caching layer (beyond Redis sessions)
- No CDN for static assets
- Manual scaling required

### Scaling Roadmap

**Q4 2025**:
- Deploy 3 backend instances
- Implement multi-layer caching (L1: local, L2: Redis)
- Add database connection pooling
- Optimize slow queries

**Q1 2026**:
- Multi-region deployment (US, EU, APAC)
- Global load balancing (Cloudflare)
- Read replicas for database
- CDN for static assets

**Q2 2026**:
- Auto-scaling based on load
- Horizontal scaling for agent sandboxes
- Database sharding (if needed)
- Edge computing for low-latency regions

## Compliance & Governance

### Current State
- Basic audit logging
- Manual security reviews
- No formal compliance certifications

### Target State (Q2 2026)

**SOC2 Type I Certification**:
- Centralized audit logging (1-year retention)
- Access control policies
- Incident response runbook
- Penetration testing (annual)
- Security training (quarterly)

**GDPR Compliance**:
- Data retention policies
- Right to erasure (delete user data)
- Data portability (export user data)
- Privacy policy and terms of service

**Security Best Practices**:
- Secret scanning in CI (Gitleaks + TruffleHog)
- Dependency vulnerability scanning (Dependabot)
- WAF rules (Cloudflare)
- DDoS protection
- Rate limiting

## Technology Stack Summary

### Frontend
- **Framework**: Vite + React + TypeScript
- **UI Library**: Tailwind CSS + shadcn/ui
- **State Management**: React Context + Hooks
- **PWA**: Service Workers + Offline support
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI (Python)
- **Authentication**: JWT + RBAC
- **Database**: Supabase PostgreSQL + pgvector
- **Cache**: Upstash Redis
- **Task Queue**: Redis Queue (RQ)
- **Deployment**: Render

### AI/ML
- **LLM**: OpenAI GPT-4 (primary), GPT-3.5 (fallback)
- **Orchestration**: LangGraph + LangChain
- **Vector Search**: pgvector (Supabase)
- **Embeddings**: OpenAI text-embedding-3-small

### Infrastructure
- **Frontend Hosting**: Vercel
- **Backend Hosting**: Render
- **Database**: Supabase (PostgreSQL)
- **Cache/Queue**: Upstash (Redis)
- **Agent Sandboxes**: Fly.io (Docker)
- **CDN**: Cloudflare (planned)
- **Monitoring**: Prometheus + Grafana (planned)
- **Logging**: CloudWatch (planned)

### CI/CD
- **Version Control**: GitHub
- **CI/CD**: GitHub Actions (16 workflows)
- **Testing**: pytest (Python), Vitest (TypeScript)
- **Code Quality**: Ruff (Python), ESLint (TypeScript)
- **Coverage**: pytest-cov (target: 80%)

## Directory Structure

```
morningai/
├── handoff/20250928/40_App/
│   ├── frontend-dashboard/      # Tenant Dashboard (Vite + React)
│   ├── owner-console/           # Owner Console (Vite + React)
│   ├── api-backend/             # FastAPI Backend
│   └── orchestrator/            # LangGraph Orchestrator
│       ├── graph.py             # FAQ generation pipeline
│       ├── langgraph_orchestrator.py  # Stateful workflow
│       └── governance/          # Cost tracking + Reputation
├── agents/
│   ├── dev_agent/               # Dev Agent Sandbox (Fly.io)
│   └── ops_agent/               # Ops Agent Sandbox (Fly.io)
├── docs/
│   ├── ARCHITECTURE.md          # This file
│   ├── CONTRIBUTING.md          # Contribution guidelines
│   ├── GOVERNANCE_FRAMEWORK.md  # Agent governance
│   └── ci_matrix.md             # CI/CD workflows
├── .github/
│   ├── workflows/               # GitHub Actions (16 workflows)
│   ├── projects/                # Project roadmaps
│   └── ISSUE_TEMPLATE/          # Issue templates
└── CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md  # Strategic roadmap
```

## Next Steps & Roadmap

See [CTO Strategic Plan](../CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md) for detailed roadmap.

**Immediate Priorities (P0 - Next 2 Weeks)**:
1. Implement RLS (Row Level Security) in Supabase
2. Add secret scanning to CI (Gitleaks + TruffleHog)
3. Fix test collection errors (5 errors blocking tests)
4. Migrate backend from SQLite to PostgreSQL

**Short-Term Goals (P1 - Next 30 Days)**:
1. Deploy multi-instance backend (3 instances)
2. Implement load balancing (Cloudflare)
3. Set up centralized logging (CloudWatch)
4. Configure monitoring (Prometheus + Grafana)
5. Stripe integration MVP
6. Increase test coverage to 50%

**Medium-Term Goals (P2 - Next 90 Days)**:
1. Replace FAQ template with GPT-4 generation
2. Implement dynamic task decomposition (LangGraph)
3. Enhance Dev_Agent with LSP tools
4. Activate PM_Agent (sprint planning)
5. Optimize database queries & add indexes
6. SOC2 gap analysis & auditor selection

**Long-Term Vision (Q2 2026)**:
- 99.9% uptime SLA
- <100ms API latency (p95)
- 80% test coverage
- $50k MRR, 1,000 paying customers
- SOC2 Type I certification
- Multi-region deployment (US, EU, APAC)

---

**Last Updated**: October 24, 2025  
**Version**: 2.0 (World-Class Architecture)  
**Owner**: CTO  
**Related Documents**:
- [CTO Strategic Plan](../CTO_STRATEGIC_PLAN_MVP_TO_WORLD_CLASS.md)
- [Strategic Roadmap](../.github/projects/cto-strategic-roadmap-q4-2025-q2-2026.yml)
- [Governance Framework](GOVERNANCE_FRAMEWORK.md)
- [Contributing Guidelines](../CONTRIBUTING.md)
