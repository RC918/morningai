import { isFeatureEnabled } from './feature-flags';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

/**
 * CSRF token cache for cross-origin scenarios
 * In cross-origin requests, document.cookie cannot read cookies set by different domain
 * So we cache the token from the response body as a fallback
 */
let csrfTokenCache: string | null = null;

/**
 * Get mock data for API endpoints when OWNER_CONSOLE_API feature flag is disabled
 * Returns minimal but correct response shapes to prevent runtime errors
 */
function getMockData(url: string, _options: RequestInit = {}): any {
  // System monitoring endpoints
  if (url.includes('/api/admin/system/health')) {
    return { status: 'healthy' };
  }
  
  if (url.includes('/api/admin/system/metrics')) {
    return {
      system_health: {
        overall_status: 'healthy',
        error_rate: 0,
        avg_latency: 0,
        open_circuit_breakers: 0,
      },
      performance: {},
      breakers: [],
    };
  }
  
  if (url.includes('/api/admin/system/logs')) {
    return { items: [] };
  }
  
  // Agent endpoints
  if (url.includes('/api/admin/agents') && url.includes('/executions')) {
    return { items: [] };
  }
  
  if (url.includes('/api/admin/agents/') && !url.includes('/executions')) {
    const agentId = url.split('/api/admin/agents/')[1]?.split('/')[0] || 'mock-agent';
    return {
      id: agentId,
      name: 'Mock Agent',
      status: 'idle',
    };
  }
  
  if (url.includes('/api/admin/agents')) {
    return { items: [] };
  }
  
  // Tenant endpoints
  if (url.includes('/api/tenant/info')) {
    return { tenants: [] };
  }
  
  if (url.includes('/api/tenant/members')) {
    return { items: [] };
  }
  
  // Governance endpoints
  if (url.includes('/api/governance/agents')) {
    return { items: [] };
  }
  
  if (url.includes('/api/governance/events')) {
    return { items: [] };
  }
  
  if (url.includes('/api/governance/violations')) {
    return { items: [] };
  }
  
  if (url.includes('/api/governance/statistics')) {
    return {
      totals: {
        agents: 0,
        violations: 0,
        events: 0,
      },
    };
  }
  
  // 2FA endpoints
  if (url.includes('/api/auth/v2/totp/status')) {
    return { enabled: false };
  }
  
  if (url.includes('/api/auth/v2/totp/setup')) {
    return {
      secret: 'MOCK_SECRET_KEY',
      qr_code: 'data:image/png;base64,mock',
    };
  }
  
  if (url.includes('/api/auth/v2/totp/verify-setup')) {
    return { success: true };
  }
  
  if (url.includes('/api/auth/v2/totp/disable')) {
    return { success: true };
  }
  
  if (url.includes('/api/auth/v2/totp/backup-codes')) {
    return {
      codes: ['MOCK-CODE-1', 'MOCK-CODE-2', 'MOCK-CODE-3'],
    };
  }
  
  return {};
}

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
 * API client with automatic credentials and CSRF token injection
 * 
 * P0-3 Security Fix:
 * - Adds credentials: 'include' to send HttpOnly cookies
 * - Injects X-CSRF-Token header for POST/PUT/PATCH/DELETE requests
 * 
 * Feature Flag Support:
 * - When OWNER_CONSOLE_API is disabled, returns mock data to prevent HTTP 401 errors
 * - Mock mode is useful for development and testing without backend dependencies
 */
export async function apiClient<T>(
  url: string,
  options: RequestInit = {}
): Promise<T> {
  // Return mock data when feature flag is disabled
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    return Promise.resolve({
      data: getMockData(url, options),
      status: 200,
      headers: new Headers(),
    }) as T;
  }
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };
  
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE'];
  if (options.method && unsafeMethods.includes(options.method.toUpperCase())) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
  }
  
  const res = await fetch(`${API_BASE_URL}${url}`, {
    ...options,
    credentials: 'include',  // P0-3: Always include credentials for HttpOnly cookies
    headers,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`HTTP ${res.status} ${res.statusText} - ${text}`);
  }
  const ct = res.headers.get('content-type') || '';
  const data = ct.includes('application/json') ? await res.json() : await res.text();
  
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
 * Feature Flag Support:
 * - When OWNER_CONSOLE_API is disabled, sets a mock CSRF token instead of fetching
 */
export async function bootstrapCsrf(): Promise<void> {
  // Set mock CSRF token when feature flag is disabled
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    csrfTokenCache = 'mock-csrf-token';
    console.debug('Mock CSRF token set (OWNER_CONSOLE_API disabled)');
    return;
  }
  
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/v2/csrf`, {
      credentials: 'include',
    });
    
    if (response.ok) {
      const data = await response.json();
      if (data.csrf_token) {
        csrfTokenCache = data.csrf_token;
        console.debug('CSRF token cached from response body');
      }
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
