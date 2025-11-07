# API Client Library

This directory contains the API client utilities for making HTTP requests to the backend API.

## Overview

The library provides two main functions for making API requests:

1. **`apiClient`** - Standard API client for typical JSON endpoints
2. **`apiClientWithMeta`** - Enhanced API client that returns response metadata (status, headers)

## When to Use Each Client

### Use `apiClient` when:
- You only need the response data
- You don't need to inspect HTTP status codes or headers
- Standard error handling is sufficient

### Use `apiClientWithMeta` when:
- You need to check the HTTP status code (e.g., handling 404 differently from 500)
- You need to inspect response headers (e.g., rate limiting, pagination)
- You need to handle redirects or check for specific status codes
- You want more control over error handling with typed errors

## Features

### CSRF Token Handling
Both clients automatically handle CSRF tokens for cross-origin requests:
- **Safe methods (GET, HEAD, OPTIONS)**: No CSRF token added
- **Unsafe methods (POST, PUT, PATCH, DELETE)**: CSRF token automatically added to `X-CSRF-Token` header
- Tokens are cached from response headers for subsequent requests

### Timeout Support
`apiClientWithMeta` includes configurable timeout support:
- Default timeout: 10 seconds
- Uses `AbortController` to cancel requests
- Throws `TimeoutError` when timeout is exceeded

### Error Handling
`apiClientWithMeta` provides typed error classes:
- **`ApiError`**: HTTP errors with status code and response data
- **`TimeoutError`**: Request timeout errors

## Usage Examples

### Basic GET Request with `apiClient`

```typescript
import { apiClient } from './lib/api-client';

// Simple GET request
const data = await apiClient('/api/admin/agents', { method: 'GET' });
console.log(data);
```

### GET Request with `apiClientWithMeta`

```typescript
import { apiClientWithMeta } from './lib/api-client';

// GET request with status checking (no CSRF token added)
const result = await apiClientWithMeta<DashboardData>('/phase7/monitoring/dashboard', {
  method: 'GET'
});

if (result.status === 200) {
  console.log('Success:', result.data);
} else if (result.status === 404) {
  console.log('Not found');
}
```

### POST Request with `apiClientWithMeta`

```typescript
import { apiClientWithMeta } from './lib/api-client';

// POST request (CSRF token automatically added)
const result = await apiClientWithMeta<CreateResponse>('/admin/agents', {
  method: 'POST',
  body: JSON.stringify({ name: 'agent-1', type: 'worker' })
});

console.log('Created:', result.data);
```

### Custom Timeout

```typescript
import { apiClientWithMeta } from './lib/api-client';

// Request with 5-second timeout
try {
  const result = await apiClientWithMeta<Data>('/api/slow-endpoint', {
    method: 'GET',
    timeout: 5000 // 5 seconds
  });
  console.log(result.data);
} catch (error) {
  if (error instanceof TimeoutError) {
    console.error('Request timed out');
  }
}
```

### Error Handling

```typescript
import { apiClientWithMeta, ApiError, TimeoutError } from './lib/api-client';

try {
  const result = await apiClientWithMeta<Data>('/api/endpoint', {
    method: 'GET'
  });
  console.log(result.data);
} catch (error) {
  if (error instanceof ApiError) {
    console.error(`HTTP ${error.status}: ${error.message}`);
    console.error('Response data:', error.data);
  } else if (error instanceof TimeoutError) {
    console.error('Request timed out');
  } else {
    console.error('Unknown error:', error);
  }
}
```

## API Reference

### `apiClient<T>(url: string, options?: RequestInit): Promise<T>`

Standard API client for typical JSON endpoints.

**Parameters:**
- `url`: API endpoint URL (e.g., `/api/admin/agents`)
- `options`: Standard `fetch` options (method, headers, body, etc.)

**Returns:** Promise resolving to the response data

**Features:**
- Automatic CSRF token injection for unsafe methods
- Credentials included for HttpOnly cookies
- Automatic `/api` prefix for admin/tenant/governance routes

### `apiClientWithMeta<T>(url: string, options?: RequestInit & { timeout?: number }): Promise<{ data: T; status: number; headers: Headers }>`

Enhanced API client with response metadata.

**Parameters:**
- `url`: API endpoint URL (e.g., `/phase7/monitoring/dashboard`)
- `options`: Fetch options with optional timeout
  - `timeout`: Request timeout in milliseconds (default: 10000)

**Returns:** Promise resolving to an object with:
- `data`: Response data of type T
- `status`: HTTP status code
- `headers`: Response headers

**Features:**
- All features of `apiClient`
- Returns response metadata (status, headers)
- Configurable timeout with AbortController
- Typed error handling (ApiError, TimeoutError)
- CSRF token only added for unsafe methods (POST, PUT, PATCH, DELETE)

### Error Classes

#### `ApiError`

Thrown when the API returns an error response.

**Properties:**
- `status`: HTTP status code
- `message`: Error message
- `data`: Response data (if available)

#### `TimeoutError`

Thrown when a request exceeds the configured timeout.

**Properties:**
- `message`: Timeout error message

## Best Practices

1. **Use `apiClient` by default** for simple requests where you only need the data
2. **Use `apiClientWithMeta`** when you need to:
   - Check specific status codes (404, 401, etc.)
   - Inspect response headers
   - Handle timeouts explicitly
   - Get structured error information

3. **Set appropriate timeouts** for long-running operations:
   ```typescript
   // For potentially slow endpoints
   const result = await apiClientWithMeta('/api/heavy-computation', {
     method: 'POST',
     timeout: 30000 // 30 seconds
   });
   ```

4. **Handle errors appropriately**:
   ```typescript
   try {
     const result = await apiClientWithMeta('/api/endpoint', { method: 'GET' });
     // Handle success
   } catch (error) {
     if (error instanceof ApiError) {
       // Handle API errors
     } else if (error instanceof TimeoutError) {
       // Handle timeout
     }
   }
   ```

## Security

- **CSRF Protection**: Automatically handled for unsafe methods (POST, PUT, PATCH, DELETE)
- **Credentials**: Always included (`credentials: 'include'`) for HttpOnly cookie support
- **Token Caching**: CSRF tokens are cached from response headers for cross-origin scenarios

## Testing

When testing components that use these clients, you can mock them:

```typescript
import { vi } from 'vitest';
import * as apiClient from './lib/api-client';

// Mock apiClientWithMeta
vi.spyOn(apiClient, 'apiClientWithMeta').mockResolvedValue({
  data: { /* mock data */ },
  status: 200,
  headers: new Headers()
});
```

For timeout testing, you can use a short timeout value:

```typescript
// This will timeout quickly in tests
const result = await apiClientWithMeta('/api/endpoint', {
  method: 'GET',
  timeout: 1 // 1ms timeout for testing
});
```
