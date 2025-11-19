import { http, HttpResponse, delay } from 'msw';

export const handlers = [
  http.get('*/api/auth/v2/csrf', async () => {
    return HttpResponse.json({ token: 'test-csrf-token' });
  }),

  http.post('*/api/auth/v2/refresh', async () => {
    return HttpResponse.json({ ok: true });
  }),

  http.get('*/api/admin/system/health', async () => {
    await delay(1500);
    return HttpResponse.json({
      data: {
        status: 'healthy',
        uptime_seconds: 86400,
        services: {
          database: { status: 'healthy', response_time_ms: 15 },
          redis: { status: 'healthy', response_time_ms: 5 },
          api: { status: 'healthy', response_time_ms: 20 },
        },
      },
    });
  }),

  http.get('*/api/admin/system/metrics', async () => {
    await delay(1500);
    return HttpResponse.json({
      data: {
        cpu_usage: 45.2,
        memory_usage: 62.8,
        disk_usage: 38.5,
        request_rate: 150,
      },
    });
  }),

  http.get('*/api/admin/agent-execution-logs', async () => {
    await delay(1500);
    return HttpResponse.json({
      execution_logs: [
        {
          task_id: 'task-001',
          status: 'completed',
          task_type: 'code_review',
          agent: { agent_type: 'dev_agent', reputation_score: 150 },
          duration_ms: 5000,
          timestamps: {
            created_at: '2024-01-15T10:00:00Z',
            completed_at: '2024-01-15T10:00:05Z',
          },
        },
      ],
      summary: {
        total_executions: 1,
        success_rate: 100,
        avg_duration_ms: 5000,
      },
      pagination: {
        total_items: 1,
        total_pages: 1,
      },
    });
  }),

  http.get('*/api/admin/agent-stats', async () => {
    await delay(1500);
    return HttpResponse.json({
      data: {
        total_agents: 5,
        active_agents: 3,
        total_tasks: 100,
        success_rate: 95,
      },
    });
  }),
];
