# Morning AI API Specifications

## Overview
This document provides comprehensive API specifications for the Morning AI Phase 1-3 functionality, including the newly implemented endpoints for multi-tenant architecture, AI agent binding, bot creation, and subscription management.

## Base URL
- **Development**: `http://127.0.0.1:10000`
- **Production**: `https://morningai-backend-v2.onrender.com`

## Authentication
All API endpoints use standard HTTP authentication. Include authentication headers as required by your deployment environment.

## Health Check Endpoints

### GET /health
Returns comprehensive system health information.

**Response:**
```json
{
  "service": "morningai-backend",
  "status": "healthy",
  "environment": "production",
  "phase": "Phase 8: Self-service Dashboard & Reporting Center",
  "app_version": "8.0.0",
  "database_status": "connected",
  "security_status": "available",
  "timestamp": "2025-09-29T19:28:13.123456"
}
```

### GET /healthz
Kubernetes-style health check endpoint with same response format as `/health`.

## Phase 2 Endpoints - Multi-tenant Architecture

### POST /api/agents/bind
AI Agent Assisted Binding - Bind AI agents to tenant platforms with 95%+ success rate.

**Request Body:**
```json
{
  "tenant_id": "string (required)",
  "platform_type": "string (required)",
  "credentials": {
    "api_key": "string",
    "webhook_url": "string"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "AI Agent binding completed successfully",
  "data": {
    "binding_id": "bind_tenant_001_1727640493",
    "tenant_id": "tenant_001",
    "platform_type": "slack",
    "status": "success",
    "success_rate": 0.95,
    "binding_time": "2025-09-29T19:28:13.123456",
    "ai_assistance": true,
    "conversation_flow": {
      "steps_completed": 4,
      "total_steps": 4,
      "automated_fields": ["api_key", "webhook_url", "permissions"],
      "user_confirmations": ["terms_accepted", "data_sharing_consent"]
    }
  }
}
```

**Error Responses:**
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Server processing error

### POST /api/tenants/isolate
Multi-tenant Data Isolation - Configure tenant-specific data isolation.

**Request Body:**
```json
{
  "tenant_id": "string (required)",
  "isolation_level": "string (default: 'schema')"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Tenant data isolation configured successfully",
  "data": {
    "tenant_id": "tenant_001",
    "isolation_level": "schema",
    "status": "isolated",
    "created_at": "2025-09-29T19:28:13.123456",
    "database_schema": "tenant_tenant_001",
    "security_policies": [
      "row_level_security",
      "encrypted_at_rest",
      "audit_logging",
      "access_control"
    ],
    "resource_limits": {
      "max_storage_gb": 100,
      "max_api_calls_per_hour": 1000,
      "max_concurrent_users": 50
    }
  }
}
```

## Phase 3 Endpoints - AI Bot Creation & Payment Integration

### POST /api/bots/create
AI Bot Generator - Create customized AI bots for tenants.

**Request Body:**
```json
{
  "bot_name": "string (required)",
  "bot_type": "string (default: 'general')",
  "tenant_id": "string (required)",
  "customization": {
    "personality": "string",
    "language": "string",
    "response_style": "string"
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "AI Bot created successfully",
  "data": {
    "bot_id": "bot_tenant_001_1727640493",
    "bot_name": "Customer Support Bot",
    "bot_type": "customer_service",
    "tenant_id": "tenant_001",
    "status": "created",
    "created_at": "2025-09-29T19:28:13.123456",
    "customization": {
      "personality": "friendly",
      "language": "en",
      "response_style": "professional"
    },
    "capabilities": [
      "natural_language_processing",
      "context_awareness",
      "multi_platform_integration",
      "custom_workflows"
    ],
    "deployment_status": "staging",
    "performance_metrics": {
      "response_time_ms": 150,
      "accuracy_rate": 0.92,
      "user_satisfaction": 0.88
    }
  }
}
```

### POST /api/subscriptions/create
Subscription Management - Create and manage tenant subscriptions with Stripe integration.

**Request Body:**
```json
{
  "tenant_id": "string (required)",
  "plan_type": "string (default: 'basic')",
  "payment_method": "string"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Subscription created successfully",
  "data": {
    "subscription_id": "sub_tenant_001_1727640493",
    "tenant_id": "tenant_001",
    "plan_type": "professional",
    "status": "active",
    "created_at": "2025-09-29T19:28:13.123456",
    "billing_cycle": "monthly",
    "amount": 99.99,
    "currency": "USD",
    "stripe_integration": {
      "customer_id": "cus_tenant_001",
      "payment_method_id": "pm_test_card_visa",
      "invoice_settings": "auto_charge",
      "trial_period_days": 14
    },
    "features": {
      "ai_agents": 25,
      "api_calls_per_month": 100000,
      "custom_integrations": true,
      "priority_support": true
    }
  }
}
```

## Dashboard and Reporting Endpoints

### GET /api/dashboard/data
Get real-time dashboard data for monitoring and analytics.

**Query Parameters:**
- `hours`: Number of hours of data to retrieve (default: 1)

**Response:**
```json
{
  "system_metrics": {
    "cpu_usage": 72,
    "memory_usage": 68,
    "response_time": 145,
    "error_rate": 0.02,
    "active_strategies": 12,
    "pending_approvals": 3,
    "cost_today": 45.67
  },
  "task_execution": {
    "recent_tasks": [
      {
        "name": "AI策略優化",
        "status": "completed",
        "duration": "2.3s",
        "agent": "GrowthStrategist"
      }
    ],
    "total_tasks_today": 47,
    "success_rate": 0.96,
    "avg_duration": "3.2s"
  }
}
```

### POST /api/reports/generate
Generate custom reports in various formats.

**Request Body:**
```json
{
  "type": "string (default: 'performance')",
  "time_range": "string (default: '24h')",
  "format": "string (default: 'json')"
}
```

**Supported Report Types:**
- `performance`: System performance metrics
- `task_tracking`: AI agent task execution
- `resilience`: System resilience patterns
- `financial`: Cost analysis

**Supported Formats:**
- `json`: JSON response
- `pdf`: PDF download
- `csv`: CSV download

## Error Handling

All endpoints follow consistent error response format:

```json
{
  "error": "Error message description",
  "code": "ERROR_CODE",
  "timestamp": "2025-09-29T19:28:13.123456"
}
```

**Common HTTP Status Codes:**
- `200 OK`: Successful request
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `405 Method Not Allowed`: HTTP method not supported
- `500 Internal Server Error`: Server processing error

## Rate Limiting

API endpoints are subject to rate limiting based on tenant subscription:

- **Basic Plan**: 1,000 requests/hour
- **Professional Plan**: 10,000 requests/hour
- **Enterprise Plan**: 100,000 requests/hour

Rate limit headers are included in responses:
- `X-RateLimit-Limit`: Request limit per hour
- `X-RateLimit-Remaining`: Remaining requests
- `X-RateLimit-Reset`: Reset time (Unix timestamp)

## Data Models

### Tenant
```json
{
  "tenant_id": "string",
  "name": "string",
  "status": "active|suspended|inactive",
  "created_at": "ISO 8601 timestamp",
  "subscription": {
    "plan_type": "basic|professional|enterprise",
    "status": "active|trial|expired"
  }
}
```

### AI Agent Binding
```json
{
  "binding_id": "string",
  "tenant_id": "string",
  "platform_type": "string",
  "status": "success|failed|pending",
  "success_rate": "number (0-1)",
  "binding_time": "ISO 8601 timestamp"
}
```

### AI Bot
```json
{
  "bot_id": "string",
  "bot_name": "string",
  "bot_type": "string",
  "tenant_id": "string",
  "status": "created|training|deployed|inactive",
  "capabilities": ["string"],
  "performance_metrics": {
    "response_time_ms": "number",
    "accuracy_rate": "number (0-1)",
    "user_satisfaction": "number (0-1)"
  }
}
```

## SDK and Integration Examples

### JavaScript/Node.js
```javascript
const morningAI = new MorningAIClient({
  baseURL: 'https://morningai-backend-v2.onrender.com',
  apiKey: 'your-api-key'
});

// Bind AI agent
const binding = await morningAI.agents.bind({
  tenant_id: 'tenant_001',
  platform_type: 'slack',
  credentials: {
    api_key: 'slack-api-key',
    webhook_url: 'https://hooks.slack.com/webhook'
  }
});

// Create AI bot
const bot = await morningAI.bots.create({
  bot_name: 'Support Bot',
  tenant_id: 'tenant_001',
  customization: {
    personality: 'helpful',
    language: 'en'
  }
});
```

### Python
```python
from morningai_client import MorningAIClient

client = MorningAIClient(
    base_url='https://morningai-backend-v2.onrender.com',
    api_key='your-api-key'
)

# Create subscription
subscription = client.subscriptions.create(
    tenant_id='tenant_001',
    plan_type='professional',
    payment_method='pm_test_card'
)
```

## Testing and Development

### Local Development
```bash
# Start local server
cd handoff/20250928/40_App/api-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
gunicorn -w 2 -b 0.0.0.0:10000 src.main:app
```

### Testing Endpoints
```bash
# Test health endpoint
curl http://127.0.0.1:10000/health

# Test AI agent binding
curl -X POST http://127.0.0.1:10000/api/agents/bind \
  -H "Content-Type: application/json" \
  -d '{"tenant_id": "test", "platform_type": "slack"}'

# Test bot creation
curl -X POST http://127.0.0.1:10000/api/bots/create \
  -H "Content-Type: application/json" \
  -d '{"bot_name": "Test Bot", "tenant_id": "test"}'
```

## Deployment Configuration

### Environment Variables
```bash
# Required
DATABASE_URL=sqlite:///phase7_state.db
APP_VERSION=8.0.0
APP_PHASE=8
PHASE_BANNER="Phase 8: Self-service Dashboard & Reporting Center"

# Optional
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-your-key
SENTRY_DSN=https://your-sentry-dsn
CORS_ORIGINS=http://localhost:5173
```

### Render Deployment
```yaml
services:
  - type: web
    name: morningai-backend-v2
    env: python
    runtime: python-3.11
    buildCommand: |
      cd handoff/20250928/40_App/api-backend &&
      pip install --upgrade pip &&
      pip install -r requirements.txt
    startCommand: cd handoff/20250928/40_App/api-backend/src && gunicorn --bind 0.0.0.0:$PORT --timeout 120 --workers 1 main:app
```

## Support and Troubleshooting

### Common Issues
1. **405 Method Not Allowed**: Ensure you're using the correct HTTP method (POST for creation endpoints)
2. **400 Bad Request**: Check that all required fields are included in request body
3. **500 Internal Server Error**: Check server logs for detailed error information

### Monitoring
- Health endpoints: `/health` and `/healthz`
- Monitoring dashboard: `/api/dashboard/data`
- System metrics: Available through monitoring endpoints

### Contact
For API support and questions:
- Documentation: This specification document
- Issues: GitHub repository issues
- Monitoring: Built-in monitoring and alerting system
