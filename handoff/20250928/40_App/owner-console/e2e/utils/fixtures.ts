/**
 * Test fixtures for E2E tests
 * Provides mock data for AgentExecutionLogs and SystemMonitoring components
 */

export const mockExecutionLogsResponse = {
  execution_logs: [
    {
      task_id: '123e4567-e89b-12d3-a456-426614174000',
      status: 'completed',
      task_type: 'faq_generation',
      agent: { 
        agent_type: 'faq_agent', 
        reputation_score: 750 
      },
      tenant_id: '00000000-0000-0000-0000-000000000001',
      duration_ms: 45000,
      timestamps: {
        created_at: '2025-11-18T10:00:00Z',
        started_at: '2025-11-18T10:00:05Z',
        completed_at: '2025-11-18T10:00:45Z',
      },
      trace_id: 'trace-123e4567-e89b-12d3-a456-426614174000',
      pr_url: 'https://github.com/RC918/morningai/pull/1234',
    },
    {
      task_id: '223e4567-e89b-12d3-a456-426614174001',
      status: 'running',
      task_type: 'code_review',
      agent: { 
        agent_type: 'dev_agent', 
        reputation_score: 820 
      },
      tenant_id: '00000000-0000-0000-0000-000000000001',
      duration_ms: null,
      timestamps: {
        created_at: '2025-11-18T10:05:00Z',
        started_at: '2025-11-18T10:05:10Z',
      },
      trace_id: 'trace-223e4567-e89b-12d3-a456-426614174001',
    },
    {
      task_id: '323e4567-e89b-12d3-a456-426614174002',
      status: 'failed',
      task_type: 'deployment',
      agent: { 
        agent_type: 'ops_agent', 
        reputation_score: 680 
      },
      tenant_id: '00000000-0000-0000-0000-000000000002',
      duration_ms: 12000,
      timestamps: {
        created_at: '2025-11-18T09:50:00Z',
        started_at: '2025-11-18T09:50:05Z',
        completed_at: '2025-11-18T09:50:17Z',
      },
      trace_id: 'trace-323e4567-e89b-12d3-a456-426614174002',
      error_message: 'Deployment failed: Connection timeout to production server',
    },
    {
      task_id: '423e4567-e89b-12d3-a456-426614174003',
      status: 'queued',
      task_type: 'analytics',
      agent: { 
        agent_type: 'pm_agent', 
        reputation_score: 710 
      },
      tenant_id: '00000000-0000-0000-0000-000000000001',
      duration_ms: null,
      timestamps: {
        created_at: '2025-11-18T10:10:00Z',
      },
      trace_id: 'trace-423e4567-e89b-12d3-a456-426614174003',
    },
    {
      task_id: '523e4567-e89b-12d3-a456-426614174004',
      status: 'cancelled',
      task_type: 'data_migration',
      agent: { 
        agent_type: 'ops_agent', 
        reputation_score: 690 
      },
      tenant_id: '00000000-0000-0000-0000-000000000003',
      duration_ms: 8000,
      timestamps: {
        created_at: '2025-11-18T09:45:00Z',
        started_at: '2025-11-18T09:45:05Z',
        completed_at: '2025-11-18T09:45:13Z',
      },
      trace_id: 'trace-523e4567-e89b-12d3-a456-426614174004',
    },
  ],
  summary: {
    total_executions: 42,
    success_rate: 0.857,
    avg_duration_ms: 38500,
    status_counts: {
      completed: 36,
      failed: 4,
      running: 2,
    },
  },
  pagination: {
    total_items: 42,
    total_pages: 1,
  },
}

export const mockExecutionLogsResponsePage2 = {
  execution_logs: [
    {
      task_id: '623e4567-e89b-12d3-a456-426614174005',
      status: 'completed',
      task_type: 'testing',
      agent: { 
        agent_type: 'dev_agent', 
        reputation_score: 800 
      },
      tenant_id: '00000000-0000-0000-0000-000000000001',
      duration_ms: 32000,
      timestamps: {
        created_at: '2025-11-18T09:30:00Z',
        completed_at: '2025-11-18T09:30:32Z',
      },
      trace_id: 'trace-623e4567-e89b-12d3-a456-426614174005',
    },
  ],
  summary: {
    total_executions: 42,
    success_rate: 0.857,
    avg_duration_ms: 38500,
    status_counts: {
      completed: 36,
      failed: 4,
      running: 2,
    },
  },
  pagination: {
    total_items: 42,
    total_pages: 2,
  },
}

export const mockExecutionLogsFilteredByStatus = {
  execution_logs: [
    {
      task_id: '123e4567-e89b-12d3-a456-426614174000',
      status: 'completed',
      task_type: 'faq_generation',
      agent: { 
        agent_type: 'faq_agent', 
        reputation_score: 750 
      },
      tenant_id: '00000000-0000-0000-0000-000000000001',
      duration_ms: 45000,
      timestamps: {
        created_at: '2025-11-18T10:00:00Z',
        completed_at: '2025-11-18T10:00:45Z',
      },
      trace_id: 'trace-123e4567-e89b-12d3-a456-426614174000',
    },
  ],
  summary: {
    total_executions: 36,
    success_rate: 1.0,
    avg_duration_ms: 42000,
    status_counts: {
      completed: 36,
    },
  },
  pagination: {
    total_items: 36,
    total_pages: 1,
  },
}

export const mockHealthResponse = {
  status: 'healthy',
  uptime_hours: 72.5,
  services: {
    database: 'healthy',
    redis: 'healthy',
    orchestrator: 'healthy',
  },
}

export const mockHealthResponseDegraded = {
  status: 'degraded',
  uptime_hours: 48.2,
  services: {
    database: 'healthy',
    redis: 'degraded',
    orchestrator: 'healthy',
  },
}

export const mockMetricsResponse = {
  cpu: { 
    usage_percent: 45.2, 
    count: 4 
  },
  memory: { 
    usage_percent: 62.8, 
    used_gb: 5.0, 
    total_gb: 8.0 
  },
  disk: { 
    usage_percent: 38.5, 
    used_gb: 77.0, 
    total_gb: 200.0 
  },
}

export const mockMetricsResponseHighUsage = {
  cpu: { 
    usage_percent: 89.5, 
    count: 4 
  },
  memory: { 
    usage_percent: 94.2, 
    used_gb: 7.5, 
    total_gb: 8.0 
  },
  disk: { 
    usage_percent: 82.1, 
    used_gb: 164.2, 
    total_gb: 200.0 
  },
}

/**
 * Helper to stub Math.random for deterministic chart generation
 */
export function stubMathRandom(page: any) {
  return page.addInitScript(() => {
    Math.random = () => 0.5
  })
}

/**
 * Helper to disable animations for stable screenshots
 */
export function disableAnimations(page: any) {
  return page.addStyleTag({
    content: '*, *::before, *::after { animation: none !important; transition: none !important; }'
  })
}

/**
 * Helper to grant clipboard permissions
 */
export async function grantClipboardPermissions(context: any) {
  await context.grantPermissions(['clipboard-read', 'clipboard-write'])
}

/**
 * Mock data for governance endpoints
 */
export const mockGovernanceEvents = {
  events: [],
  count: 0
}

export const mockGovernanceViolations = {
  violations: [],
  count: 0
}

export const mockGovernanceStatistics = {
  reputation: {},
  costs: {
    daily: {
      usage: {}
    }
  },
  timestamp: {}
}

/**
 * Helper to stub CSRF endpoint
 * Tests if CSRF token fetch is blocking app initialization
 */
export async function stubCsrfEndpoint(page: any) {
  await page.route('**/api/auth/v2/csrf', route =>
    route.fulfill({ 
      status: 200, 
      contentType: 'application/json', 
      body: JSON.stringify({ csrf_token: 'test-csrf-token' }) 
    })
  )
}

/**
 * Mock data for admin agents endpoint
 */
export const mockAdminAgents = {
  agents: [],
  count: 0
}

/**
 * Helper to stub governance API endpoints that return 503 in CI
 * These endpoints lack ALLOW_GOVERNANCE_MOCK support, so we stub them at the test layer
 */
export async function stubGovernanceEndpoints(page: any) {
  await page.route('**/*', route => {
    const url = route.request().url()
    if (url.includes('agent-execution-logs')) {
      console.log('[CATCH-ALL HIT] agent-execution-logs:', url)
    }
    route.continue()
  })
  
  await page.route('**/api/admin/agent-execution-logs*', route => {
    const url = route.request().url()
    console.log('[MOCK GLOB] Intercepted agent-execution-logs:', url)
    
    if (url.includes('page=2')) {
      route.fulfill({ 
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExecutionLogsResponsePage2) 
      })
    } else if (url.includes('status=completed')) {
      route.fulfill({ 
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExecutionLogsFilteredByStatus) 
      })
    } else {
      route.fulfill({ 
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify(mockExecutionLogsResponse) 
      })
    }
  })
  
  await page.route(/\/api\/admin\/agents(\?.*)?$/, route => {
    console.log('[MOCK] Intercepted /api/admin/agents')
    route.fulfill({ 
      status: 200, 
      contentType: 'application/json', 
      body: JSON.stringify(mockAdminAgents) 
    })
  })
  
  await page.route(/\/api\/governance\/events(\?.*)?$/, route => {
    console.log('[MOCK] Intercepted /api/governance/events')
    route.fulfill({ 
      status: 200, 
      contentType: 'application/json', 
      body: JSON.stringify(mockGovernanceEvents) 
    })
  })
  
  await page.route(/\/api\/governance\/violations(\?.*)?$/, route => {
    console.log('[MOCK] Intercepted /api/governance/violations')
    route.fulfill({ 
      status: 200, 
      contentType: 'application/json', 
      body: JSON.stringify(mockGovernanceViolations) 
    })
  })
  
  await page.route(/\/api\/governance\/statistics(\?.*)?$/, route => {
    console.log('[MOCK] Intercepted /api/governance/statistics')
    route.fulfill({ 
      status: 200, 
      contentType: 'application/json', 
      body: JSON.stringify(mockGovernanceStatistics) 
    })
  })
}

/**
 * Helper to add diagnostic logging for debugging E2E test failures
 */
export async function addDiagnosticLogging(page: any) {
  page.on('request', (request: any) => {
    const url = request.url()
    if (url.includes('/agent-execution-logs')) {
      console.log('[REQ]', request.method(), url)
    }
  })
  
  page.on('console', (msg: any) => {
    const type = msg.type()
    if (type === 'error' || type === 'warning') {
      console.log(`[Browser ${type}]:`, msg.text())
    }
  })
  
  page.on('pageerror', (error: any) => {
    console.log('[Page Error]:', error.message)
  })
  
  page.on('requestfailed', (request: any) => {
    console.log('[Request Failed]:', request.url(), request.failure()?.errorText)
  })
  
  page.on('response', async (response: any) => {
    if (response.status() >= 400) {
      const url = response.url()
      const status = response.status()
      console.log(`[API Error ${status}]:`, url)
      
      if (status === 401 && url.includes('/api/')) {
        try {
          const body = await response.text()
          console.log(`[401 Response Body]:`, body.substring(0, 500))
        } catch (e) {
          console.log('[401 Response Body]: <unable to read>')
        }
      }
    }
  })
}
