# MorningAI Onboarding Guide

**Welcome to MorningAI!** 🎉

> 📚 **術語標準**: 請參閱 [術語對照表](./TERMINOLOGY.md) 了解標準化的應用名稱和用戶類型定義。

This guide will help you get started with the MorningAI project, understand the architecture, set up your development environment, and start contributing.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Environment Architecture](#environment-architecture)
3. [Getting Started](#getting-started)
4. [Development Workflow](#development-workflow)
5. [Key Technologies](#key-technologies)
6. [Project Structure](#project-structure)
7. [Important Documentation](#important-documentation)
8. [Common Tasks](#common-tasks)
9. [Troubleshooting](#troubleshooting)
10. [Getting Help](#getting-help)

---

## Project Overview

### What is MorningAI?

MorningAI is an intelligent agent orchestration platform that automates software development, operations, and project management tasks. The system employs multiple specialized AI agents that work collaboratively to handle bug fixes, create pull requests, manage infrastructure, respond to incidents, and make strategic decisions.

### Vision

Building the world's most advanced autonomous AI agent orchestration platform that seamlessly integrates development, operations, and business intelligence with human-in-the-loop governance.

### Current Status

- **Phase**: Phase 8 (v8.0.0) - MVP Foundation Complete
- **Test Coverage**: 41% (Target: 80% by Q2 2026)
- **Uptime**: 90% (Target: 99.9% by Q2 2026)
- **Transformation**: Q4 2025 - Q2 2026 (MVP to World-Class)

### Key Features

- **Dev_Agent**: Automated bug fixing and PR creation (>85% success rate)
- **Ops_Agent**: Automated incident response and self-healing (>70% automation)
- **PM_Agent**: Project management and task tracking
- **Growth_Strategist**: Business strategy and optimization
- **Meta_Agent**: Agent orchestration and OODA loop coordination

---

## Environment Architecture

MorningAI uses a multi-environment deployment architecture to ensure safe development, testing, and production workflows.

### 🚀 Production Environment

**Services**:
- **Backend API**: https://morningai-backend-v2.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api.onrender.com
- **Frontend**: https://morningai.vercel.app

**Infrastructure**:
- **Database**: Supabase PostgreSQL (production)
- **Redis**: Upstash (TLS enabled)
- **Branch**: `main`
- **Auto-Deploy**: Yes

### 🧪 Staging Environment ✅

**Services**:
- **Backend API**: https://morningai-backend-v2-stg.onrender.com
- **Orchestrator API**: https://morningai-orchestrator-api-stg.onrender.com

**Infrastructure**:
- **Database**: Supabase PostgreSQL (staging: dckisglnlemvpvmyvnut)
- **Redis**: Upstash (shared, key prefix: `stg:`)
- **Branch**: `develop`
- **Auto-Deploy**: Yes
- **Status**: ✅ Fully Operational

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

**Template**: [.github/ISSUE_TEMPLATE/rfc.md](.github/ISSUE_TEMPLATE/rfc.md)

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

- **Framework**: React 18 + Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS + Custom Design System
- **State Management**: React Context + Hooks
- **UI Components**: Apple-inspired design system
- **Testing**: Vitest + React Testing Library
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
│       └── ...                    # Owner console files
│
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

The following production backend modules are located in the root directory and imported by `handoff/20250928/40_App/api-backend/src/main.py`:

- **`phase4_meta_agent_api.py`**: Meta-agent coordination (OODA loop, LangGraph workflows, AI governance)
- **`phase5_data_intelligence_api.py`**: Data intelligence (QuickSight, growth marketing, BI dashboards)
- **`phase6_security_governance_api.py`**: Security & governance (Zero Trust, SecurityReviewer Agent, HITL analysis)
- **`phase6_startup.py`**: Phase 6 initialization (monitoring, security, Meta-Agent hub)
- **`phase7_startup.py`**: Phase 7 initialization (Ops_Agent, Growth_Strategist, PM_Agent, HITL system)

**Note**: These files are in the root directory for historical reasons. They are production code imported by the backend. Future refactoring may move them to `handoff/20250928/40_App/api-backend/src/phases/`.

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

### Testing
- **[Testing Guide](TESTING.md)** - Comprehensive testing documentation
- **[Phase 3 Testing](PHASE3_TESTING_GUIDE.md)** - Phase 3 testing guide

---

## Common Tasks

### Running Tests

**Backend Tests**:
```bash
cd handoff/20250928/40_App/api-backend
source ../../../../.venv/bin/activate
pytest -v
```

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

**Create Migration**:
```bash
cd handoff/20250928/40_App/api-backend
alembic revision --autogenerate -m "description"
```

**Apply Migration**:
```bash
alembic upgrade head
```

**Rollback Migration**:
```bash
alembic downgrade -1
```

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

---

## Getting Help

### Internal Resources

**Documentation**:
- Check [docs/](docs/) directory for comprehensive documentation
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

**Last Updated**: 2025-10-28  
**Version**: 1.0.0  
**Maintained By**: CTO / DevOps Team
