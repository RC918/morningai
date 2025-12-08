# ADR-003: Backend of Record for MorningAI

**Status**: Accepted  
**Date**: 2025-10-29  
**Deciders**: CTO, Backend Team  
**Related**: Technical Debt Roadmap Phase 2

## Context

The MorningAI codebase contains multiple backend-related directories and modules across different locations:

- `handoff/20250928/40_App/api-backend/` - Flask backend application
- `orchestrator/` - Orchestrator API service (legacy FastAPI, see note)
- `handoff/20250928/40_App/orchestrator/` - RQ-based orchestrator workers (primary)
- `phase4_meta_agent_api.py`, `phase5_data_intelligence_api.py`, etc. - Phase API modules in root
- Various agent modules in `agents/` directory

This distributed structure creates confusion about:
- Which backend is the "canonical" or "primary" backend?
- Where should new API endpoints be added?
- Which backend handles authentication, database, and core business logic?
- How do different components relate to each other?

Without a clear "Backend of Record" designation, developers face:
- Uncertainty about where to add new features
- Risk of duplicating functionality across backends
- Difficulty onboarding new team members
- Inconsistent architecture decisions

## Decision

Designate **`handoff/20250928/40_App/api-backend/`** as the **Backend of Record** for MorningAI.

### Definition

The Backend of Record is the canonical backend application that:
- Owns the primary database schema and migrations
- Handles user authentication and authorization
- Provides core business logic APIs
- Serves as the integration point for frontend applications
- Imports and exposes functionality from phase API modules

### Scope

**Backend of Record (`handoff/20250928/40_App/api-backend/`):**
- Technology: Flask + SQLAlchemy
- Deployment: `morningai-backend-v2` on Render
- Responsibilities:
  - User management and authentication (JWT)
  - Database operations (PostgreSQL via Supabase)
  - Core API endpoints (`/api/*`)
  - Health checks and monitoring
  - Integration with Redis (Upstash)
  - Importing phase API modules (phase4-7)
- Entry point: `src/main.py`

**Other Backend Components (Not Backend of Record):**
- **Orchestrator Workers** (`handoff/20250928/40_App/orchestrator/`): RQ-based workers for task execution (primary orchestrator)
- **Orchestrator API** (`orchestrator/`): Legacy FastAPI service (may be deprecated)
- **Phase API Modules** (root `phase*.py`): Imported by Backend of Record, not standalone services
- **Agent Workers**: Background workers, not HTTP APIs

> **Note**: The primary orchestrator is now RQ-based workers invoked by the Flask backend via Redis Queue. The Flask backend enqueues tasks to Redis, and RQ workers in `handoff/20250928/40_App/orchestrator/` execute them using either Simple Mode or LangGraph Mode.

### Architecture Relationship

```
Frontend (Vercel)
    ↓
Backend of Record (Flask)
    ├─ Imports: phase4_meta_agent_api.py
    ├─ Imports: phase5_data_intelligence_api.py
    ├─ Imports: phase6_security_governance_api.py
    ├─ Imports: phase6_startup.py
    ├─ Imports: phase7_startup.py
    ├─ Enqueues: Tasks to Redis Queue (RQ Workers)
    └─ Connects: PostgreSQL, Redis
```

### File Locations

**Backend of Record Structure:**
```
handoff/20250928/40_App/api-backend/
├── src/
│   ├── main.py              # Flask app entry point
│   ├── database.py          # Database connection
│   ├── routes/              # API route handlers
│   │   ├── agent.py         # Agent endpoints
│   │   ├── auth.py          # Authentication
│   │   └── governance.py    # Governance APIs
│   └── models/              # SQLAlchemy models
├── requirements.txt         # Python dependencies
├── gunicorn.conf.py        # Production server config
└── pytest.ini              # Test configuration
```

**Phase API Modules (Imported by Backend of Record):**
```
phase4_meta_agent_api.py         # Meta-agent coordination
phase5_data_intelligence_api.py  # Data intelligence & growth
phase6_security_governance_api.py # Security & governance
phase6_startup.py                # Phase 6 initialization
phase7_startup.py                # Phase 7 initialization
```

## Alternatives Considered

### 1. Orchestrator API as Backend of Record
**Pros**: Modern FastAPI, better async support  
**Cons**: Specialized for task orchestration, lacks user management and database  
**Rejected**: Orchestrator is a specialized service, not a general-purpose backend

### 2. Microservices with No Single Backend
**Pros**: Maximum flexibility, independent scaling  
**Cons**: Complexity, no clear ownership, difficult to maintain consistency  
**Rejected**: Premature for current scale, increases operational burden

### 3. Merge All Backends into One
**Pros**: Single codebase, simpler deployment  
**Cons**: Tight coupling, difficult to scale independently  
**Rejected**: Producer-consumer pattern (ADR-002) requires separation

### 4. Create New Backend from Scratch
**Pros**: Clean slate, modern architecture  
**Cons**: Migration effort, risk of breaking existing functionality  
**Deferred**: Consider for future major refactor

## Consequences

### Positive

- ✅ **Clear Ownership**: Developers know where to add new features
- ✅ **Consistent Architecture**: Single source of truth for database schema
- ✅ **Easier Onboarding**: New developers have clear entry point
- ✅ **Reduced Duplication**: Prevents reimplementing functionality
- ✅ **Simplified Testing**: Core business logic in one place
- ✅ **Better Documentation**: Can focus documentation efforts

### Negative

- ❌ **Single Point of Failure**: If Backend of Record is down, core functionality unavailable
- ❌ **Scaling Constraints**: All core logic scales together
- ❌ **Technology Lock-in**: Committed to Flask for core backend
- ❌ **Migration Path**: Phase modules in root need eventual refactor

### Operational Considerations

1. **Development Workflow**:
   - New API endpoints → Add to Backend of Record
   - New background tasks → Use Orchestrator API
   - New phase functionality → Add to appropriate phase module, import in Backend of Record

2. **Deployment**:
   - Backend of Record: `morningai-backend-v2` on Render
   - Health check: https://morningai-backend-v2.onrender.com/health
   - Auto-deploy on main branch merge

3. **Monitoring**:
   - Primary health endpoint: `/health`
   - Database connection status
   - Redis connection status
   - Version tracking: `APP_VERSION` env var

4. **Future Refactoring** (Technical Debt Roadmap):
   - Move phase modules from root to `src/phases/` directory
   - Maintain Backend of Record designation during refactor
   - Keep import paths working during transition

## Related Documentation

- [Backend README](../../handoff/20250928/40_App/api-backend/README.md)
- [ADR-002: Producer-Consumer Architecture](./002-producer-consumer-architecture.md)
- [Technical Debt Roadmap](../TECHNICAL_DEBT_ROADMAP.md)
- [Render Deployment Configuration](../../render.yaml)

## References

- Flask Documentation: https://flask.palletsprojects.com/
- SQLAlchemy Documentation: https://docs.sqlalchemy.org/
- Backend of Record Pattern: https://martinfowler.com/bliki/SystemOfRecord.html
