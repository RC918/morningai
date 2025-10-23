# Agent Governance Framework

## Overview

The MorningAI Agent Governance Framework implements constraint-based autonomy for multi-agent systems. It provides three core capabilities:

1. **Policy Configuration** (`policies.yaml`) - Declarative governance rules
2. **Cost Governance** - Token/USD budget tracking and enforcement
3. **Reputation System** - Dynamic agent scoring and permission management

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Governance Layer                           │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PolicyGuard  │  │ CostTracker  │  │ Reputation   │      │
│  │              │  │              │  │ Engine       │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│  ┌──────────────┐  ┌──────────────┐                        │
│  │ Permission   │  │ Violation    │                        │
│  │ Checker      │  │ Detector     │                        │
│  └──────────────┘  └──────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ PostgreSQL   │  │ Redis        │  │ policies.yaml│      │
│  │ (Reputation) │  │ (Cost Cache) │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Policy Configuration (`config/policies.yaml`)

Declarative YAML configuration defining governance rules.

**Sections:**
- `resource_sandbox` - File access and network restrictions
- `cost_budget` - Daily, hourly, and per-task limits
- `capability_constraints` - Tool permission requirements
- `task_contract` - Output schema validation
- `risk_routing` - High-risk operation handling
- `violation_detection` - Security violation patterns
- `reputation` - Scoring rules and permission levels
- `monitoring` - Audit and alerting configuration

**Example:**
```yaml
resource_sandbox:
  file_access:
    allow: ["./apps/web/**", "./docs/**"]
    deny: ["./secrets/**", ".env*"]
  network:
    allow_domains: ["api.github.com", "registry.npmjs.org"]
    rate_limit:
      requests_per_minute: 60

cost_budget:
  daily:
    max_usd: 5.0
    max_tokens: 100000
  hourly:
    max_usd: 1.0
    max_tokens: 20000
```

### 2. PolicyGuard Middleware

Enforces constraint-based autonomy through decorator pattern.

**Key Methods:**
- `check_file_access(file_path)` - Validates file access against allow/deny lists
- `check_network_access(domain)` - Validates network access
- `check_tool_permission(tool, operation, level)` - Validates tool usage
- `check_risk_level(file_paths)` - Determines operation risk level
- `requires_human_approval(labels, risk)` - Checks if human approval needed

**Usage:**
```python
from governance import guarded, PolicyGuard

@guarded
def deploy_to_production(config):
    # Automatically checks permissions before execution
    pass
```

### 3. Cost Tracker

Multi-granularity budget tracking and enforcement.

**Features:**
- Real-time token and USD tracking
- Three granularity levels: daily, hourly, per-task
- Alert thresholds: warning (80%), critical (95%)
- Redis-backed for performance

**Usage:**
```python
from governance import get_cost_tracker, CostBudgetExceeded

tracker = get_cost_tracker()

# Track usage
tracker.track_usage(trace_id, tokens=1000, cost_usd=0.03, model='gpt-4')

# Enforce budget
try:
    tracker.enforce_budget(trace_id, period='daily')
except CostBudgetExceeded as e:
    print(f"Budget exceeded: {e}")

# Get status
status = tracker.get_budget_status(trace_id, period='daily')
print(f"Used: ${status['usage']['usd']:.2f} / ${status['limits']['usd']:.2f}")
```

### 4. Reputation System

Dynamic agent scoring with permission level gating.

**Database Schema:**
```sql
-- Agent reputation tracking
CREATE TABLE agent_reputation (
    agent_id UUID PRIMARY KEY,
    agent_type TEXT NOT NULL,
    reputation_score INTEGER DEFAULT 100,
    permission_level TEXT DEFAULT 'sandbox_only',
    pr_merged_count INTEGER DEFAULT 0,
    pr_reverted_count INTEGER DEFAULT 0,
    test_pass_rate FLOAT DEFAULT 1.0,
    ...
);

-- Event audit trail
CREATE TABLE reputation_events (
    event_id UUID PRIMARY KEY,
    agent_id UUID REFERENCES agent_reputation(agent_id),
    event_type TEXT NOT NULL,
    delta INTEGER NOT NULL,
    trace_id UUID,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);
```

**Permission Levels:**
- `sandbox_only` (0-89): Read-only, test execution
- `staging_access` (90-129): Staging deployments, non-prod changes
- `prod_low_risk` (130-159): Low-risk prod changes (docs, UI)
- `prod_full_access` (160+): Full production access

**Scoring Rules:**
- PR merged without revert: +5
- PR reverted: -15
- Human escalation: -8
- Test passed: +2
- Test failed: -3
- Cost overrun: -10
- Violation detected: -20

**Usage:**
```python
from governance import get_reputation_engine

engine = get_reputation_engine()

# Get or create agent
agent_id = engine.get_or_create_agent('dev_agent')

# Record event
engine.record_event(
    agent_id,
    'pr_merged_without_revert',
    trace_id='trace-123',
    reason='PR #456 merged successfully'
)

# Get reputation
score = engine.get_reputation_score(agent_id)
level = engine.get_permission_level(agent_id)
print(f"Agent score: {score}, level: {level}")
```

### 5. Permission Checker

Reputation-based access control.

**Usage:**
```python
from governance import get_permission_checker, PermissionDenied

checker = get_permission_checker()

# Check permission
try:
    checker.check_permission(agent_id, 'deploy_prod')
    print("Permission granted")
except PermissionDenied as e:
    print(f"Permission denied: {e}")

# Check environment access
can_access_prod = checker.can_access_environment(agent_id, 'production')

# Get summary
summary = checker.get_permission_summary(agent_id)
print(f"Level: {summary['permission_level']}")
print(f"Score: {summary['reputation_score']}")
print(f"Allowed operations: {summary['allowed_operations']}")
```

### 6. Violation Detector

Detects and prevents policy violations.

**Features:**
- Secrets access detection
- Dangerous operations detection
- Unauthorized API access detection
- Content sanitization

**Usage:**
```python
from governance import get_violation_detector, ViolationError

detector = get_violation_detector()

# Check for violations
try:
    detector.check_all('shell_command', 'rm -rf /', {})
except ViolationError as e:
    print(f"Violation detected: {e}")

# Sanitize content
sanitized = detector.sanitize_content("API_KEY=sk-1234567890")
```

## Integration

### Graph.py Integration

The governance system is integrated into the orchestrator's graph execution:

```python
from governance import get_cost_tracker, get_reputation_engine, CostBudgetExceeded

def execute(goal, repo_full, trace_id=None):
    # Initialize governance
    cost_tracker = get_cost_tracker()
    reputation_engine = get_reputation_engine()
    agent_id = reputation_engine.get_or_create_agent('meta_agent')
    
    # Check budget before starting
    try:
        cost_tracker.enforce_budget(trace_id, period='daily')
        cost_tracker.enforce_budget(trace_id, period='hourly')
    except CostBudgetExceeded as e:
        if agent_id:
            reputation_engine.record_event(
                agent_id, 'cost_overrun', 
                trace_id=trace_id, reason=str(e)
            )
        return None, "budget_exceeded", trace_id
    
    # Execute task...
    
    # Track cost
    cost_tracker.track_usage(trace_id, tokens, cost_usd)
    
    # Record reputation event
    if state == "success":
        reputation_engine.record_event(
            agent_id, 'test_passed', 
            trace_id=trace_id
        )
```

## Daily Maintenance

### Reputation Update Script

Runs daily via GitHub Actions to:
1. Apply reputation decay for inactive agents
2. Update permission levels based on scores
3. Generate system statistics
4. Send alerts for low-reputation agents

**Manual Execution:**
```bash
python scripts/update_reputation_daily.py
```

**Automated Execution:**
- Workflow: `.github/workflows/reputation-update.yml`
- Schedule: Daily at 00:00 UTC
- Manual trigger: Available via `workflow_dispatch`

## CI/CD Integration

### Governance Check Workflow

Validates governance configuration in CI:

**Workflow:** `.github/workflows/governance-check.yml`

**Checks:**
- `policies.yaml` structure validation
- File access patterns configuration
- Cost budget configuration
- Reputation system configuration
- Governance module imports
- Risk routing configuration

**Trigger:**
- Pull requests to `main` branch
- Changes to orchestrator, agents, or policies

## Monitoring

### Key Metrics

1. **Cost Metrics:**
   - Daily/hourly/per-task token usage
   - Daily/hourly/per-task USD spending
   - Budget utilization percentage
   - Alert level (ok, warning, critical)

2. **Reputation Metrics:**
   - Average agent reputation score
   - Agents by permission level
   - High reputation agents (≥130)
   - Low reputation agents (<90)
   - Event counts by type

3. **Violation Metrics:**
   - Violation attempts by type
   - Blocked operations
   - Secrets access attempts

### Alerts

**Cost Alerts:**
- Warning: 80% of budget consumed
- Critical: 95% of budget consumed

**Reputation Alerts:**
- Agent score drops below 70
- Permission level downgrade
- Repeated violations

**Telegram Integration:**
Daily summary notifications sent to admin chat:
```
🤖 Daily Reputation Update Complete

📊 Statistics:
• Total agents: 5
• Average score: 112.4
• High reputation (≥130): 2
• Low reputation (<90): 1

📈 By Permission Level:
• sandbox_only: 1
• staging_access: 2
• prod_low_risk: 2
```

## Best Practices

### 1. Policy Configuration

- **Start restrictive**: Begin with minimal permissions, expand as needed
- **Use glob patterns**: Leverage wildcards for flexible file access rules
- **Document exceptions**: Comment why specific patterns are allowed/denied
- **Version control**: Track all policy changes in Git

### 2. Cost Management

- **Set realistic budgets**: Based on historical usage patterns
- **Monitor trends**: Review daily reports for anomalies
- **Adjust thresholds**: Tune alert levels to reduce noise
- **Track by task**: Use trace IDs for granular cost attribution

### 3. Reputation Management

- **Calibrate scoring**: Adjust scoring rules based on agent behavior
- **Review regularly**: Check agent statistics weekly
- **Investigate drops**: Analyze events when scores drop significantly
- **Reward success**: Ensure positive events are properly recorded

### 4. Security

- **Validate inputs**: Always validate file paths and commands
- **Sanitize outputs**: Remove secrets from logs and responses
- **Audit regularly**: Review violation logs for patterns
- **Update patterns**: Add new violation patterns as threats emerge

## Troubleshooting

### Common Issues

**1. Budget Exceeded Errors**
```
CostBudgetExceeded: Daily budget exceeded: 5.2/5.0 USD
```
**Solution:** 
- Check current usage: `tracker.get_budget_status(trace_id, 'daily')`
- Increase budget in `policies.yaml` if justified
- Investigate high-cost operations

**2. Permission Denied Errors**
```
PermissionDenied: Operation 'deploy_prod' denied for agent. Current level: sandbox_only
```
**Solution:**
- Check agent reputation: `engine.get_reputation_score(agent_id)`
- Review recent events: `engine.get_recent_events(agent_id)`
- Improve agent performance to increase score

**3. Policy Violations**
```
PolicyViolation: File access denied: ./secrets/api_key.txt
```
**Solution:**
- Verify file path is correct
- Check if pattern should be in allow list
- Update `policies.yaml` if legitimate access

**4. Supabase Connection Issues**
```
[ReputationEngine] Supabase unavailable: Connection timeout
```
**Solution:**
- Verify `SUPABASE_URL` and `SUPABASE_SERVICE_ROLE_KEY` are set
- Check network connectivity
- Review Supabase service status

## Migration Guide

### Applying Database Migration

```bash
# Connect to Supabase
psql $DATABASE_URL

# Run migration
\i migrations/012_agent_reputation_system.sql

# Verify tables created
\dt agent_reputation
\dt reputation_events

# Check functions
\df record_reputation_event
\df update_permission_level
```

### Initializing Agents

```python
from governance import get_reputation_engine

engine = get_reputation_engine()

# Initialize all agent types
agent_types = ['dev_agent', 'ops_agent', 'pm_agent', 'growth_strategist', 'meta_agent']

for agent_type in agent_types:
    agent_id = engine.get_or_create_agent(agent_type)
    print(f"Initialized {agent_type}: {agent_id}")
```

## API Reference

### PolicyGuard

```python
class PolicyGuard:
    def check_file_access(self, file_path: str) -> bool
    def check_network_access(self, domain: str) -> bool
    def check_tool_permission(self, tool_name: str, operation: str, level: str) -> bool
    def check_risk_level(self, file_paths: List[str]) -> str
    def requires_human_approval(self, labels: List[str], risk_level: str) -> bool
```

### CostTracker

```python
class CostTracker:
    def track_usage(self, trace_id: str, tokens: int, cost_usd: float, model: str, operation: str) -> None
    def check_budget(self, trace_id: str, period: str) -> Tuple[bool, CostMetrics, Dict]
    def enforce_budget(self, trace_id: str, period: str) -> None
    def get_budget_status(self, trace_id: str, period: str) -> Dict
    def estimate_cost(self, tokens: int, model: str) -> float
```

### ReputationEngine

```python
class ReputationEngine:
    def get_or_create_agent(self, agent_type: str) -> Optional[str]
    def record_event(self, agent_id: str, event_type: str, trace_id: str, reason: str, metadata: Dict) -> bool
    def get_reputation(self, agent_id: str) -> Optional[Dict]
    def get_permission_level(self, agent_id: str) -> str
    def get_reputation_score(self, agent_id: str) -> int
    def update_permission_level(self, agent_id: str) -> str
    def get_allowed_operations(self, agent_id: str) -> list
    def apply_decay(self, agent_id: str) -> bool
    def get_statistics(self) -> Dict
```

### PermissionChecker

```python
class PermissionChecker:
    def check_permission(self, agent_id: str, operation: str) -> bool
    def can_access_environment(self, agent_id: str, environment: str) -> bool
    def require_permission(self, agent_id: str, operation: str) -> None
    def get_permission_summary(self, agent_id: str) -> dict
```

### ViolationDetector

```python
class ViolationDetector:
    def check_secrets_access(self, content: str) -> None
    def check_dangerous_operations(self, command: str) -> None
    def check_unauthorized_api(self, api_call: str, args: Dict) -> None
    def check_file_access(self, file_path: str) -> None
    def check_all(self, operation: str, content: str, metadata: Dict) -> None
    def sanitize_content(self, content: str) -> str
```

## Future Enhancements

### Phase 1 (Current)
- ✅ Policy configuration framework
- ✅ Cost tracking and enforcement
- ✅ Reputation system with permission levels
- ✅ Violation detection
- ✅ Daily maintenance automation

### Phase 2 (Planned)
- [ ] Machine learning-based anomaly detection
- [ ] Predictive cost forecasting
- [ ] Advanced reputation decay models
- [ ] Multi-tenant isolation
- [ ] Real-time dashboard

### Phase 3 (Future)
- [ ] Federated learning for pattern recognition
- [ ] Cross-agent collaboration scoring
- [ ] Dynamic policy adjustment
- [ ] Blockchain-based audit trail
- [ ] SOC2/GDPR compliance automation

## Support

For questions or issues:
1. Check this documentation
2. Review test cases in `tests/test_governance.py`
3. Examine example usage in `handoff/20250928/40_App/orchestrator/graph.py`
4. Open an issue with label `governance`

## License

Copyright © 2025 MorningAI. All rights reserved.
