# Ops Agent Operations Runbook

## Table of Contents

1. [Quick Start](#quick-start)
2. [Daily Operations](#daily-operations)
3. [Incident Response](#incident-response)
4. [Deployment Procedures](#deployment-procedures)
5. [Monitoring & Alerts](#monitoring--alerts)
6. [Troubleshooting Guide](#troubleshooting-guide)
7. [Maintenance Tasks](#maintenance-tasks)
8. [Emergency Contacts](#emergency-contacts)

## Quick Start

### Prerequisites

```bash
# Required environment variables
export VERCEL_TOKEN_NEW="your-vercel-token"
export Mailtrap_API_TOKEN="your-mailtrap-token"  # Optional
export SLACK_WEBHOOK_URL="your-slack-webhook"    # Optional
export SUPABASE_URL="your-supabase-url"
export SUPABASE_SERVICE_ROLE_KEY="your-key"
```

### Health Check Commands

```bash
# Check all production endpoints
curl -I https://morningai-sandbox-dev-agent.fly.dev/health
curl -I https://morningai-sandbox-ops-agent.fly.dev/health
curl -I https://morningai-morning-ai.vercel.app

# Run Ops Agent tests
cd /home/ubuntu/repos/morningai
python -m pytest agents/ops_agent/tests/ -v

# Check system metrics
cd agents/ops_agent
python -c "
import asyncio
from tools.monitoring_tool import MonitoringTool

async def check():
    tool = MonitoringTool()
    metrics = await tool.get_system_metrics()
    print(metrics)

asyncio.run(check())
"
```

## Daily Operations

### Morning Checklist (09:00 UTC)

1. **Check System Health**
   ```bash
   # Verify all endpoints are responding
   ./scripts/health_check.sh
   ```

2. **Review Overnight Alerts**
   - Check Mailtrap inbox for critical alerts
   - Check Slack #ops-alerts channel (if configured)
   - Review deployment logs

3. **Monitor Key Metrics**
   - CPU usage < 80%
   - Memory usage < 85%
   - Disk usage < 90%
   - Active alerts = 0

4. **Database Health**
   ```bash
   # Check Supabase connection
   psql $DATABASE_URL_2 -c "SELECT version();"
   ```

### Evening Checklist (18:00 UTC)

1. **Review Day's Deployments**
   ```bash
   cd agents/ops_agent
   python -c "
   import asyncio, os
   from tools.deployment_tool import DeploymentTool
   
   async def review():
       tool = DeploymentTool(token=os.getenv('VERCEL_TOKEN_NEW'))
       result = await tool.list_deployments(limit=10)
       for dep in result['deployments']:
           print(f\"{dep['name']}: {dep['state']} - {dep['url']}\")
   
   asyncio.run(review())
   "
   ```

2. **Check Error Patterns**
   ```bash
   # Analyze logs from last 24h
   python -c "
   import asyncio
   from tools.log_analysis_tool import LogAnalysisTool
   
   async def analyze():
       tool = LogAnalysisTool()
       errors = await tool.analyze_error_patterns(time_range='24h')
       print(f\"Total errors: {errors['total_errors']}\")
       print(f\"Unique patterns: {len(errors['patterns'])}\")
   
   asyncio.run(analyze())
   "
   ```

3. **Update Status Dashboard**
   - Update team on day's incidents
   - Document any changes or issues
   - Plan tomorrow's maintenance

## Incident Response

### Severity Levels

- **P0 (Critical)**: Service down, data loss, security breach
- **P1 (High)**: Major feature broken, performance degradation >50%
- **P2 (Medium)**: Minor feature broken, performance degradation <50%
- **P3 (Low)**: Cosmetic issues, minor bugs

### P0 Incident Response

#### Step 1: Assess (5 minutes)

```bash
# Quick health check
curl -I https://morningai-sandbox-ops-agent.fly.dev/health

# Check system metrics
python -c "
import asyncio
from agents.ops_agent.tools.monitoring_tool import MonitoringTool

async def assess():
    tool = MonitoringTool()
    metrics = await tool.get_system_metrics()
    if metrics['success']:
        cpu = metrics['metrics']['cpu']['percent']
        mem = metrics['metrics']['memory']['percent']
        print(f'CPU: {cpu}%, Memory: {mem}%')
        if cpu > 90 or mem > 90:
            print('⚠️ RESOURCE CRITICAL!')

asyncio.run(assess())
"
```

#### Step 2: Communicate (Immediate)

```bash
# Send critical alert (example)
python -c "
import asyncio, os
from agents.ops_agent.tools.notification_service import NotificationService

async def alert():
    service = NotificationService(
        mailtrap_token=os.getenv('Mailtrap_API_TOKEN'),
        slack_webhook_url=os.getenv('SLACK_WEBHOOK_URL')
    )
    
    await service.send_notification(
        channel='email',
        message='P0 INCIDENT: Service degradation detected',
        to='ops-team@morningai.com',
        subject='[P0] Critical Incident'
    )
    
    await service.send_notification(
        channel='slack',
        message='🔴 P0 INCIDENT: Investigating service degradation',
        slack_channel='#ops-alerts'
    )

asyncio.run(alert())
"
```

#### Step 3: Mitigate (15-30 minutes)

Common mitigation strategies:

1. **High CPU/Memory**
   ```bash
   # Restart service
   fly restart --app morningai-sandbox-ops-agent
   
   # Scale up if needed
   fly scale count 2 --app morningai-sandbox-ops-agent
   ```

2. **Deployment Issues**
   ```bash
   # Rollback to previous version
   python -c "
   import asyncio, os
   from agents/ops_agent/tools/deployment_tool import DeploymentTool
   
   async def rollback():
       tool = DeploymentTool(token=os.getenv('VERCEL_TOKEN_NEW'))
       # Get previous deployment
       deployments = await tool.list_deployments(limit=5)
       if deployments['success'] and len(deployments['deployments']) > 1:
           prev_dep = deployments['deployments'][1]
           print(f'Rolling back to: {prev_dep[\"id\"]}')
           result = await tool.redeploy(prev_dep['id'], target='production')
           print(result)
   
   asyncio.run(rollback())
   "
   ```

3. **Database Issues**
   ```bash
   # Check connection pool
   psql $DATABASE_URL_2 -c "SELECT count(*) FROM pg_stat_activity;"
   
   # If pool exhausted, restart pooler via Supabase dashboard
   ```

#### Step 4: Resolve & Document

1. Fix root cause
2. Update runbook with new procedures
3. Post-mortem document
4. Update monitoring/alerts

### P1/P2 Incident Response

Follow same structure but with extended timelines:
- P1: Assess (15 min), Communicate (30 min), Mitigate (1-2 hours)
- P2: Assess (30 min), Communicate (1 hour), Mitigate (4 hours)

## Deployment Procedures

### Standard Deployment

#### Pre-Deployment Checklist

- [ ] All tests passing locally
- [ ] Code reviewed and approved
- [ ] Database migrations prepared (if any)
- [ ] Rollback plan documented
- [ ] Stakeholders notified

#### Deployment Steps

```bash
# 1. Backup database
pg_dump $DATABASE_URL_2 > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. Run migrations (if any)
psql $DATABASE_URL_2 -f migrations/XXX_migration.sql

# 3. Push to main (triggers auto-deploy)
git push origin main

# 4. Monitor deployment
python -c "
import asyncio, os, time
from agents.ops_agent.tools.deployment_tool import DeploymentTool

async def monitor():
    tool = DeploymentTool(token=os.getenv('VERCEL_TOKEN_NEW'))
    
    while True:
        deployments = await tool.list_deployments(limit=1)
        if deployments['success']:
            latest = deployments['deployments'][0]
            state = latest['state']
            print(f'Deployment state: {state}')
            
            if state == 'READY':
                print('✅ Deployment successful!')
                break
            elif state == 'ERROR':
                print('❌ Deployment failed!')
                break
        
        await asyncio.sleep(5)

asyncio.run(monitor())
"

# 5. Verify deployment
curl -I https://morningai-morning-ai.vercel.app
curl -I https://morningai-sandbox-ops-agent.fly.dev/health

# 6. Run smoke tests
python -m pytest agents/ops_agent/tests/test_ops_agent_e2e.py -v
```

#### Post-Deployment

1. Monitor for 30 minutes
2. Check error rates
3. Verify all features working
4. Update deployment log
5. Send success notification

### Emergency Rollback

```bash
# Quick rollback procedure
python -c "
import asyncio, os
from agents.ops_agent.tools.deployment_tool import DeploymentTool

async def emergency_rollback():
    tool = DeploymentTool(token=os.getenv('VERCEL_TOKEN_NEW'))
    
    # Get last 5 deployments
    result = await tool.list_deployments(limit=5)
    
    # Find last READY deployment
    for dep in result['deployments']:
        if dep['state'] == 'READY' and dep['environment'] == 'production':
            print(f'Rolling back to: {dep[\"id\"]} ({dep[\"created_at\"]})')
            rollback = await tool.promote_to_production(dep['id'])
            print(rollback)
            break

asyncio.run(emergency_rollback())
"
```

## Monitoring & Alerts

### Key Metrics to Monitor

1. **System Resources**
   - CPU usage
   - Memory usage
   - Disk space
   - Network throughput

2. **Application Metrics**
   - Response times
   - Error rates
   - Request volume
   - Database connections

3. **Business Metrics**
   - User sessions
   - API calls
   - Feature usage

### Alert Configuration

```yaml
# config.yaml example
alerts:
  rules:
    - name: high_cpu_usage
      condition: cpu > 80%
      severity: medium
      channels: [email, slack]
      
    - name: critical_cpu_usage
      condition: cpu > 95%
      severity: critical
      channels: [email, slack]
      
    - name: high_memory_usage
      condition: memory > 85%
      severity: medium
      channels: [email]
      
    - name: disk_space_critical
      condition: disk > 90%
      severity: high
      channels: [email, slack]
      
    - name: deployment_failure
      condition: deployment_state == ERROR
      severity: high
      channels: [email, slack]
```

### Creating New Alert Rules

```python
import asyncio
from agents.ops_agent.tools.alert_management_tool import AlertManagementTool

async def create_alert():
    tool = AlertManagementTool()
    
    await tool.create_alert_rule(
        name="custom_metric_threshold",
        condition="metric > threshold",
        severity="medium",
        channels=["email"],
        description="Alert when custom metric exceeds threshold"
    )

asyncio.run(create_alert())
```

## Troubleshooting Guide

### Common Issues

#### Issue: High CPU Usage

**Symptoms**: CPU > 80%, slow response times

**Diagnosis**:
```bash
# Check processes
top -n 1

# Check Ops Agent metrics
python -c "
import asyncio
from agents.ops_agent.ops_agent_ooda import OpsAgentOODA

async def diagnose():
    agent = OpsAgentOODA()
    result = await agent.execute_task('troubleshoot high CPU usage')
    print(result)

asyncio.run(diagnose())
"
```

**Resolution**:
1. Identify resource-heavy processes
2. Restart if necessary
3. Scale up if persistent
4. Optimize code if recurring

#### Issue: Deployment Fails

**Symptoms**: Deployment state = ERROR

**Diagnosis**:
```bash
# Get deployment logs
python -c "
import asyncio, os
from agents.ops_agent.tools.deployment_tool import DeploymentTool

async def get_logs():
    tool = DeploymentTool(token=os.getenv('VERCEL_TOKEN_NEW'))
    
    # Get latest deployment
    deployments = await tool.list_deployments(limit=1)
    if deployments['success']:
        dep_id = deployments['deployments'][0]['id']
        events = await tool.get_deployment_events(dep_id)
        print(events)

asyncio.run(get_logs())
"
```

**Resolution**:
1. Check build logs for errors
2. Verify environment variables
3. Check dependencies
4. Rollback if critical

#### Issue: Database Connection Errors

**Symptoms**: psycopg2.OperationalError, connection timeouts

**Diagnosis**:
```bash
# Test connection
psql $DATABASE_URL_2 -c "SELECT 1;"

# Check connection pool
psql $DATABASE_URL_2 -c "
SELECT count(*), state 
FROM pg_stat_activity 
GROUP BY state;
"
```

**Resolution**:
1. Check Supabase status
2. Verify credentials
3. Restart connection pooler
4. Contact Supabase support if persists

#### Issue: Email Notifications Not Sending

**Symptoms**: Alerts not received

**Diagnosis**:
```bash
# Test Mailtrap
curl -H "Authorization: Bearer $Mailtrap_API_TOKEN" \
     https://send.api.mailtrap.io/api/send \
     -X POST -H "Content-Type: application/json" \
     -d '{"from":{"email":"test@morningai.com"},"to":[{"email":"test@example.com"}],"subject":"Test","text":"Test"}'
```

**Resolution**:
1. Verify Mailtrap token is valid
2. Check token has correct permissions
3. Regenerate token if needed
4. Update VERCEL_TOKEN_NEW environment variable

## Maintenance Tasks

### Weekly Tasks

#### Monday: Review & Plan
- Review last week's incidents
- Plan this week's deployments
- Update documentation

#### Wednesday: System Cleanup
```bash
# Clean old Docker images
docker system prune -a

# Clean old logs
find /var/log -name "*.log" -mtime +30 -delete

# Vacuum database (if needed)
psql $DATABASE_URL_2 -c "VACUUM ANALYZE;"
```

#### Friday: Backup & Verify
```bash
# Full database backup
pg_dump $DATABASE_URL_2 | gzip > backup_$(date +%Y%m%d).sql.gz

# Verify backup
gunzip -c backup_$(date +%Y%m%d).sql.gz | head -100

# Upload to S3/backup storage
aws s3 cp backup_$(date +%Y%m%d).sql.gz s3://morningai-backups/
```

### Monthly Tasks

1. **Security Updates**
   - Update dependencies
   - Review access logs
   - Rotate credentials

2. **Performance Review**
   - Analyze slow queries
   - Review error patterns
   - Optimize hot paths

3. **Capacity Planning**
   - Review resource usage trends
   - Plan for growth
   - Upgrade infrastructure if needed

## Emergency Contacts

### On-Call Rotation

| Time (UTC) | Primary | Secondary |
|------------|---------|-----------|
| 00:00-08:00 | Ryan Chen | Devin AI |
| 08:00-16:00 | Ryan Chen | Devin AI |
| 16:00-00:00 | Ryan Chen | Devin AI |

### Escalation Path

1. **Level 1**: On-call engineer
2. **Level 2**: Team lead
3. **Level 3**: Engineering manager
4. **Level 4**: CTO

### External Vendors

- **Vercel Support**: https://vercel.com/support
- **Supabase Support**: https://supabase.com/support
- **Mailtrap Support**: https://mailtrap.io/support
- **Fly.io Support**: https://fly.io/docs/about/support/

---

## Appendix

### Useful Commands Reference

```bash
# Quick health check
curl -I https://morningai-sandbox-ops-agent.fly.dev/health

# Run all tests
python -m pytest agents/ops_agent/tests/ -v

# Check logs
fly logs --app morningai-sandbox-ops-agent

# SSH to server
fly ssh console --app morningai-sandbox-ops-agent

# Database query
psql $DATABASE_URL_2

# Monitor resources
htop

# Network diagnostics
netstat -tulpn

# Disk usage
df -h
```

### Version History

- **v1.0.0** (2025-10-19): Initial release
  - 4 core tools implemented
  - Notification service
  - OODA Loop orchestrator
  - 110 tests (100% passing)

---

**Last Updated**: October 19, 2025
**Maintained By**: Ops Team
**Review Frequency**: Monthly
