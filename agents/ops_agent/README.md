# Ops Agent - Operations and Deployment Management

## Overview

Ops Agent is responsible for automated operations, deployment management, system monitoring, log analysis, and alert management. It integrates with Vercel for deployment operations and provides comprehensive operational capabilities.

## Architecture

```
ops_agent/
├── README.md                          # This file
├── ops_agent_ooda.py                  # Main OODA Loop implementation
├── tools/                             # Core tools
│   ├── __init__.py
│   ├── deployment_tool.py             # Vercel deployment management
│   ├── monitoring_tool.py             # System monitoring
│   ├── log_analysis_tool.py           # Log analysis
│   └── alert_management_tool.py       # Alert management
├── sandbox/                           # Sandbox environment
│   ├── ops_agent_sandbox.py          # Existing sandbox
│   └── mcp/                          # MCP tools
├── tests/                            # Test suite
│   ├── test_deployment_tool.py
│   ├── test_monitoring_tool.py
│   ├── test_log_analysis_tool.py
│   ├── test_alert_management_tool.py
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
alert_tool = AlertManagementTool()

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
