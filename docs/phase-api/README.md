# Phase API Documentation

## Overview

The MorningAI backend includes several "phase" API modules located in the root directory. These modules provide production endpoints for different phases of the system's evolution and are imported by the main FastAPI backend.

**Status**: PRODUCTION  
**Location**: `handoff/20250928/40_App/api-backend/src/phases/` (migrated from root directory)  
**Related**: ADR-003 (Backend of Record)

## Module Location

These files have been **migrated** from the root directory to `handoff/20250928/40_App/api-backend/src/phases/` per Blueprint's modular structure requirements.

**Migration Date**: January 2026  
**Migration PR**: [Phase API Migration to src/phases/](https://github.com/RC918/morningai/pull/4287)

---

## Phase API Modules

### Phase 4: Meta-Agent Coordination API

**File**: `phase4_meta_agent_api.py`  
**Purpose**: Meta-agent coordination and decision-making  
**Status**: PRODUCTION

#### Key Components

1. **MetaAgentDecisionHub**
   - OODA (Observe-Orient-Decide-Act) cycle implementation
   - System and business metrics collection
   - Situation analysis and decision-making
   - Automated action execution

2. **LangGraphWorkflowEngine**
   - Workflow creation and management
   - Multi-agent coordination
   - State machine execution
   - Node and edge graph definitions

3. **AIGovernanceConsole**
   - Governance policy management
   - Compliance monitoring
   - Risk assessment
   - Audit logging

#### API Endpoints

```python
# OODA Cycle
async def api_meta_agent_ooda_cycle() -> Dict[str, Any]
# Returns: cycle_id, status, observation, orientation, decision, action

# LangGraph Workflows
async def api_create_langgraph_workflow(workflow_definition: Dict[str, Any]) -> Dict[str, Any]
# Returns: workflow_id, status, node_count, edge_count

async def api_execute_workflow(workflow_id: str, input_data: Dict[str, Any]) -> Dict[str, Any]
# Returns: execution_id, status, output_data, execution_time_ms

# Governance
async def api_governance_status() -> Dict[str, Any]
# Returns: governance_score, compliance_status, risk_assessment

async def api_create_governance_policy(policy_data: Dict[str, Any]) -> Dict[str, Any]
# Returns: policy_id, status, enforcement_level
```

#### Data Models

**OODAContext**:
```python
@dataclass
class OODAContext:
    observation_id: str
    timestamp: datetime
    system_metrics: Dict[str, Any]
    business_metrics: Dict[str, Any]
    situation_assessment: Dict[str, Any]
    decision_required: bool
```

**DecisionResult**:
```python
@dataclass
class DecisionResult:
    decision_id: str
    strategy: str
    actions: List[Dict[str, Any]]
    confidence: float
    risk_assessment: float
    execution_timeline: str
    requires_approval: bool
```

#### Usage Example

```python
# Start OODA cycle
result = await api_meta_agent_ooda_cycle()
# {
#   'cycle_id': 'ooda_1234567890',
#   'status': 'completed',
#   'observation': {...},
#   'decision': {...},
#   'action': {...}
# }

# Create workflow
workflow_def = {
    'name': 'AI Agent Coordination',
    'nodes': [...],
    'edges': [...]
}
workflow = await api_create_langgraph_workflow(workflow_def)

# Execute workflow
execution = await api_execute_workflow(workflow['workflow_id'], {'task': 'optimize'})
```

---

### Phase 5: Data Intelligence API

**File**: `phase5_data_intelligence_api.py`  
**Purpose**: Data analytics, business intelligence, and growth marketing  
**Status**: PRODUCTION

#### Key Components

1. **QuickSightIntegration**
   - Amazon QuickSight dashboard creation
   - Data visualization management
   - Automated insights generation
   - Report generation

2. **GrowthMarketingEngine**
   - Referral program management
   - Marketing content generation
   - Campaign analytics
   - Viral growth tracking

3. **DataIntelligencePlatform**
   - Business intelligence summaries
   - User, revenue, and growth metrics
   - Automated insights generation
   - Recommendation engine

#### API Endpoints

```python
# QuickSight Dashboards
async def api_create_quicksight_dashboard(dashboard_config: Dict[str, Any]) -> Dict[str, Any]
# Returns: dashboard_id, status, url, visualization_count

async def api_get_dashboard_insights(dashboard_id: str) -> Dict[str, Any]
# Returns: insights_count, insights, confidence_avg

async def api_generate_automated_report(report_config: Dict[str, Any]) -> Dict[str, Any]
# Returns: report_id, status, data, download_url

# Growth Marketing
async def api_create_referral_program(program_config: Dict[str, Any]) -> Dict[str, Any]
# Returns: program_id, tracking_code, rewards

async def api_get_referral_analytics(program_id: str) -> Dict[str, Any]
# Returns: total_referrals, conversion_rate, roi, top_referrers

async def api_generate_marketing_content(content_request: Dict[str, Any]) -> Dict[str, Any]
# Returns: content_id, type, content, engagement_rate

# Business Intelligence
async def api_get_business_intelligence() -> Dict[str, Any]
# Returns: summary, key_metrics, insights, recommendations
```

#### Data Models

**DataInsight**:
```python
@dataclass
class DataInsight:
    insight_id: str
    category: str
    title: str
    description: str
    confidence: float
    impact_score: float
    recommended_actions: List[str]
```

**GrowthMetric**:
```python
@dataclass
class GrowthMetric:
    metric_name: str
    current_value: float
    previous_value: float
    growth_rate: float
    trend: str
    target_value: float
```

#### Usage Example

```python
# Create QuickSight dashboard
dashboard_config = {
    'name': 'User Analytics Dashboard',
    'type': 'analytics',
    'data_sources': ['user_metrics', 'system_metrics'],
    'visualizations': [...]
}
dashboard = await api_create_quicksight_dashboard(dashboard_config)

# Get insights
insights = await api_get_dashboard_insights(dashboard['dashboard_id'])

# Create referral program
program_config = {
    'name': 'User Referral Program',
    'referrer_reward': 100,
    'referee_reward': 50,
    'reward_type': 'points'
}
program = await api_create_referral_program(program_config)

# Get analytics
analytics = await api_get_referral_analytics(program['program_id'])

# Generate marketing content
content_request = {
    'type': 'email',
    'target_audience': 'enterprise_users'
}
content = await api_generate_marketing_content(content_request)

# Get business intelligence summary
bi_summary = await api_get_business_intelligence()
```

---

### Phase 6: Security & Governance API

**File**: `phase6_security_governance_api.py`  
**Purpose**: Security monitoring, compliance, and governance  
**Status**: PRODUCTION

#### Key Components

1. **SecurityMonitoringSystem**
   - Real-time threat detection
   - Security event logging
   - Vulnerability scanning
   - Incident response automation

2. **ComplianceEngine**
   - Regulatory compliance tracking (GDPR, SOC2, HIPAA)
   - Audit trail management
   - Policy enforcement
   - Compliance reporting

3. **GovernanceFramework**
   - Access control management
   - Data governance policies
   - Risk assessment
   - Security posture monitoring

#### API Endpoints

```python
# Security Monitoring
async def api_get_security_status() -> Dict[str, Any]
# Returns: threat_level, active_threats, security_score

async def api_scan_vulnerabilities() -> Dict[str, Any]
# Returns: scan_id, vulnerabilities_found, severity_breakdown

async def api_respond_to_incident(incident_data: Dict[str, Any]) -> Dict[str, Any]
# Returns: incident_id, response_actions, status

# Compliance
async def api_get_compliance_status() -> Dict[str, Any]
# Returns: compliance_score, frameworks, violations

async def api_generate_compliance_report(framework: str) -> Dict[str, Any]
# Returns: report_id, framework, compliance_percentage, findings

# Governance
async def api_get_governance_posture() -> Dict[str, Any]
# Returns: governance_score, policies_active, risk_level
```

#### Usage Example

```python
# Get security status
security = await api_get_security_status()
# {
#   'threat_level': 'low',
#   'active_threats': 0,
#   'security_score': 94.5
# }

# Scan for vulnerabilities
scan = await api_scan_vulnerabilities()

# Get compliance status
compliance = await api_get_compliance_status()

# Generate compliance report
report = await api_generate_compliance_report('SOC2')
```

---

### Phase 7: Startup & Initialization

**File**: `phase7_startup.py`  
**Purpose**: System initialization and startup procedures  
**Status**: PRODUCTION

#### Key Components

1. **SystemInitializer**
   - Service health checks
   - Database migrations
   - Cache warming
   - Configuration validation

2. **ServiceOrchestrator**
   - Service dependency management
   - Startup sequence coordination
   - Graceful shutdown handling
   - Health monitoring

#### API Endpoints

```python
# System Initialization
async def api_initialize_system() -> Dict[str, Any]
# Returns: initialization_status, services_started, health_checks

async def api_get_system_health() -> Dict[str, Any]
# Returns: overall_health, service_statuses, uptime

async def api_shutdown_gracefully() -> Dict[str, Any]
# Returns: shutdown_status, services_stopped
```

#### Usage Example

```python
# Initialize system on startup
init_result = await api_initialize_system()

# Check system health
health = await api_get_system_health()

# Graceful shutdown
shutdown = await api_shutdown_gracefully()
```

---

## Import Relationships

### Backend Main Entry Point

**File**: `handoff/20250928/40_App/api-backend/src/main.py`

```python
# Phase API imports (migrated to src/phases/ per Blueprint modular structure)
from src.phases.phase4_meta_agent_api import (
    api_meta_agent_ooda_cycle,
    api_create_langgraph_workflow,
    api_execute_workflow,
    api_governance_status,
    api_create_governance_policy
)

from src.phases.phase5_data_intelligence_api import (
    api_create_quicksight_dashboard,
    api_get_dashboard_insights,
    api_generate_automated_report,
    api_create_referral_program,
    api_get_referral_analytics,
    api_generate_marketing_content,
    api_get_business_intelligence
)

from src.phases.phase6_security_governance_api import (
    api_get_security_status,
    api_scan_vulnerabilities,
    api_respond_to_incident,
    api_get_compliance_status,
    api_generate_compliance_report,
    api_get_governance_posture
)

from phase7_startup import (
    api_initialize_system,
    api_get_system_health,
    api_shutdown_gracefully
)
```

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FastAPI Backend                          │
│         (handoff/20250928/40_App/api-backend)               │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │              src/main.py                            │    │
│  │         (Main FastAPI Application)                  │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          │ imports                           │
│                          ▼                                   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Phase API Modules (Root Dir)                │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  phase4_meta_agent_api.py                     │   │  │
│  │  │  - MetaAgentDecisionHub                       │   │  │
│  │  │  - LangGraphWorkflowEngine                    │   │  │
│  │  │  - AIGovernanceConsole                        │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  phase5_data_intelligence_api.py              │   │  │
│  │  │  - QuickSightIntegration                      │   │  │
│  │  │  - GrowthMarketingEngine                      │   │  │
│  │  │  - DataIntelligencePlatform                   │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  phase6_security_governance_api.py            │   │  │
│  │  │  - SecurityMonitoringSystem                   │   │  │
│  │  │  - ComplianceEngine                           │   │  │
│  │  │  - GovernanceFramework                        │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  │                                                        │  │
│  │  ┌──────────────────────────────────────────────┐   │  │
│  │  │  phase7_startup.py                            │   │  │
│  │  │  - SystemInitializer                          │   │  │
│  │  │  - ServiceOrchestrator                        │   │  │
│  │  └──────────────────────────────────────────────┘   │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## Error Handling

All phase API functions follow consistent error handling patterns:

```python
try:
    result = await api_function(params)
    return {
        'status': 'success',
        'data': result
    }
except Exception as e:
    logger.error(f"Error in api_function: {e}")
    return {
        'status': 'error',
        'error': str(e),
        'timestamp': datetime.now().isoformat()
    }
```

---

## Testing

Each phase API module includes a test function that can be run standalone:

```bash
# Test Phase 4
python phase4_meta_agent_api.py

# Test Phase 5
python phase5_data_intelligence_api.py

# Test Phase 6
python phase6_security_governance_api.py

# Test Phase 7
python phase7_startup.py
```

---

## Future Refactoring Plan

### Long-term Goal

Move all phase API modules to a structured directory:

```
handoff/20250928/40_App/api-backend/src/phases/
├── __init__.py
├── phase4_meta_agent.py
├── phase5_data_intelligence.py
├── phase6_security_governance.py
└── phase7_startup.py
```

### Benefits

1. **Better Organization**: Clear module hierarchy
2. **Improved Imports**: Relative imports within backend
3. **Easier Testing**: Isolated test suites per phase
4. **Cleaner Root**: Reduced clutter in root directory

### Migration Steps

1. Create `src/phases/` directory structure
2. Move phase files with updated imports
3. Update `main.py` import statements
4. Update test files and CI workflows
5. Verify all endpoints still work
6. Remove old files from root directory

---

## Related Documentation

- **Architecture Decision**: [ADR-003: Backend of Record](../adr/003-backend-of-record.md)
- **Orchestrator Documentation**: [docs/orchestrator/ROLE.md](../orchestrator/ROLE.md)
- **Backend Main**: [handoff/20250928/40_App/api-backend/src/main.py](../../handoff/20250928/40_App/api-backend/src/main.py)
- **Technical Debt Roadmap**: [docs/TECHNICAL_DEBT_ROADMAP.md](../TECHNICAL_DEBT_ROADMAP.md)

---

## Monitoring and Observability

### Logging

All phase APIs use structured logging:

```python
logger.info("Operation completed", extra={
    "operation": "api_function_name",
    "phase": "phase4",
    "duration_ms": 150,
    "status": "success"
})
```

### Metrics

Key metrics to monitor:
- **API Response Time**: P50, P95, P99 latencies
- **Error Rate**: Percentage of failed requests
- **Throughput**: Requests per second per phase
- **Resource Usage**: CPU, memory per phase module

### Health Checks

Each phase provides health check endpoints:
- Phase 4: Meta-agent OODA cycle status
- Phase 5: Data platform connectivity
- Phase 6: Security monitoring status
- Phase 7: System initialization status

---

## Security Considerations

### Authentication

All phase API endpoints require authentication via:
- JWT tokens (for user requests)
- Service tokens (for internal requests)
- API keys (for external integrations)

### Authorization

Role-based access control (RBAC):
- **Admin**: Full access to all phases
- **Developer**: Access to Phase 4, 5, 7
- **Security**: Access to Phase 6
- **Analyst**: Read-only access to Phase 5

### Data Protection

- Sensitive data encrypted at rest and in transit
- PII handling follows GDPR compliance
- Audit logs for all governance operations
- Rate limiting on all endpoints

---

## Performance Optimization

### Caching Strategy

- **Phase 4**: Cache OODA cycle results (30s TTL)
- **Phase 5**: Cache dashboard insights (5min TTL)
- **Phase 6**: Cache security status (1min TTL)
- **Phase 7**: Cache system health (10s TTL)

### Async Operations

All phase APIs use async/await for:
- Non-blocking I/O operations
- Concurrent data collection
- Parallel metric aggregation
- Efficient resource utilization

---

## Troubleshooting

### Common Issues

**Import Errors**:
```python
# Problem: Cannot import phase modules
# Solution: Ensure root directory is in PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:/path/to/morningai"
```

**Missing Dependencies**:
```bash
# Problem: Module not found errors
# Solution: Install phase-specific requirements
pip install -r requirements.txt
```

**Performance Issues**:
```python
# Problem: Slow API responses
# Solution: Enable caching and async operations
# Check logs for bottlenecks
```

---

## Contributing

When modifying phase API modules:

1. **Maintain Backward Compatibility**: Don't break existing endpoints
2. **Add Tests**: Include test cases for new functionality
3. **Update Documentation**: Keep this README in sync with code
4. **Follow Conventions**: Use existing patterns and naming
5. **Log Appropriately**: Add structured logging for debugging

---

## Changelog

- **2025-10-30**: Initial documentation created (Issue #870)
- **Future**: Plan migration to `src/phases/` directory
