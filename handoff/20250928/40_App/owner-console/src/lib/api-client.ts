import { getAccessToken, getOrRefreshAccessToken, refreshAccessToken, clearTokens, clearTokensAndRedirectToLogin, RefreshAccessTokenError } from './auth.ts';

const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') || '';

/**
 * CSRF token cache for cross-origin scenarios
 * In cross-origin requests, document.cookie cannot read cookies set by different domain
 * So we cache the token from the response body as a fallback
 */
let csrfTokenCache: string | null = null;

/**
 * Get CSRF token from cache or cookie
 * Priority: cache (from response body) > cookie (for same-origin)
 */
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;
  
  if (csrfTokenCache) {
    return csrfTokenCache;
  }
  
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

/**
 * HTTP methods that require CSRF token
 */
const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/**
 * Build authentication headers for API requests
 * Shared helper to avoid duplication between apiClient and apiClientWithMeta
 */
async function buildAuthHeaders(
  method: string,
  existingHeaders?: HeadersInit
): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(existingHeaders as Record<string, string> | undefined),
  };

  if (UNSAFE_METHODS.includes(method.toUpperCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }

  // Get access token, refreshing if necessary (handles page refresh case)
  // Filter out literal "null" and "undefined" strings to prevent "Authorization: Bearer null"
  const accessToken = await getOrRefreshAccessToken();
  if (accessToken && accessToken !== 'null' && accessToken !== 'undefined') {
    headers['Authorization'] = `Bearer ${accessToken}`;
  }

  return headers;
}

/**
 * API client with automatic credentials and CSRF token injection
 * 
 * P0-3 Security Fix:
 * - Adds credentials: 'include' to send HttpOnly cookies
 * - Injects X-CSRF-Token header for POST/PUT/PATCH/DELETE requests
 * 
 * P1 Enhancement: 401 Retry Mechanism
 * - On 401 "Token expired" response, attempts to refresh token and retry request once
 * - If retry fails, clears tokens and redirects to login
 */
export async function apiClient<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  let finalUrl = url;
  
  if (!url.startsWith('/api/') && (url.startsWith('/admin') || url.startsWith('/tenant') || url.startsWith('/governance'))) {
    finalUrl = '/api' + url;
  }
  
  const method = options.method || 'GET';
  const headers = await buildAuthHeaders(method, options.headers);
  
  const res = await fetch(`${API_BASE_URL}${finalUrl}`, {
    ...options,
    credentials: 'include',  // P0-3: Always include credentials for HttpOnly cookies
    headers,
  });

  // Handle 401 responses - only retry for "Token expired" cases
  if (res.status === 401) {
    // Read the response body once to check if it's a token-expired error
    const text = typeof res.text === 'function' ? await res.text().catch(() => '') : '';
    const statusText = res.statusText || '';
    
    // Check if this is a token-expired error (not a generic 401 Unauthorized)
    const isTokenExpiredError = 
      text.toLowerCase().includes('token expired') ||
      text.toLowerCase().includes('token_expired') ||
      text.toLowerCase().includes('jwt expired');
    
    if (!isTokenExpiredError) {
      // Generic 401 - preserve original behavior, throw error without retry
      throw new Error(`HTTP 401 ${statusText} - ${text}`);
    }
    
    // Token expired - attempt refresh and retry
    try {
      // Attempt to refresh the token
      await refreshAccessToken();
      
      // Rebuild headers with new token
      const retryHeaders = await buildAuthHeaders(method, options.headers);
      
      // Retry the request once
      const retryRes = await fetch(`${API_BASE_URL}${finalUrl}`, {
        ...options,
        credentials: 'include',
        headers: retryHeaders,
      });
      
      if (retryRes.status === 401) {
        // Retry also failed - clear tokens and redirect to login
        clearTokensAndRedirectToLogin();
        const retryText = typeof retryRes.text === 'function' ? await retryRes.text().catch(() => '') : '';
        throw new Error(`HTTP 401 - Authentication failed. Please login again. ${retryText}`);
      }
      
      if (!retryRes.ok) {
        const retryText = typeof retryRes.text === 'function' ? await retryRes.text().catch(() => '') : '';
        const retryStatusText = retryRes.statusText || '';
        throw new Error(`HTTP ${retryRes.status} ${retryStatusText} - ${retryText}`);
      }
      
      const ct = retryRes.headers && typeof retryRes.headers.get === 'function' ? retryRes.headers.get('content-type') || '' : '';
      const data = ct.includes('application/json') ? await retryRes.json() : (typeof retryRes.text === 'function' ? await retryRes.text() : '');
      
      return {
        data,
        status: retryRes.status,
        headers: retryRes.headers,
      } as T;
    } catch (error) {
      // If refresh failed with session_invalid, clear tokens and redirect
      if (error instanceof RefreshAccessTokenError && error.code === 'session_invalid') {
        clearTokensAndRedirectToLogin();
      }
      throw error;
    }
  }

  if (!res.ok) {
    const text = typeof res.text === 'function' ? await res.text().catch(() => '') : '';
    const statusText = res.statusText || '';
    throw new Error(`HTTP ${res.status} ${statusText} - ${text}`);
  }
  const ct = res.headers && typeof res.headers.get === 'function' ? res.headers.get('content-type') || '' : '';
  const data = ct.includes('application/json') ? await res.json() : (typeof res.text === 'function' ? await res.text() : '');
  
  return {
    data,
    status: res.status,
    headers: res.headers,
  } as T;
}

/**
 * Bootstrap CSRF token before making authenticated requests
 * Call this on app initialization
 * 
 * P0 Fix: Cache CSRF token from response body for cross-origin scenarios
 * Backend returns { csrf_token: "..." } in response body which we can read cross-origin
 * 
 * Preview Mode: Skip CSRF bootstrap for /ux-metrics route in preview environments
 * when VITE_PREVIEW_PUBLIC_METRICS is enabled (static metrics JSON doesn't need auth)
 */
export async function bootstrapCsrf(): Promise<void> {
  if (typeof window !== 'undefined' && 
      import.meta.env.VITE_PREVIEW_PUBLIC_METRICS === 'true' &&
      window.location.pathname.startsWith('/ux-metrics')) {
    console.debug('Skipping CSRF bootstrap for /ux-metrics in preview mode');
    return;
  }

  if (!API_BASE_URL) {
    console.warn('CSRF bootstrap skipped: VITE_API_BASE_URL not configured');
    return;
  }

  try {
    const url = `${API_BASE_URL}/api/auth/v2/csrf`;
    console.debug('Bootstrapping CSRF token from:', url);
    
    const response = await fetch(url, {
      credentials: 'include',
    });
    
    const contentType = response.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      const text = await response.text();
      console.error('CSRF bootstrap failed: Expected JSON but got', contentType, 'Status:', response.status);
      console.error('Response preview:', text.substring(0, 200));
      return;
    }
    
    if (response.ok) {
      const data = await response.json();
      if (data.csrf_token) {
        csrfTokenCache = data.csrf_token;
        console.debug('CSRF token cached from response body');
      }
    } else {
      console.error('CSRF bootstrap failed with status:', response.status);
    }
  } catch (error) {
    console.warn('Failed to bootstrap CSRF token:', error);
  }
}

/**
 * Admin API methods for Owner Console
 * P0-3: System Monitoring and Agent Governance endpoints
 * 
 * Uses apiClient() to ensure:
 * - Consistent CSRF token injection for unsafe methods
 * - Proper credentials handling
 * - Future-proofing for 401 refresh/retry
 */
const adminApi = {
  getSystemHealth: async () => {
    const result = await apiClient<{ data: any }>('/api/admin/system/health', { method: 'GET' });
    return (result as any).data;
  },
  
  getSystemMetrics: async () => {
    const result = await apiClient<{ data: any }>('/api/admin/system/metrics', { method: 'GET' });
    return (result as any).data;
  },
  
  getSystemLogs: async (params: { level?: string; limit?: number; since?: string } = {}) => {
    const queryParams = new URLSearchParams();
    if (params.level) queryParams.append('level', params.level);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.since) queryParams.append('since', params.since);
    const url = `/api/admin/system/logs${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const result = await apiClient<{ data: any }>(url, { method: 'GET' });
    return (result as any).data;
  },
  
  getAgents: async (params: { status?: string; limit?: number } = {}) => {
    const queryParams = new URLSearchParams();
    if (params.status) queryParams.append('status', params.status);
    if (params.limit) queryParams.append('limit', params.limit.toString());
    const url = `/api/admin/agents${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const result = await apiClient<{ data: any }>(url, { method: 'GET' });
    return (result as any).data;
  },
  
  getAgentDetails: async (agentId: string) => {
    const result = await apiClient<{ data: any }>(`/api/admin/agents/${agentId}`, { method: 'GET' });
    return (result as any).data;
  },
  
  getAgentExecutions: async (agentId: string, params: { limit?: number; status?: string } = {}) => {
    const queryParams = new URLSearchParams();
    if (params.limit) queryParams.append('limit', params.limit.toString());
    if (params.status) queryParams.append('status', params.status);
    const url = `/api/admin/agents/${agentId}/executions${queryParams.toString() ? '?' + queryParams.toString() : ''}`;
    const result = await apiClient<{ data: any }>(url, { method: 'GET' });
    return (result as any).data;
  },
  
  pauseAgent: async (agentId: string) => {
    const result = await apiClient<{ data: any }>(`/api/admin/agents/${agentId}/pause`, { method: 'POST' });
    return (result as any).data;
  },
  
  resumeAgent: async (agentId: string) => {
    const result = await apiClient<{ data: any }>(`/api/admin/agents/${agentId}/resume`, { method: 'POST' });
    return (result as any).data;
  }
};

/**
 * Legacy Governance API methods (kept for backward compatibility)
 * These use the old /api/governance endpoints
 */
const governanceApi = {
  getGovernanceAgents: async () => {
    const result = await apiClient<{ data: any }>('/api/governance/agents', { method: 'GET' });
    return (result as any).data;
  },
  
  getGovernanceEvents: async (params: { limit?: number } = {}) => {
    const url = params.limit ? `/api/governance/events?limit=${params.limit}` : '/api/governance/events';
    const result = await apiClient<{ data: any }>(url, { method: 'GET' });
    return (result as any).data;
  },
  
  getGovernanceViolations: async (params: { limit?: number } = {}) => {
    const url = params.limit ? `/api/governance/violations?limit=${params.limit}` : '/api/governance/violations';
    const result = await apiClient<{ data: any }>(url, { method: 'GET' });
    return (result as any).data;
  },
  
  getGovernanceStatistics: async () => {
    const result = await apiClient<{ data: any }>('/api/governance/statistics', { method: 'GET' });
    return (result as any).data;
  }
};

(apiClient as any).getSystemHealth = adminApi.getSystemHealth;
(apiClient as any).getSystemMetrics = adminApi.getSystemMetrics;
(apiClient as any).getSystemLogs = adminApi.getSystemLogs;
(apiClient as any).getAgents = adminApi.getAgents;
(apiClient as any).getAgentDetails = adminApi.getAgentDetails;
(apiClient as any).getAgentExecutions = adminApi.getAgentExecutions;
(apiClient as any).pauseAgent = adminApi.pauseAgent;
(apiClient as any).resumeAgent = adminApi.resumeAgent;
(apiClient as any).getGovernanceAgents = governanceApi.getGovernanceAgents;
(apiClient as any).getGovernanceEvents = governanceApi.getGovernanceEvents;
(apiClient as any).getGovernanceViolations = governanceApi.getGovernanceViolations;
(apiClient as any).getGovernanceStatistics = governanceApi.getGovernanceStatistics;

/**
 * Custom error types for better error handling
 */
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public data?: unknown
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

export class TimeoutError extends Error {
  constructor(message: string = 'Request timeout') {
    super(message);
    this.name = 'TimeoutError';
  }
}

/**
 * API client with metadata (status, headers) for endpoints that need response metadata
 * Used by components that need to check response status or headers
 * 
 * Features:
 * - Returns response metadata (status, headers) in addition to data
 * - Automatic CSRF token handling for unsafe methods (POST, PUT, PATCH, DELETE)
 * - Configurable timeout with AbortController
 * - Typed error handling (ApiError, TimeoutError)
 * 
 * @param url - API endpoint URL (e.g., '/phase7/monitoring/dashboard')
 * @param options - Fetch options with optional timeout
 * @returns Promise with data, status, and headers
 * 
 * @example
 * ```typescript
 * // GET request (no CSRF token)
 * const result = await apiClientWithMeta<DashboardData>('/phase7/monitoring/dashboard', {
 *   method: 'GET'
 * });
 * 
 * // POST request (with CSRF token)
 * const result = await apiClientWithMeta<CreateResponse>('/admin/agents', {
 *   method: 'POST',
 *   body: JSON.stringify({ name: 'agent-1' })
 * });
 * 
 * // With custom timeout
 * const result = await apiClientWithMeta<Data>('/api/endpoint', {
 *   method: 'GET',
 *   timeout: 5000 // 5 seconds
 * });
 * ```
 */
export async function apiClientWithMeta<T>(
  url: string,
  options: RequestInit & { timeout?: number } = {}
): Promise<{ data: T; status: number; headers: Headers }> {
  const { timeout = 10000, ...fetchOptions } = options;
  
  let finalUrl = url;
  
  if (!url.startsWith('/api/') && (url.startsWith('/admin') || url.startsWith('/tenant') || url.startsWith('/governance') || url.startsWith('/phase7'))) {
    finalUrl = '/api' + url;
  }
  
  const method = (fetchOptions.method || 'GET').toUpperCase();

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeout);

  try {
    const headers = await buildAuthHeaders(method, fetchOptions.headers);
    
    const response = await fetch(API_BASE_URL + finalUrl, {
      ...fetchOptions,
      headers,
      credentials: 'include',
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (response.headers.get('X-CSRF-Token')) {
      csrfTokenCache = response.headers.get('X-CSRF-Token');
    }

    // Handle 401 responses - only retry for "Token expired" cases
    if (response.status === 401) {
      // Read the response body once to check if it's a token-expired error
      const errorData = await response.json().catch(() => ({ message: 'Unauthorized' }));
      const errorMessage = errorData.message || errorData.error || '';
      
      // Check if this is a token-expired error (not a generic 401 Unauthorized)
      const isTokenExpiredError = 
        errorMessage.toLowerCase().includes('token expired') ||
        errorMessage.toLowerCase().includes('token_expired') ||
        errorMessage.toLowerCase().includes('jwt expired');
      
      if (!isTokenExpiredError) {
        // Generic 401 - preserve original behavior, throw error without retry
        throw new ApiError(401, errorMessage || 'Unauthorized', errorData);
      }
      
      // Token expired - attempt refresh and retry
      try {
        // Attempt to refresh the token
        await refreshAccessToken();
        
        // Rebuild headers with new token
        const retryHeaders = await buildAuthHeaders(method, fetchOptions.headers);
        
        // Create new abort controller for retry
        const retryController = new AbortController();
        const retryTimeoutId = setTimeout(() => retryController.abort(), timeout);
        
        try {
          // Retry the request once
          const retryResponse = await fetch(API_BASE_URL + finalUrl, {
            ...fetchOptions,
            headers: retryHeaders,
            credentials: 'include',
            signal: retryController.signal,
          });
          
          clearTimeout(retryTimeoutId);
          
          if (retryResponse.headers.get('X-CSRF-Token')) {
            csrfTokenCache = retryResponse.headers.get('X-CSRF-Token');
          }
          
          if (retryResponse.status === 401) {
            // Retry also failed - clear tokens and redirect to login
            clearTokensAndRedirectToLogin();
            const retryErrorData = await retryResponse.json().catch(() => ({ message: 'Authentication failed' }));
            throw new ApiError(401, 'Authentication failed. Please login again.', retryErrorData);
          }
          
          if (!retryResponse.ok) {
            const retryErrorData = await retryResponse.json().catch(() => ({ message: 'Request failed' }));
            throw new ApiError(
              retryResponse.status,
              retryErrorData.message || `HTTP ${retryResponse.status}`,
              retryErrorData
            );
          }
          
          const data = await retryResponse.json();
          return {
            data,
            status: retryResponse.status,
            headers: retryResponse.headers
          };
        } catch (retryError) {
          clearTimeout(retryTimeoutId);
          throw retryError;
        }
      } catch (error) {
        // If refresh failed with session_invalid, clear tokens and redirect
        if (error instanceof RefreshAccessTokenError && error.code === 'session_invalid') {
          clearTokensAndRedirectToLogin();
        }
        throw error;
      }
    }

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: 'Request failed' }));
      throw new ApiError(
        response.status,
        errorData.message || `HTTP ${response.status}`,
        errorData
      );
    }

    const data = await response.json();
    return {
      data,
      status: response.status,
      headers: response.headers
    };
  } catch (error) {
    clearTimeout(timeoutId);
    
    if (error instanceof ApiError) {
      throw error;
    }
    
    if (error instanceof Error && error.name === 'AbortError') {
      throw new TimeoutError(`Request timeout after ${timeout}ms`);
    }
    
    throw error;
  }
}

export default apiClient;
