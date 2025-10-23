# Ops Agent - Operations and Deployment Management

## Overview

Ops Agent is responsible for automated operations, deployment management, system monitoring, log analysis, and alert management. It integrates with Vercel for deployment operations and provides comprehensive operational capabilities.

## Architecture

```
ops_agent/
├── README.md                          # This file
├── ops_agent_ooda.py                  # Main OODA Loop implementation
├── config.example.yaml                # Configuration example
├── tools/                             # Core tools
│   ├── __init__.py
│   ├── deployment_tool.py             # Vercel deployment management
│   ├── monitoring_tool.py             # System monitoring
│   ├── log_analysis_tool.py           # Log analysis
│   ├── alert_management_tool.py       # Alert management
│   └── notification_service.py        # Notification service (Email, Slack, Webhook)
├── sandbox/                           # Sandbox environment
│   ├── ops_agent_sandbox.py          # Existing sandbox
│   └── mcp/                          # MCP tools
├── tests/                            # Test suite
│   ├── test_deployment_tool.py
│   ├── test_monitoring_tool.py
│   ├── test_log_analysis_tool.py
│   ├── test_alert_management_tool.py
│   ├── test_notification_service.py
│   ├── test_vercel_integration.py    # Real Vercel API tests
│   └── test_ops_agent_e2e.py
└── docs/                             # Documentation
    ├── DEPLOYMENT_GUIDE.md
    ├── MONITORING_GUIDE.md
    └── API_REFERENCE.md
```

## Core Features

### 1. Deployment Tool
- **Vercel Integration**: Deploy to Vercel platform
- **Deployment History**: Track all deployments
- **Rollback Support**: Quick rollback to previous versions
- **Environment Management**: Manage staging/production environments
- **Build Status Monitoring**: Monitor build progress

### 2. Monitoring Tool
- **System Metrics**: CPU, memory, disk usage
- **Application Health**: Service availability checks
- **Performance Metrics**: Response time, throughput
- **Custom Metrics**: User-defined monitoring
- **Real-time Dashboards**: Live metric visualization

### 3. Log Analysis Tool
- **Log Collection**: Centralized log aggregation
- **Pattern Detection**: Identify error patterns
- **Log Search**: Fast log query capabilities
- **Log Filtering**: Filter by severity, time, service
- **Anomaly Detection**: Detect unusual patterns

### 4. Alert Management Tool
- **Alert Rules**: Define custom alert conditions
- **Alert Channels**: Email, Slack, webhook notifications
- **Alert Prioritization**: Critical, high, medium, low
- **Alert History**: Track all triggered alerts
- **Auto-remediation**: Automatic issue resolution

### 5. Notification Service
- **Email via Mailtrap**: Production-ready email sending via Mailtrap API
- **Email via SMTP**: Alternative SMTP email delivery
- **Slack Integration**: Send notifications to Slack channels via webhooks
- **Webhook Support**: Generic webhook notifications for custom integrations
- **Multi-channel**: Send to multiple channels simultaneously
- **Configurable**: Environment-based configuration

## Success Metrics

- **Auto-fix Rate**: >80%
- **Deployment Success Rate**: >95%
- **Mean Time to Detection (MTTD)**: <5 minutes
- **Mean Time to Recovery (MTTR)**: <15 minutes
- **False Positive Rate**: <5%

## Integration Points

### External Services
- **Vercel API**: Deployment management
- **Sentry**: Error tracking (existing integration)
- **Custom Monitoring**: System-level metrics

### Internal Services
- **Dev Agent**: Coordinate code fixes
- **FAQ Agent**: Share operational insights
- **Database**: Store metrics and alerts

## Governance Integration

### Overview

Ops Agent Worker integrates with the Agent Governance Framework to provide:
- **Cost Tracking**: Token and USD budget monitoring
- **Permission Checking**: Reputation-based access control
- **Reputation Scoring**: Dynamic agent scoring based on task outcomes

### Configuration

**Required Dependencies** (`requirements.txt`):
```
PyYAML>=6.0
supabase==2.6.0
redis==5.0.1
```

**Required Environment Variables**:
```bash
# Supabase (for reputation system)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJhbGc...

# Redis (for cost tracking)
REDIS_URL=redis://your-redis-host:6379

# Vercel (for deployments)
VERCEL_TOKEN=your-vercel-token
VERCEL_TEAM_ID=your-team-id
```

### Agent Registration

On startup, the worker registers with the governance system:

```python
# In worker.py
self.agent_id = self.reputation_engine.get_or_create_agent('ops_agent')
```

**Agent Type**: Must be `'ops_agent'` (matches database constraint)

**Initial State**:
- Reputation Score: 100
- Permission Level: `sandbox_only`
- Allowed Operations: Read-only, test execution, sandbox deployments

### Task Execution Flow

```
1. Task received from Redis queue
   ↓
2. Budget check (daily + hourly)
   ↓
3. Permission check (based on reputation)
   ↓
4. Task execution
   ↓
5. Cost tracking
   ↓
6. Reputation event recording
```

**Example Log Output**:
```
INFO:__main__:✅ Governance modules initialized
INFO:__main__:✅ Registered with Governance (agent_id: 7df3273c-1c9c-49cf-9fb3-41d8494768d8)
INFO:__main__:   Permission Level: sandbox_only, Reputation Score: 100
INFO:__main__:✅ Budget check passed for task task-123
INFO:__main__:✅ Permission check passed for operation: deploy_sandbox
INFO:__main__:✅ Recorded reputation event: task_success
```

### Reputation Events

The worker records the following events:

| Event Type | Delta | Trigger |
|-----------|-------|---------|
| `task_success` | +2 | Task completed successfully |
| `task_failure` | -3 | Task failed |
| `budget_exceeded` | -10 | Cost budget exceeded |
| `permission_denied` | -8 | Permission check failed |

### Permission Levels

| Level | Score Range | Allowed Operations |
|-------|-------------|-------------------|
| `sandbox_only` | 0-89 | Read-only, test execution, sandbox deployments |
| `staging_access` | 90-129 | Staging deployments, non-prod changes |
| `prod_low_risk` | 130-159 | Low-risk prod changes (docs, UI) |
| `prod_full_access` | 160+ | Full production access |

### Degraded Mode

If governance registration fails, the worker operates in **degraded mode**:

**Symptoms**:
```
⚠️ Could not register with Governance (degraded mode)
```

**Impact**:
- No cost tracking
- No permission checking
- No reputation scoring
- All tasks execute without governance constraints

**Troubleshooting**:
1. Check environment variables (SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
2. Verify dependencies installed (PyYAML, supabase)
3. Check Supabase connection
4. Review worker logs for specific errors

### Monitoring

**Key Metrics**:
- Agent reputation score
- Permission level
- Task success rate
- Cost per task
- Budget utilization

**Alerts**:
- Reputation score drops below 70
- Budget exceeds 80% (warning) or 95% (critical)
- Permission denied events

### Related Documentation

- [Governance Framework](../../docs/GOVERNANCE_FRAMEWORK.md)
- [Cost Tracking](../../docs/GOVERNANCE_FRAMEWORK.md#3-cost-tracker)
- [Reputation System](../../docs/GOVERNANCE_FRAMEWORK.md#4-reputation-system)

## API Design

### Deployment Tool API
```python
deployment_tool = DeploymentTool(vercel_token="...")

# Deploy to Vercel
result = await deployment_tool.deploy(
    project="morningai",
    environment="production",
    branch="main"
)

# Check deployment status
status = await deployment_tool.get_deployment_status(deployment_id)

# Rollback deployment
rollback = await deployment_tool.rollback(deployment_id)
```

### Monitoring Tool API
```python
monitoring_tool = MonitoringTool()

# Get system metrics
metrics = await monitoring_tool.get_system_metrics()

# Check service health
health = await monitoring_tool.check_service_health(service="api")

# Set up custom metric
await monitoring_tool.add_custom_metric(
    name="api_latency",
    query="avg(response_time)"
)
```

### Log Analysis Tool API
```python
log_tool = LogAnalysisTool()

# Search logs
logs = await log_tool.search_logs(
    query="error",
    time_range="1h",
    severity="error"
)

# Analyze error patterns
patterns = await log_tool.analyze_error_patterns(time_range="24h")

# Detect anomalies
anomalies = await log_tool.detect_anomalies()
```

### Alert Management Tool API
```python
from tools.notification_service import NotificationService

# Initialize notification service
notification_service = NotificationService(
    mailtrap_token=os.getenv("Mailtrap_API_TOKEN"),
    slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL")
)

# Initialize alert tool with notification service
alert_tool = AlertManagementTool(
    notification_service=notification_service,
    default_email_recipient="ops-alerts@yourcompany.com",
    default_slack_channel="#ops-alerts"
)

# Create alert rule
rule = await alert_tool.create_alert_rule(
    name="high_error_rate",
    condition="error_rate > 5%",
    severity="critical",
    channels=["email", "slack"]
)

# Get active alerts
alerts = await alert_tool.get_active_alerts()

# Acknowledge alert
await alert_tool.acknowledge_alert(alert_id)
```

### Notification Service API
```python
from tools.notification_service import NotificationService

# Initialize service
notification_service = NotificationService(
    mailtrap_token=os.getenv("Mailtrap_API_TOKEN"),
    slack_webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
)

# Send email via Mailtrap
result = await notification_service.send_email_mailtrap(
    to="admin@example.com",
    subject="Critical Alert",
    body="CPU usage exceeded 90%"
)

# Send Slack message
result = await notification_service.send_slack_message(
    message="🔴 [CRITICAL] CPU usage exceeded 90%",
    channel="#ops-alerts"
)

# Send webhook
result = await notification_service.send_webhook(
    url="https://your-webhook-url.com/alerts",
    payload={
        "severity": "critical",
        "message": "CPU usage exceeded 90%",
        "timestamp": datetime.utcnow().isoformat()
    }
)

# Unified send_notification (recommended)
result = await notification_service.send_notification(
    channel="email",
    message="Alert message",
    to="admin@example.com",
    subject="Alert Subject"
)
```

## Development Plan

### Phase 1: Deployment Tool (Week 1)
- [ ] Implement Vercel API integration
- [ ] Add deployment management functions
- [ ] Create rollback mechanism
- [ ] Write unit and integration tests
- [ ] Document API and usage

### Phase 2: Monitoring Tool (Week 1-2)
- [ ] Implement system metrics collection
- [ ] Add health check functionality
- [ ] Create performance monitoring
- [ ] Write tests
- [ ] Document monitoring setup

### Phase 3: Log Analysis Tool (Week 2)
- [ ] Implement log collection
- [ ] Add search and filter capabilities
- [ ] Create pattern detection
- [ ] Write tests
- [ ] Document log analysis

### Phase 4: Alert Management Tool (Week 2)
- [ ] Implement alert rules engine
- [ ] Add notification channels
- [ ] Create alert history
- [ ] Write tests
- [ ] Document alert setup

### Phase 5: Integration & Testing (Week 2-3)
- [ ] Create E2E test scenarios
- [ ] Performance benchmarking
- [ ] Load testing
- [ ] Documentation completion
- [ ] Production deployment guide

## Testing Strategy

### Unit Tests
- Each tool has comprehensive unit tests
- Mock external services (Vercel API, etc.)
- Test error handling and edge cases
- Test async operations

### Integration Tests
- Test tool interactions
- Test real API calls (with test accounts)
- Test OODA Loop integration
- Test data persistence

### E2E Tests
- Full deployment workflow
- Monitoring and alerting workflow
- Log analysis workflow
- Multi-agent coordination

### Performance Tests
- Load testing (100+ concurrent requests)
- Latency benchmarks (<100ms for monitoring)
- Resource usage monitoring

## Security Considerations

- **API Key Management**: Secure storage of Vercel tokens
- **Access Control**: Role-based access to operations
- **Audit Logging**: Track all operational actions
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: Sanitize all inputs

## Usage Examples

### Example 1: Automated Deployment
```python
from ops_agent import OpsAgentOODA

ops_agent = OpsAgentOODA(
    vercel_token=os.getenv("VERCEL_TOKEN"),
    enable_monitoring=True
)

# Execute deployment task
result = await ops_agent.execute_task(
    task="Deploy latest changes to production",
    priority="high"
)

print(f"Deployment status: {result['status']}")
print(f"URL: {result['deployment_url']}")
```

### Example 2: Monitor and Alert
```python
# Set up monitoring and alerting
await ops_agent.execute_task(
    task="Monitor API error rate and alert if >5%",
    priority="critical"
)
```

### Example 3: Log Analysis
```python
# Analyze recent errors
result = await ops_agent.execute_task(
    task="Analyze error logs from the past hour and identify root causes",
    priority="medium"
)

print(f"Patterns found: {result['patterns']}")
print(f"Suggested fixes: {result['recommendations']}")
```

## Contributing

When adding new features:
1. Follow existing code structure
2. Write comprehensive tests
3. Update documentation
4. Add type hints
5. Follow Python best practices

## License

[Your License]
