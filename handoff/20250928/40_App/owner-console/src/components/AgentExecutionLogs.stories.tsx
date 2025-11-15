import React from 'react';
import { http, HttpResponse } from 'msw';
import AgentExecutionLogs from './AgentExecutionLogs';

export default {
  title: 'Components/AgentExecutionLogs',
  component: AgentExecutionLogs,
  parameters: {
    layout: 'fullscreen',
  },
};

export const InitialLoading = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/admin/agent-execution-logs', async () => {
          await new Promise(resolve => setTimeout(resolve, 1500));
          return HttpResponse.json({});
        }),
      ],
    },
  },
};

export const WithSuccessfulExecutions = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/admin/agent-execution-logs', () => {
          return HttpResponse.json({
            execution_logs: [
              {
                task_id: 'task-001',
                status: 'completed',
                task_type: 'create_pr',
                agent: {
                  agent_type: 'dev_agent',
                  reputation_score: 150
                },
                tenant_id: 'tenant-001',
                duration_ms: 5000,
                timestamps: {
                  created_at: '2025-11-15T10:00:00Z',
                  started_at: '2025-11-15T10:00:05Z',
                  completed_at: '2025-11-15T10:00:10Z',
                  updated_at: '2025-11-15T10:00:10Z'
                }
              },
              {
                task_id: 'task-002',
                status: 'completed',
                task_type: 'deploy',
                agent: {
                  agent_type: 'ops_agent',
                  reputation_score: 180
                },
                tenant_id: 'tenant-002',
                duration_ms: 8000,
                timestamps: {
                  created_at: '2025-11-15T10:05:00Z',
                  started_at: '2025-11-15T10:05:02Z',
                  completed_at: '2025-11-15T10:05:10Z',
                  updated_at: '2025-11-15T10:05:10Z'
                }
              },
              {
                task_id: 'task-003',
                status: 'completed',
                task_type: 'update_docs',
                agent: {
                  agent_type: 'pm_agent',
                  reputation_score: 120
                },
                tenant_id: 'tenant-001',
                duration_ms: 3000,
                timestamps: {
                  created_at: '2025-11-15T10:10:00Z',
                  started_at: '2025-11-15T10:10:01Z',
                  completed_at: '2025-11-15T10:10:04Z',
                  updated_at: '2025-11-15T10:10:04Z'
                }
              }
            ],
            summary: {
              total_executions: 3,
              success_rate: 100,
              avg_duration_ms: 5333,
              status_counts: {
                completed: 3
              }
            },
            pagination: {
              total_items: 3,
              total_pages: 1
            }
          });
        }),
      ],
    },
  },
};

export const WithMixedStatuses = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/admin/agent-execution-logs', () => {
          return HttpResponse.json({
            execution_logs: [
              {
                task_id: 'task-001',
                status: 'running',
                task_type: 'create_pr',
                agent: {
                  agent_type: 'dev_agent',
                  reputation_score: 150
                },
                tenant_id: 'tenant-001',
                timestamps: {
                  created_at: '2025-11-15T10:00:00Z',
                  started_at: '2025-11-15T10:00:05Z',
                  updated_at: '2025-11-15T10:00:10Z'
                }
              },
              {
                task_id: 'task-002',
                status: 'failed',
                task_type: 'deploy',
                agent: {
                  agent_type: 'ops_agent',
                  reputation_score: 180
                },
                tenant_id: 'tenant-002',
                duration_ms: 2000,
                error_message: 'Deployment failed: connection timeout',
                timestamps: {
                  created_at: '2025-11-15T10:05:00Z',
                  started_at: '2025-11-15T10:05:02Z',
                  completed_at: '2025-11-15T10:05:04Z',
                  updated_at: '2025-11-15T10:05:04Z'
                }
              },
              {
                task_id: 'task-003',
                status: 'queued',
                task_type: 'update_docs',
                agent: {
                  agent_type: 'pm_agent',
                  reputation_score: 120
                },
                tenant_id: 'tenant-001',
                timestamps: {
                  created_at: '2025-11-15T10:10:00Z',
                  updated_at: '2025-11-15T10:10:00Z'
                }
              },
              {
                task_id: 'task-004',
                status: 'completed',
                task_type: 'create_pr',
                agent: {
                  agent_type: 'dev_agent',
                  reputation_score: 150
                },
                tenant_id: 'tenant-003',
                duration_ms: 6000,
                timestamps: {
                  created_at: '2025-11-15T10:15:00Z',
                  started_at: '2025-11-15T10:15:02Z',
                  completed_at: '2025-11-15T10:15:08Z',
                  updated_at: '2025-11-15T10:15:08Z'
                }
              },
              {
                task_id: 'task-005',
                status: 'cancelled',
                task_type: 'deploy',
                agent: {
                  agent_type: 'ops_agent',
                  reputation_score: 180
                },
                tenant_id: 'tenant-002',
                duration_ms: 1000,
                timestamps: {
                  created_at: '2025-11-15T10:20:00Z',
                  started_at: '2025-11-15T10:20:01Z',
                  completed_at: '2025-11-15T10:20:02Z',
                  updated_at: '2025-11-15T10:20:02Z'
                }
              }
            ],
            summary: {
              total_executions: 5,
              success_rate: 40,
              avg_duration_ms: 3750,
              status_counts: {
                running: 1,
                failed: 1,
                queued: 1,
                completed: 1,
                cancelled: 1
              }
            },
            pagination: {
              total_items: 5,
              total_pages: 1
            }
          });
        }),
      ],
    },
  },
};

export const ErrorState = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/admin/agent-execution-logs', () => {
          return HttpResponse.json(
            { error: 'Failed to fetch execution logs' },
            { status: 500 }
          );
        }),
      ],
    },
  },
};

export const EmptyState = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/admin/agent-execution-logs', () => {
          return HttpResponse.json({
            execution_logs: [],
            summary: {
              total_executions: 0,
              success_rate: 0,
              avg_duration_ms: 0,
              status_counts: {}
            },
            pagination: {
              total_items: 0,
              total_pages: 0
            }
          });
        }),
      ],
    },
  },
};

export const WithPagination = {
  parameters: {
    msw: {
      handlers: [
        http.get('*/api/admin/agent-execution-logs', () => {
          return HttpResponse.json({
            execution_logs: Array.from({ length: 10 }, (_, i) => ({
              task_id: `task-${String(i + 1).padStart(3, '0')}`,
              status: ['completed', 'running', 'failed', 'queued'][i % 4],
              task_type: ['create_pr', 'deploy', 'update_docs'][i % 3],
              agent: {
                agent_type: ['dev_agent', 'ops_agent', 'pm_agent'][i % 3],
                reputation_score: 100 + (i * 10)
              },
              tenant_id: `tenant-${String((i % 3) + 1).padStart(3, '0')}`,
              duration_ms: 1000 + (i * 500),
              timestamps: {
                created_at: new Date(Date.now() - (i * 300000)).toISOString(),
                started_at: new Date(Date.now() - (i * 300000) + 5000).toISOString(),
                completed_at: new Date(Date.now() - (i * 300000) + 10000).toISOString(),
                updated_at: new Date(Date.now() - (i * 300000) + 10000).toISOString()
              }
            })),
            summary: {
              total_executions: 50,
              success_rate: 75,
              avg_duration_ms: 4500,
              status_counts: {
                completed: 25,
                running: 10,
                failed: 10,
                queued: 5
              }
            },
            pagination: {
              total_items: 50,
              total_pages: 5
            }
          });
        }),
      ],
    },
  },
};
