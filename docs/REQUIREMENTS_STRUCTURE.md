# Requirements Structure Documentation

## Overview

MorningAI uses a **service-separated dependency management strategy** to ensure each service only installs the dependencies it needs. This approach improves build times, reduces security surface area, and makes dependency management more maintainable.

## Requirements Files Structure

```
morningai/
├── requirements.txt                                    # Shared dev/test dependencies
├── orchestrator/requirements.txt                       # FastAPI orchestrator service
├── handoff/20250928/40_App/
│   ├── api-backend/requirements.txt                   # Flask backend service
│   └── orchestrator/requirements.txt                  # RQ worker service
├── agents/
│   ├── faq_agent/requirements.txt                     # FAQ agent dependencies
│   ├── dev_agent/requirements.txt                     # Dev agent dependencies
│   └── ops_agent/requirements.txt                     # Ops agent dependencies
└── monitoring/requirements.txt                         # Monitoring service
```

---

## Root Requirements (Development/Testing Only)

**File**: `requirements.txt`  
**Purpose**: Shared development and testing tools  
**Usage**: Install for running tests and linting

### Contents

```txt
# Configuration & Environment
python-dotenv>=1.0.0
pyyaml>=6.0

# Testing
pytest>=7.4.0
pytest-asyncio>=0.21.0
pytest-cov>=4.1.0
pytest-timeout>=2.2.0

# Code Quality
flake8

# Utilities
typing_extensions>=4.15.0
```

### Installation

```bash
# For development/testing only
pip install -r requirements.txt
```

### ⚠️ Important

**DO NOT** use root `requirements.txt` to run services. Each service has its own requirements file with all necessary runtime dependencies.

---

## Service-Specific Requirements

### 1. Orchestrator API (FastAPI)

**File**: `orchestrator/requirements.txt`  
**Framework**: FastAPI  
**Purpose**: Task submission API endpoint  
**Deployment**: Render (morningai-orchestrator-api)

#### Key Dependencies

```txt
fastapi>=0.104.0          # Web framework
uvicorn[standard]>=0.24.0 # ASGI server
redis>=5.0.0              # Queue management
pydantic>=2.4.0           # Data validation
PyJWT>=2.8.0              # Authentication
```

#### Installation

```bash
cd orchestrator
pip install -r requirements.txt
```

#### CI Usage

```yaml
# .github/workflows/orchestrator-ci.yml
- name: Install dependencies
  run: |
    cd orchestrator
    pip install -r requirements.txt
```

---

### 2. Backend API (Flask)

**File**: `handoff/20250928/40_App/api-backend/requirements.txt`  
**Framework**: Flask  
**Purpose**: Main backend API service  
**Deployment**: Render (morningai-backend-v2)

#### Key Dependencies

```txt
Flask==3.1.1              # Web framework
flask-cors==6.0.0         # CORS support
Flask-SQLAlchemy==3.1.1   # ORM
gunicorn                  # WSGI server
redis>=5.2.0              # Caching/queue
rq                        # Task queue
sentry-sdk==2.19.2        # Error tracking
supabase==2.6.0           # Database client
```

#### Installation

```bash
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt
```

#### CI Usage

```yaml
# .github/workflows/backend.yml
- name: Install dependencies
  run: |
    cd handoff/20250928/40_App/api-backend
    pip install -r requirements.txt
```

---

### 3. Orchestrator Worker (RQ Worker)

**File**: `handoff/20250928/40_App/orchestrator/requirements.txt`  
**Framework**: RQ (Redis Queue)  
**Purpose**: Task execution engine  
**Deployment**: Render (morningai-agent-worker)

#### Key Dependencies

```txt
rq>=1.16.0                # Redis Queue worker
langgraph                 # State machine
langchain-core            # LLM framework
redis>=5.0.0              # Queue backend
```

#### Installation

```bash
cd handoff/20250928/40_App/orchestrator
pip install -r requirements.txt
pip install -e .  # Install orchestrator package
```

#### CI Usage

```yaml
# .github/workflows/orchestrator-e2e.yml
- name: Install dependencies
  run: |
    cd handoff/20250928/40_App/orchestrator
    pip install -r requirements.txt
    pip install -e .
```

---

## Framework Separation

### Why Split by Framework?

MorningAI uses **two different Python web frameworks**:

1. **FastAPI** (Orchestrator API)
   - Modern async framework
   - Automatic OpenAPI documentation
   - Type hints and validation
   - Used for: Task submission endpoints

2. **Flask** (Backend API)
   - Mature synchronous framework
   - Large ecosystem
   - Simple and flexible
   - Used for: Main business logic API

### Dependency Conflicts

Keeping requirements separate prevents conflicts:
- FastAPI requires `uvicorn` (ASGI server)
- Flask requires `gunicorn` (WSGI server)
- Different versions of shared dependencies (e.g., `pydantic`)

---

## CI/CD Integration

### Backend CI Workflow

**File**: `.github/workflows/backend.yml`

```yaml
jobs:
  test:
    steps:
      - name: Install dependencies
        run: |
          cd handoff/20250928/40_App/api-backend
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
          cd ../orchestrator
          pip install -e .
```

### Orchestrator E2E Workflow

**File**: `.github/workflows/orchestrator-e2e.yml`

```yaml
jobs:
  run:
    steps:
      - name: Install orchestrator dependencies
        run: |
          cd handoff/20250928/40_App/orchestrator
          pip install -r requirements.txt
          pip install -e .
```

---

## Best Practices

### 1. Adding New Dependencies

**For Backend API (Flask)**:
```bash
cd handoff/20250928/40_App/api-backend
pip install <package>
pip freeze | grep <package> >> requirements.txt
```

**For Orchestrator API (FastAPI)**:
```bash
cd orchestrator
pip install <package>
pip freeze | grep <package> >> requirements.txt
```

**For Development Tools**:
```bash
# Root directory
pip install <package>
pip freeze | grep <package> >> requirements.txt
```

### 2. Updating Dependencies

```bash
# Update specific package
cd <service-directory>
pip install --upgrade <package>
pip freeze | grep <package> > temp.txt
# Manually update requirements.txt with new version
```

### 3. Verifying Dependencies

```bash
# Check for unused dependencies
pip install pip-autoremove
pip-autoremove <package> --list

# Check for security vulnerabilities
pip install safety
safety check -r requirements.txt
```

---

## Troubleshooting

### Issue: Import Errors

**Problem**: `ModuleNotFoundError` when running service

**Solution**: Ensure you're installing from the correct requirements file:
```bash
# Wrong (using root requirements)
pip install -r requirements.txt

# Correct (using service requirements)
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt
```

### Issue: Version Conflicts

**Problem**: Conflicting dependency versions between services

**Solution**: Use virtual environments for each service:
```bash
# Backend API
python -m venv venv-backend
source venv-backend/bin/activate
cd handoff/20250928/40_App/api-backend
pip install -r requirements.txt

# Orchestrator API
python -m venv venv-orchestrator
source venv-orchestrator/bin/activate
cd orchestrator
pip install -r requirements.txt
```

### Issue: CI Build Failures

**Problem**: CI fails with missing dependencies

**Solution**: Verify CI workflow uses correct requirements path:
```yaml
# Check workflow file
- name: Install dependencies
  run: |
    cd <correct-service-path>
    pip install -r requirements.txt
```

---

## Migration History

### Issue #871: Split requirements.txt by service

**Date**: 2025-10-30  
**Status**: ✅ Completed (already implemented)

**Changes Made**:
1. ✅ Root `requirements.txt` reduced to shared dev/test dependencies
2. ✅ `orchestrator/requirements.txt` created with FastAPI dependencies
3. ✅ `handoff/20250928/40_App/api-backend/requirements.txt` contains Flask dependencies
4. ✅ CI workflows updated to use correct paths
5. ✅ README.md documentation added (lines 100-139)
6. ✅ All services build successfully

**Verification**:
- Backend CI: ✅ Passing
- Orchestrator E2E: ✅ Passing
- All tests: ✅ 434/434 passing

---

## Related Documentation

- **README.md**: Lines 100-139 (Python 依賴管理)
- **CI Matrix**: [docs/ci_matrix.md](ci_matrix.md)
- **Contributing Guide**: [CONTRIBUTING.md](../CONTRIBUTING.md)
- **Orchestrator Documentation**: [docs/orchestrator/ROLE.md](orchestrator/ROLE.md)
- **Phase API Documentation**: [docs/phase-api/README.md](phase-api/README.md)

---

## Future Improvements

### Dependency Management Tools

Consider adopting modern dependency management:
- **Poetry**: Dependency resolution and lock files
- **pip-tools**: Requirements compilation and pinning
- **Dependabot**: Automated dependency updates

### Monorepo Tools

For better multi-service management:
- **Pants**: Build system for Python monorepos
- **Bazel**: Multi-language build system
- **Nx**: Monorepo orchestration

---

## Summary

MorningAI's requirements structure follows **service separation principles**:

✅ **Root requirements.txt**: Development/testing tools only  
✅ **Service requirements**: Each service has its own complete dependency list  
✅ **CI/CD integration**: Workflows use correct requirements paths  
✅ **Documentation**: Comprehensive guides in README.md and this document  

This structure ensures:
- **Fast builds**: Only install what's needed
- **Clear separation**: No confusion about which framework is used where
- **Easy maintenance**: Update dependencies per service
- **Reduced conflicts**: Isolated dependency trees
