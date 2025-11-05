/**
 * API Client for Owner Console
 * 
 * Issue #767: API Connection
 * Squad: Owner Console Squad
 * 
 * Week 0 P0-4: Feature flag OWNER_CONSOLE_API removed - Owner Console now always uses real API.
 * Mock data has been removed. Real backend configuration is required.
 * 
 * This module provides typed API clients for all Owner Console endpoints:
 * - Agents API (Issue #769)
 * - Tenants API (Issue #770)
 * - Monitoring API (Issue #771)
 * - Settings API (Issue #772)
 * - Security API (Issue #773)
 * 
 * @see docs/PARALLEL_DEVELOPMENT_STRATEGY.md
 */

import { authenticatedFetch } from '../auth';
import { apiClient as apiClientFunction } from '../api-client';


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

export { apiClientFunction as apiClient };


export interface PaginationParams {
  page?: number;
  pageSize?: number;
}

export interface PaginationResponse<T> {
  items: T[];
  pagination: {
    page: number;
    pageSize: number;
    totalItems: number;
    totalPages: number;
  };
}

export interface ApiError {
  code: string;
  message: string;
  details?: Record<string, any>;
}


/**
 * Build URL with query parameters
 */
function buildUrl(path: string, params?: Record<string, any>): string {
  const url = new URL(`${API_BASE_URL}${path}`);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.append(key, String(value));
      }
    });
  }
  
  return url.toString();
}

/**
 * Handle API response
 */
async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error: ApiError = await response.json().catch(() => ({
      code: 'unknown_error',
      message: `HTTP ${response.status} ${response.statusText}`,
    }));
    
    throw new Error(error.message);
  }
  
  const contentType = response.headers.get('content-type');
  
  if (contentType?.includes('application/json')) {
    return response.json();
  }
  
  return response.text() as any;
}

/**
 * Make authenticated GET request
 */
async function get<T>(path: string, params?: Record<string, any>): Promise<T> {
  const url = buildUrl(path, params);
  const response = await authenticatedFetch(url, {
    method: 'GET',
  });
  
  return handleResponse<T>(response);
}

/**
 * Make authenticated POST request
 */
async function post<T>(path: string, data?: any): Promise<T> {
  const url = buildUrl(path);
  const response = await authenticatedFetch(url, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

/**
 * Make authenticated PATCH request
 */
async function patch<T>(path: string, data?: any): Promise<T> {
  const url = buildUrl(path);
  const response = await authenticatedFetch(url, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: data ? JSON.stringify(data) : undefined,
  });
  
  return handleResponse<T>(response);
}

/**
 * Make authenticated DELETE request
 */
async function del<T>(path: string): Promise<T> {
  const url = buildUrl(path);
  const response = await authenticatedFetch(url, {
    method: 'DELETE',
  });
  
  return handleResponse<T>(response);
}


export interface Agent {
  agentId: string;
  agentType: 'dev_agent' | 'ops_agent' | 'pm_agent' | 'growth_strategist' | 'meta_agent';
  status: 'active' | 'idle' | 'busy' | 'offline' | 'error';
  permissionLevel: 'sandbox_only' | 'staging_access' | 'prod_low_risk' | 'prod_full_access';
  reputationScore: number;
  capabilities: string[];
  metadata?: Record<string, any>;
  createdAt: string;
  lastActivity: string;
  statistics?: {
    prMergedCount: number;
    prRevertedCount: number;
    testPassCount: number;
    testFailCount: number;
    testPassRate: number;
  };
}

export const agentsApi = {
  /**
   * List all agents
   */
  list: (params?: PaginationParams & {
    agentType?: string;
    status?: string;
    permissionLevel?: string;
  }): Promise<PaginationResponse<Agent>> => {
    return get('/api/v1/agents', params);
  },
  
  /**
   * Get agent by ID
   */
  get: (agentId: string): Promise<Agent> => {
    return get(`/api/v1/agents/${agentId}`);
  },
  
  /**
   * Update agent
   */
  update: (agentId: string, data: Partial<Agent>): Promise<Agent> => {
    return patch(`/api/v1/agents/${agentId}`, data);
  },
  
  /**
   * Delete agent
   */
  delete: (agentId: string): Promise<void> => {
    return del(`/api/v1/agents/${agentId}`);
  },
};


export interface Tenant {
  tenantId: string;
  name: string;
  planTier: 'free' | 'starter' | 'professional' | 'enterprise';
  status: 'active' | 'suspended' | 'cancelled';
  quota: {
    maxAgents: number;
    maxTasksPerMonth: number;
    maxStorageGB: number;
  };
  usage: {
    activeAgents: number;
    tasksThisMonth: number;
    storageUsedGB: number;
  };
  createdAt: string;
  updatedAt: string;
}

export const tenantsApi = {
  /**
   * List all tenants
   */
  list: (params?: PaginationParams & {
    planTier?: string;
    status?: string;
  }): Promise<PaginationResponse<Tenant>> => {
    return get('/api/v1/tenants', params);
  },
  
  /**
   * Get tenant by ID
   */
  get: (tenantId: string): Promise<Tenant> => {
    return get(`/api/v1/tenants/${tenantId}`);
  },
  
  /**
   * Update tenant
   */
  update: (tenantId: string, data: Partial<Tenant>): Promise<Tenant> => {
    return patch(`/api/v1/tenants/${tenantId}`, data);
  },
  
  /**
   * Suspend tenant
   */
  suspend: (tenantId: string, reason: string): Promise<Tenant> => {
    return post(`/api/v1/tenants/${tenantId}/suspend`, { reason });
  },
  
  /**
   * Reactivate tenant
   */
  reactivate: (tenantId: string): Promise<Tenant> => {
    return post(`/api/v1/tenants/${tenantId}/reactivate`);
  },
};


export interface SystemMetrics {
  timestamp: string;
  cpu: {
    usage: number;
    cores: number;
  };
  memory: {
    used: number;
    total: number;
    percentage: number;
  };
  disk: {
    used: number;
    total: number;
    percentage: number;
  };
  network: {
    bytesSent: number;
    bytesReceived: number;
  };
}

export interface ServiceHealth {
  service: string;
  status: 'healthy' | 'degraded' | 'down';
  uptime: number;
  lastCheck: string;
  details?: Record<string, any>;
}

export const monitoringApi = {
  /**
   * Get system metrics
   */
  getMetrics: (params?: {
    service?: string;
    timeRange?: string;
  }): Promise<SystemMetrics[]> => {
    return get('/api/v1/monitoring/metrics', params);
  },
  
  /**
   * Get service health
   */
  getHealth: (): Promise<ServiceHealth[]> => {
    return get('/api/v1/monitoring/health');
  },
  
  /**
   * Get alerts
   */
  getAlerts: (params?: PaginationParams & {
    severity?: string;
    status?: string;
  }): Promise<PaginationResponse<any>> => {
    return get('/api/v1/monitoring/alerts', params);
  },
};


export interface PlatformSettings {
  security: {
    mfaRequired: boolean;
    sessionTimeout: number;
    passwordPolicy: {
      minLength: number;
      requireUppercase: boolean;
      requireLowercase: boolean;
      requireNumbers: boolean;
      requireSpecialChars: boolean;
    };
  };
  agents: {
    defaultPermissionLevel: string;
    autoApproveThreshold: number;
    sandboxTimeout: number;
  };
  billing: {
    currency: string;
    billingCycle: 'monthly' | 'annual';
  };
}

export const settingsApi = {
  /**
   * Get platform settings
   */
  get: (): Promise<PlatformSettings> => {
    return get('/api/v1/settings');
  },
  
  /**
   * Update platform settings
   */
  update: (data: Partial<PlatformSettings>): Promise<PlatformSettings> => {
    return patch('/api/v1/settings', data);
  },
};


export interface AuditLog {
  id: string;
  timestamp: string;
  userId: string;
  userEmail: string;
  action: string;
  resource: string;
  resourceId: string;
  details: Record<string, any>;
  ipAddress: string;
  userAgent: string;
}

export const securityApi = {
  /**
   * Get audit logs
   */
  getAuditLogs: (params?: PaginationParams & {
    userId?: string;
    action?: string;
    resource?: string;
    startDate?: string;
    endDate?: string;
  }): Promise<PaginationResponse<AuditLog>> => {
    return get('/api/v1/security/audit-logs', params);
  },
  
  /**
   * Get security events
   */
  getSecurityEvents: (params?: PaginationParams & {
    severity?: string;
    status?: string;
  }): Promise<PaginationResponse<any>> => {
    return get('/api/v1/security/events', params);
  },
};


export const api = {
  agents: agentsApi,
  tenants: tenantsApi,
  monitoring: monitoringApi,
  settings: settingsApi,
  security: securityApi,
};

export default api;
