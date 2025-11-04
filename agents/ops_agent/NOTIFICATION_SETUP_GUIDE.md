# Notification Service Setup Guide

## Quick Start

The Ops Agent notification service supports multiple channels: Email (Mailtrap/SMTP), Slack, and Webhooks.

## Configuration

### 1. Email via Mailtrap (Recommended for Production)

```bash
# Set in environment or .env file
export Mailtrap_API_TOKEN="your-mailtrap-token"
```

### 2. Email via SMTP (Fallback)

```bash
export SMTP_HOST="smtp.gmail.com"
export SMTP_PORT=587
export SMTP_USER="your-email@gmail.com"
export SMTP_PASSWORD="your-app-password"
```

### 3. Slack

```bash
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

## Usage Examples

### Basic Email Notification

```python
import os
from agents.ops_agent.tools.notification_service import NotificationService

# Initialize service
notification_service = NotificationService(
    mailtrap_token=os.getenv("Mailtrap_API_TOKEN")
)

# Send email
result = await notification_service.send_email_mailtrap(
    to="ops-team@yourcompany.com",
    subject="[CRITICAL] High CPU Usage Alert",
    body="CPU usage has exceeded 90% for the last 5 minutes."
)

if result['success']:
    print("✅ Email sent successfully")
else:
    print(f"❌ Failed: {result['error']}")
```

### Slack Notification

```python
# Initialize with Slack webhook
notification_service = NotificationService(
    slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL")
)

# Send to Slack
result = await notification_service.send_slack_message(
    message="🔴 [CRITICAL] CPU usage at 95%",
    channel="#ops-alerts"
)
```

### Webhook Notification

```python
# Send to custom webhook
result = await notification_service.send_webhook(
    url="https://your-webhook-endpoint.com/alerts",
    payload={
        "severity": "critical",
        "message": "High CPU usage detected",
        "value": 95,
        "timestamp": datetime.utcnow().isoformat()
    }
)
```

### Unified API (Recommended)

```python
# Send to any channel using unified API
result = await notification_service.send_notification(
    channel="email",  # or "slack", "webhook"
    message="Alert message",
    to="admin@example.com",
    subject="Alert Subject"
)
```

## Integration with Alert Management

```python
from agents.ops_agent.tools.notification_service import NotificationService
from agents.ops_agent.tools.alert_management_tool import AlertManagementTool

# Setup notification service
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
await alert_tool.create_alert_rule(
    name="high_cpu_usage",
    condition="cpu > 80%",
    severity="critical",
    channels=["email", "slack"]  # Multi-channel alerts
)

# When alert is triggered, notifications are sent automatically
await alert_tool.trigger_alert(
    rule_id="rule_001",
    message="CPU usage at 85%",
    metadata={"cpu_percent": 85}
)
```

## Testing Notifications

### Test Email

```python
import asyncio
from agents.ops_agent.tools.notification_service import NotificationService

async def test_email():
    service = NotificationService(
        mailtrap_token=os.getenv("Mailtrap_API_TOKEN")
    )
    
    result = await service.send_email_mailtrap(
        to="test@example.com",
        subject="Test Notification",
        body="This is a test email from Ops Agent"
    )
    
    print("Result:", result)

asyncio.run(test_email())
```

### Test Slack

```python
async def test_slack():
    service = NotificationService(
        slack_webhook_url=os.getenv("SLACK_WEBHOOK_URL")
    )
    
    result = await service.send_slack_message(
        message="🧪 Test notification from Ops Agent",
        channel="#test"
    )
    
    print("Result:", result)

asyncio.run(test_slack())
```

## Troubleshooting

### Email Not Sending

1. **Check Mailtrap token**:
   ```bash
   echo $Mailtrap_API_TOKEN
   ```

2. **Verify token in Mailtrap dashboard**:
   - Go to https://mailtrap.io
   - Check API tokens section
   - Ensure token has `emails:send` permission

3. **Check error response**:
   ```python
   result = await service.send_email_mailtrap(...)
   print(result)  # Check 'error' field
   ```

### Slack Not Receiving

1. **Verify webhook URL**:
   ```bash
   echo $SLACK_WEBHOOK_URL
   # Should start with: https://hooks.slack.com/services/
   ```

2. **Test webhook directly**:
   ```bash
   curl -X POST $SLACK_WEBHOOK_URL \
     -H 'Content-Type: application/json' \
     -d '{"text":"Test message"}'
   ```

3. **Check Slack app configuration**:
   - Ensure webhook is enabled
   - Verify channel permissions

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Mailtrap token not configured` | Missing environment variable | Set `Mailtrap_API_TOKEN` |
| `Slack webhook URL not configured` | Missing environment variable | Set `SLACK_WEBHOOK_URL` |
| `403 Forbidden` | Invalid token/webhook | Regenerate token/webhook |
| `401 Unauthorized` | Expired credentials | Update credentials |

## Best Practices

### 1. Use Environment Variables
Never hardcode credentials:
```python
# ✅ Good
token = os.getenv("Mailtrap_API_TOKEN")

# ❌ Bad
token = "abc123xyz..."
```

### 2. Handle Failures Gracefully
```python
result = await notification_service.send_notification(...)

if not result['success']:
    logger.error(f"Notification failed: {result['error']}")
    # Fallback to alternative channel
    await send_fallback_notification()
```

### 3. Rate Limiting
Avoid sending too many notifications:
```python
from datetime import datetime, timedelta

last_alert = None
min_interval = timedelta(minutes=5)

def should_send_alert():
    global last_alert
    now = datetime.now()
    
    if last_alert is None or (now - last_alert) > min_interval:
        last_alert = now
        return True
    return False
```

### 4. Test in Staging First
Always test new notification configurations in staging before production.

### 5. Monitor Notification Delivery
Track delivery success rates:
```python
stats = {
    'total': 0,
    'success': 0,
    'failed': 0
}

result = await send_notification(...)
stats['total'] += 1
if result['success']:
    stats['success'] += 1
else:
    stats['failed'] += 1

print(f"Success rate: {stats['success'] / stats['total'] * 100}%")
```

## Production Checklist

- [ ] Mailtrap token configured
- [ ] Slack webhook URL configured (if using Slack)
- [ ] Test notifications sent successfully
- [ ] Default recipients configured
- [ ] Alert rules created
- [ ] Rate limiting implemented
- [ ] Error handling in place
- [ ] Monitoring enabled
- [ ] Fallback channels configured
- [ ] Documentation updated

## Support

For issues or questions:
1. Check logs: `tail -f /var/log/ops-agent.log`
2. Review configuration: `cat config.yaml`
3. Test connection: Run test scripts above
4. Contact: ops-team@yourcompany.com

## References

- [Mailtrap API Documentation](https://api-docs.mailtrap.io/)
- [Slack Incoming Webhooks](https://api.slack.com/messaging/webhooks)
- [Ops Agent README](./README.md)
- [Configuration Example](./config.example.yaml)
