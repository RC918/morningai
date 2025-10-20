# FAQ Agent REST API Documentation

## Overview

The FAQ Agent REST API provides comprehensive FAQ management capabilities including search, CRUD operations, and analytics. All endpoints support async operations and include Redis caching for optimal performance.

## Base URL

```
/api/faq
```

## Authentication

All FAQ API endpoints require JWT authentication. Include the JWT token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

**Role-Based Access Control:**
- **User/Analyst**: Can access GET endpoints (search, get FAQ, categories, stats)
- **Admin**: Can access all endpoints including POST, PUT, DELETE

**Status Codes:**
- `401 Unauthorized`: Missing or invalid JWT token
- `403 Forbidden`: Insufficient privileges (admin required)

## Endpoints

### Search FAQs

Search for FAQs using semantic or keyword search.

**Endpoint:** `GET /api/faq/search`

**Query Parameters:**
- `q` (string, required): Search query
- `page` (integer, optional): Page number (default: 1, min: 1)
- `page_size` (integer, optional): Results per page (default: 10, min: 1, max: 100)
- `category` (string, optional): Filter by category
- `sort_by` (string, optional): Sort field (created_at, updated_at)
- `sort_order` (string, optional): Sort order (asc, desc) (default: desc)

**Response:**
```json
{
  "data": {
    "query": "how to reset password",
    "results": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "question": "How do I reset my password?",
        "answer": "To reset your password...",
        "category": "account",
        "tags": ["password", "security"],
        "score": 0.95,
        "created_at": "2025-01-15T10:00:00Z",
        "updated_at": "2025-01-15T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "page_size": 10,
      "total_results": 1,
      "has_more": false
    },
    "timestamp": "2025-01-20T12:00:00Z"
  },
  "cached": false
}
```

**Status Codes:**
- `200 OK`: Search completed successfully
- `401 Unauthorized`: Missing/invalid JWT token
- `422 Unprocessable Entity`: Validation error (e.g., page_size > 100, empty query)
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Search failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
# Basic search
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "https://api.example.com/api/faq/search?q=billing&page=1&page_size=5"

# With pagination
curl -H "Authorization: Bearer $JWT_TOKEN" \
  "https://api.example.com/api/faq/search?q=billing&page=2&page_size=10&sort_order=asc"
```

---

### Get FAQ by ID

Retrieve a single FAQ by its ID.

**Endpoint:** `GET /api/faq/{id}`

**Path Parameters:**
- `id` (string, required): FAQ UUID

**Response:**
```json
{
  "faq": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "question": "What payment methods are accepted?",
    "answer": "We accept credit cards, PayPal, and bank transfers.",
    "category": "billing",
    "tags": ["payment", "billing"],
    "metadata": {},
    "view_count": 150,
    "helpful_count": 45,
    "created_at": "2025-01-15T10:00:00Z",
    "updated_at": "2025-01-15T10:00:00Z"
  },
  "cached": false,
  "timestamp": "2025-01-20T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: FAQ retrieved successfully
- `404 Not Found`: FAQ not found
- `500 Internal Server Error`: Fetch failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
curl "https://api.example.com/api/faq/550e8400-e29b-41d4-a716-446655440000"
```

---

### Create FAQ

Create a new FAQ entry.

**Endpoint:** `POST /api/faq`

**Request Body:**
```json
{
  "question": "How do I upgrade my plan?",
  "answer": "To upgrade your plan, go to Settings > Billing...",
  "category": "billing",
  "tags": ["upgrade", "plan", "billing"]
}
```

**Required Fields:**
- `question` (string): FAQ question
- `answer` (string): FAQ answer

**Optional Fields:**
- `category` (string): Category name
- `tags` (array of strings): Tags for categorization

**Response:**
```json
{
  "faq_id": "550e8400-e29b-41d4-a716-446655440001",
  "message": "FAQ created successfully",
  "timestamp": "2025-01-20T12:00:00Z"
}
```

**Status Codes:**
- `201 Created`: FAQ created successfully
- `400 Bad Request`: Invalid input
- `500 Internal Server Error`: Creation failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
curl -X POST "https://api.example.com/api/faq" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I export my data?",
    "answer": "You can export your data from Settings > Data Export",
    "category": "data",
    "tags": ["export", "data"]
  }'
```

---

### Update FAQ

Update an existing FAQ.

**Endpoint:** `PUT /api/faq/{id}`

**Path Parameters:**
- `id` (string, required): FAQ UUID

**Request Body:**
```json
{
  "question": "Updated question (optional)",
  "answer": "Updated answer (optional)",
  "category": "new-category (optional)",
  "tags": ["tag1", "tag2"]
}
```

**Note:** All fields are optional. Only provided fields will be updated.

**Response:**
```json
{
  "faq_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "FAQ updated successfully",
  "timestamp": "2025-01-20T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: FAQ updated successfully
- `400 Bad Request`: Invalid input or no fields to update
- `404 Not Found`: FAQ not found
- `500 Internal Server Error`: Update failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
curl -X PUT "https://api.example.com/api/faq/550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Updated comprehensive answer with more details..."
  }'
```

---

### Delete FAQ

Delete an FAQ entry.

**Endpoint:** `DELETE /api/faq/{id}`

**Path Parameters:**
- `id` (string, required): FAQ UUID

**Response:**
```json
{
  "faq_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "FAQ deleted successfully",
  "timestamp": "2025-01-20T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: FAQ deleted successfully
- `404 Not Found`: FAQ not found
- `500 Internal Server Error`: Deletion failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
curl -X DELETE "https://api.example.com/api/faq/550e8400-e29b-41d4-a716-446655440000"
```

---

### Get Categories

List all FAQ categories.

**Endpoint:** `GET /api/faq/categories`

**Response:**
```json
{
  "categories": [
    {
      "id": "1",
      "name": "billing",
      "description": "Billing and payment questions",
      "parent_category_id": null,
      "created_at": "2025-01-15T10:00:00Z"
    },
    {
      "id": "2",
      "name": "technical",
      "description": "Technical support questions",
      "parent_category_id": null,
      "created_at": "2025-01-15T10:00:00Z"
    }
  ],
  "count": 2,
  "cached": false,
  "timestamp": "2025-01-20T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Categories retrieved successfully
- `500 Internal Server Error`: Fetch failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
curl "https://api.example.com/api/faq/categories"
```

---

### Get Statistics

Get FAQ system statistics.

**Endpoint:** `GET /api/faq/stats`

**Response:**
```json
{
  "stats": {
    "total_faqs": 150,
    "by_category": {
      "billing": 45,
      "technical": 60,
      "general": 45
    },
    "most_viewed": [
      {
        "question": "How do I reset my password?",
        "view_count": 1250
      }
    ],
    "most_helpful": [
      {
        "question": "What payment methods are accepted?",
        "helpful_count": 234
      }
    ]
  },
  "cached": false,
  "timestamp": "2025-01-20T12:00:00Z"
}
```

**Status Codes:**
- `200 OK`: Stats retrieved successfully
- `500 Internal Server Error`: Fetch failed
- `503 Service Unavailable`: FAQ service not available

**Example:**
```bash
curl "https://api.example.com/api/faq/stats"
```

---

## Redis Caching

The FAQ API implements Redis caching for improved performance:

- **Search results**: Cached for 300 seconds (configurable via `FAQ_CACHE_TTL`)
- **Categories**: Cached for 600 seconds
- **Statistics**: Cached for 60 seconds
- **Individual FAQs**: Cached for 300 seconds

Cache is automatically invalidated when:
- A new FAQ is created (invalidates search and category caches)
- An FAQ is updated (invalidates search and FAQ caches)
- An FAQ is deleted (invalidates search and FAQ caches)

**Cache Status:**
All cached responses include a `cached: true` field to indicate cache hits.

---

## Error Handling

All endpoints return errors in the following format:

```json
{
  "error": {
    "code": "error_code",
    "message": "Human-readable error message",
    "details": {} // Optional, for validation errors
  }
}
```

**Common Error Codes:**
- `validation_error`: Request validation failed (422)
- `invalid_input`: Invalid request parameters (400)
- `not_found`: Resource not found (404)
- `create_failed`: FAQ creation failed (500)
- `update_failed`: FAQ update failed (500)
- `delete_failed`: FAQ deletion failed (500)
- `search_failed`: Search operation failed (500)
- `fetch_failed`: Data fetch failed (500)
- `service_unavailable`: FAQ service not available (503)
- `internal_error`: Unexpected server error (500)
- `rate_limit_exceeded`: Rate limit exceeded (429)

---

## Rate Limiting

Rate limiting is implemented using Redis sliding window algorithm:

- **60 requests per minute per IP** (configurable via `RATE_LIMIT_REQUESTS`)
- **60-second window** (configurable via `RATE_LIMIT_WINDOW`)

**Response when rate limit exceeded:**
```json
{
  "error": {
    "code": "rate_limit_exceeded",
    "message": "Rate limit exceeded. Maximum 60 requests per 60 seconds."
  }
}
```

**Status Code:** `429 Too Many Requests`

---

## OODA Loop Integration

The FAQ Agent uses an OODA (Observe-Orient-Decide-Act) loop for intelligent task execution:

1. **Observe**: Collect current FAQ system state and metrics
2. **Orient**: Analyze observations and formulate strategies
3. **Decide**: Select best strategy and create action plan
4. **Act**: Execute actions and collect results

This enables adaptive behavior for complex operations like:
- Quality optimization
- Category reorganization
- Bulk operations
- Analytics generation

See `faq_agent_ooda.py` for implementation details.

---

## Cost Control

The FAQ Agent implements OpenAI cost controls:

**Environment Variables:**
- `OPENAI_MAX_DAILY_COST`: Maximum daily OpenAI cost (default: $20.00)
- `FAQ_CACHE_TTL`: Cache TTL in seconds (default: 300)

**Cost Optimization:**
- Embeddings are cached to avoid regeneration
- Redis caching reduces API calls
- Batch embedding generation for bulk operations

See `COST_OPTIMIZATION_GUIDE.md` for detailed cost management strategies.

---

## Examples

### Complete Workflow Example

```bash
# 1. Create a new FAQ
FAQ_ID=$(curl -X POST "https://api.example.com/api/faq" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "How do I integrate the API?",
    "answer": "Use our REST API with your API key...",
    "category": "developer",
    "tags": ["api", "integration"]
  }' | jq -r '.faq_id')

# 2. Search for the FAQ
curl "https://api.example.com/api/faq/search?q=integrate+api"

# 3. Update the FAQ
curl -X PUT "https://api.example.com/api/faq/$FAQ_ID" \
  -H "Content-Type: application/json" \
  -d '{
    "answer": "Updated: Use our REST API with Bearer token authentication..."
  }'

# 4. Get FAQ details
curl "https://api.example.com/api/faq/$FAQ_ID"

# 5. Delete the FAQ
curl -X DELETE "https://api.example.com/api/faq/$FAQ_ID"
```

---

## Next Steps

See also:
- `README.md` - FAQ Agent overview
- `COST_OPTIMIZATION_GUIDE.md` - Cost management strategies
- `MULTILINGUAL_SUPPORT.md` - Internationalization
- `STAGING_DEPLOYMENT_REPORT.md` - Deployment guide
