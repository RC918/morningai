import { http, HttpResponse } from 'msw';

export const handlers = [
  http.get('/api/monitoring/system-health', () => {
    return HttpResponse.json({
      status: 'healthy',
      uptime: 86400,
      memory: {
        used: 512,
        total: 1024,
        percentage: 50
      },
      cpu: {
        usage: 25
      },
      services: {
        database: 'healthy',
        redis: 'healthy',
        queue: 'healthy'
      }
    });
  }),

  http.get('/api/monitoring/metrics', () => {
    return HttpResponse.json({
      activeAgents: 5,
      queueDepth: 12,
      tasksCompleted: 150,
      averageResponseTime: 2.5
    });
  }),

  http.get('/api/admin/agent-execution-logs', () => {
    return HttpResponse.json({
      logs: [
        {
          id: '1',
          agent_type: 'dev_agent',
          task_type: 'create_pr',
          status: 'completed',
          created_at: '2025-11-15T10:00:00Z',
          completed_at: '2025-11-15T10:05:00Z',
          duration: 300,
          trace_id: 'trace-001'
        },
        {
          id: '2',
          agent_type: 'ops_agent',
          task_type: 'deploy',
          status: 'running',
          created_at: '2025-11-15T10:10:00Z',
          trace_id: 'trace-002'
        }
      ],
      total: 2,
      page: 1,
      pageSize: 10
    });
  }),

  http.get('/api/admin/agent-stats', () => {
    return HttpResponse.json({
      totalExecutions: 150,
      successRate: 92.5,
      averageDuration: 245,
      activeAgents: 5
    });
  })
];
