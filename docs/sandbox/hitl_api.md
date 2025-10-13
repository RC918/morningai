# HITL (Human-in-the-Loop) Approval API

## Overview
REST API endpoints for managing approval requests that require human intervention. All endpoints require JWT authentication with analyst or admin roles.

## Authentication
All endpoints require a valid JWT token with analyst or admin role:
```bash
Authorization: Bearer <JWT_TOKEN>
```

## API Endpoints

### GET /api/hitl/requests
Get all pending approval requests.

**Authentication:** JWT token with analyst/admin role

**Query Parameters:**
- `priority` (optional): Filter by priority (critical/high/medium/low)

**Response (200):**
```json
{
  "requests": [
    {
      "request_id": "uuid",
      "trace_id": "trace_20251014_123456_abc",
      "title": "High-risk shell command approval",
      "description": "Request to execute 'rm -rf /tmp/test'",
      "context": {...},
      "requester_agent": "ops-agent-001",
      "priority": "high",
      "created_at": "2025-10-14T10:30:00",
      "expires_at": "2025-10-14T18:30:00",
      "status": "pending"
    }
  ],
  "total_count": 5,
  "filtered_by_priority": "high"
}
```

### GET /api/hitl/requests/{request_id}
Get details for a specific approval request.

**Authentication:** JWT token with analyst/admin role

**Response (200):**
```json
{
  "request_id": "uuid",
  "trace_id": "trace_20251014_123456_abc",
  "title": "High-risk shell command approval",
  "description": "Request to execute 'rm -rf /tmp/test'",
  "context": {...},
  "prompt_details": "{\n  \"command\": \"rm -rf /tmp/test\",\n  \"agent\": \"ops-agent-001\"\n}",
  "requester_agent": "ops-agent-001",
  "priority": "high",
  "created_at": "2025-10-14T10:30:00",
  "expires_at": "2025-10-14T18:30:00",
  "status": "pending"
}
```

**Response (404):**
```json
{
  "error": {
    "code": "request_not_found",
    "message": "Request {request_id} not found"
  }
}
```

### POST /api/hitl/approve/{request_id}
Approve an approval request. Records approver username and timestamp for audit trail.

**Authentication:** JWT token with analyst/admin role

**Request Body:**
```json
{
  "comments": "Approved after security review"
}
```

**Response (200):**
```json
{
  "request_id": "uuid",
  "status": "approved",
  "approved_by": "admin",
  "approved_at": "2025-10-14T10:35:00",
  "comments": "Approved after security review"
}
```

**Response (404):**
```json
{
  "error": {
    "code": "approval_failed",
    "message": "Request not found or already processed/expired"
  }
}
```

### POST /api/hitl/reject/{request_id}
Reject an approval request. Comments (rejection reason) are required.

**Authentication:** JWT token with analyst/admin role

**Request Body:**
```json
{
  "comments": "Security risk too high - potential data loss"
}
```

**Response (200):**
```json
{
  "request_id": "uuid",
  "status": "rejected",
  "rejected_by": "admin",
  "rejected_at": "2025-10-14T10:35:00",
  "comments": "Security risk too high - potential data loss"
}
```

**Response (400):**
```json
{
  "error": {
    "code": "invalid_input",
    "message": "Rejection reason (comments) is required"
  }
}
```

### GET /api/hitl/history
Get approval history with optional filters.

**Authentication:** JWT token with analyst/admin role

**Query Parameters:**
- `limit` (optional): Max results to return (default: 100)
- `status` (optional): Filter by status (approved/rejected/expired)

**Response (200):**
```json
{
  "history": [
    {
      "request_id": "uuid",
      "trace_id": "trace_20251014_123456_abc",
      "title": "High-risk shell command approval",
      "requester_agent": "ops-agent-001",
      "priority": "high",
      "status": "approved",
      "created_at": "2025-10-14T10:30:00",
      "approved_by": "admin",
      "approved_at": "2025-10-14T10:35:00",
      "approval_channel": "console",
      "comments": "Approved after security review"
    }
  ],
  "total_count": 25,
  "limit": 100,
  "filtered_by_status": null
}
```

### GET /api/hitl/status
Get HITL system status including pending request counts by priority.

**Authentication:** JWT token with analyst/admin role

**Response (200):**
```json
{
  "total_pending": 5,
  "by_priority": {
    "critical": 1,
    "high": 2,
    "medium": 2,
    "low": 0
  },
  "total_processed_today": 12,
  "system_health": "operational"
}
```

## Security Features

### JWT Authentication
- All endpoints require valid JWT token
- Token must include `analyst` or `admin` role
- Expired or invalid tokens return 401 Unauthorized

### Role-Based Access Control
- **Analyst Role**: Can view, approve, and reject approval requests
- **Admin Role**: Full access to all HITL operations
- Other roles (e.g., `user`) are denied access with 403 Forbidden

### Audit Trail
- All approval/rejection actions record:
  - Approver username (from JWT token)
  - Approval/rejection timestamp
  - Comments/reason
  - Approval channel (console/telegram)
- Audit log stored in Redis for persistence
- trace_id propagated through all operations for Sentry tracking

### Request Validation
- Rejection requires mandatory `comments` field
- Request IDs validated before processing
- Duplicate processing prevented (request can only be approved/rejected once)

## Integration with HITL Approval System

This API wraps the existing `HITLApprovalSystem` backend:
- **File:** `/home/ubuntu/repos/morningai/hitl_approval_system.py`
- **Dual-channel support:** Console + Telegram Bot notifications
- **Priority-based timeouts:**
  - Critical: 2 hours
  - High: 8 hours
  - Medium: 24 hours
  - Low: 72 hours
- **Persistent state:** Redis-backed storage via `persistent_state_manager`

## Usage Examples

### Get pending requests
```bash
curl http://localhost:5000/api/hitl/requests \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Approve a request
```bash
curl -X POST http://localhost:5000/api/hitl/approve/abc-123 \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comments": "Approved after review"}'
```

### Reject a request
```bash
curl -X POST http://localhost:5000/api/hitl/reject/abc-123 \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"comments": "Security risk too high"}'
```

### Get approval history
```bash
curl "http://localhost:5000/api/hitl/history?limit=50&status=approved" \
  -H "Authorization: Bearer $JWT_TOKEN"
```

### Get system status
```bash
curl http://localhost:5000/api/hitl/status \
  -H "Authorization: Bearer $JWT_TOKEN"
```

## Testing

A demo script is provided at `/scripts/demo_hitl_api.sh`:

```bash
# Set JWT token (requires admin login)
export JWT_TOKEN=$(curl -s http://localhost:5000/api/auth/login \
  -d '{"email":"admin@example.com","password":"..."}' \
  -H 'Content-Type: application/json' | jq -r '.access_token')

# Run demo
./scripts/demo_hitl_api.sh
```

## Error Handling

All errors return consistent JSON format:
```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message"
  }
}
```

**Common error codes:**
- `authorization_missing` (401): JWT token not provided
- `invalid_token` (401): JWT token expired or invalid
- `insufficient_privileges` (403): User role not allowed
- `request_not_found` (404): Approval request not found
- `invalid_input` (400): Required field missing or invalid
- `approval_failed` (500): Internal error during approval
- `retrieval_failed` (500): Internal error retrieving data

## References

- **HITL Backend:** `/hitl_approval_system.py`
- **Auth Middleware:** `/handoff/20250928/40_App/api-backend/src/middleware/auth_middleware.py`
- **Demo Script:** `/scripts/demo_hitl_api.sh`
- **Issue:** [#200 - HITL Gate](https://github.com/RC918/morningai/issues/200)
