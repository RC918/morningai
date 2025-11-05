import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MetricsDashboard } from '../MetricsDashboard';

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, params?: any) => {
      const translations: Record<string, string> = {
        'metricsDashboard.title': 'Metrics Dashboard',
        'metricsDashboard.subtitle': 'Real-time system performance and agent monitoring',
        'metricsDashboard.loadingMetrics': 'Loading metrics...',
        'metricsDashboard.error': 'Error',
        'metricsDashboard.devMode.title': 'Development Mode - Mock Data',
        'metricsDashboard.devMode.description': 'This dashboard is displaying simulated data for development purposes only. Real metrics will be available once the monitoring backend is deployed.',
        'metricsDashboard.devMode.warning': 'Do not use this data for production decisions.',
        'metricsDashboard.autoRefresh': `Auto-refresh: ${params?.status || ''}`,
        'metricsDashboard.autoRefreshOn': 'ON',
        'metricsDashboard.autoRefreshOff': 'OFF',
        'metricsDashboard.metrics.apiRequestRate': 'API Request Rate',
        'metricsDashboard.metrics.apiRequestRateDesc': 'Requests per minute',
        'metricsDashboard.metrics.taskSuccessRate': 'Task Success Rate',
        'metricsDashboard.metrics.taskSuccessRateDesc': 'Agent task completion rate',
        'metricsDashboard.metrics.queueDepth': 'Queue Depth',
        'metricsDashboard.metrics.queueDepthDesc': 'Tasks waiting in queue',
        'metricsDashboard.metrics.activeAgents': 'Active Agents',
        'metricsDashboard.metrics.activeAgentsDesc': 'Currently active agents',
        'metricsDashboard.tabs.agents': 'Agents',
        'metricsDashboard.tabs.systemHealth': 'System Health',
        'metricsDashboard.tabs.performance': 'Performance',
        'metricsDashboard.agent.idLabel': `ID: ${params?.id || ''}`,
        'metricsDashboard.agent.reputationScore': 'Reputation Score',
        'metricsDashboard.agent.successRate': 'Success Rate',
        'metricsDashboard.agent.activeTasks': 'Active Tasks',
        'metricsDashboard.systemHealth.errorRate': 'Error Rate',
        'metricsDashboard.systemHealth.avgLatency': 'Avg Latency',
        'metricsDashboard.systemHealth.latencyValue': `${params?.value || ''}ms`,
        'metricsDashboard.systemHealth.latencyTarget': 'Target: < 1000ms',
        'metricsDashboard.systemHealth.circuitBreakers': 'Circuit Breakers',
        'metricsDashboard.systemHealth.openCircuitBreakers': 'Open circuit breakers',
        'metricsDashboard.performance.title': 'Performance Metrics',
        'metricsDashboard.performance.subtitle': 'Detailed performance metrics and trends',
        'metricsDashboard.performance.description': 'Performance charts and detailed metrics will be displayed here. Integration with monitoring backend in progress.',
      };
      return translations[key] || key;
    },
  }),
}));

vi.mock('../../lib/api-client', () => ({
  apiClientWithMeta: vi.fn(),
}));

import { apiClientWithMeta } from '../../lib/api-client';

const mockApiClientWithMeta = apiClientWithMeta as ReturnType<typeof vi.fn>;

describe('MetricsDashboard Component (P1)', () => {
  beforeEach(() => {
    mockApiClientWithMeta.mockClear();
    vi.stubEnv('MODE', 'development');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('Loading State', () => {
    it('should display loading spinner initially', () => {
      mockApiClientWithMeta.mockImplementation(() => new Promise(() => {}));

      render(<MetricsDashboard />);

      expect(screen.getByText('Loading metrics...')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should fall back to mock data when API call fails in development', async () => {
      mockApiClientWithMeta.mockRejectedValueOnce(new Error('Network error'));

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Development Mode - Mock Data/i)).toBeInTheDocument();
      });
    });

    it('should throw error in production when API endpoint not found', async () => {
      vi.stubEnv('MODE', 'production');
      mockApiClientWithMeta.mockResolvedValueOnce({ 
        status: 404,
        data: null,
        headers: new Headers()
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/CRITICAL.*not implemented/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('should call apiClientWithMeta with correct endpoint', async () => {
      const mockData = {
        system_health: {
          overall_status: 'healthy',
          error_rate: 0.01,
          avg_latency: 0.1,
          open_circuit_breakers: 0,
        },
        metrics: {
          api_request_rate: { current: 1000, unit: 'req/min', trend: 'up' },
          agent_task_success_rate: { current: 0.95, unit: '%', trend: 'stable' },
          queue_depth: { current: 10, unit: 'tasks', trend: 'down' },
          active_agents: { current: 5, unit: 'agents', trend: 'stable' },
        },
        agents: [],
        alerts: [],
      };

      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledWith(
          '/phase7/monitoring/dashboard',
          expect.objectContaining({
            method: 'GET',
          })
        );
      });
    });

    it('should use apiClientWithMeta which includes credentials automatically', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: {
          system_health: { overall_status: 'healthy', error_rate: 0, avg_latency: 0, open_circuit_breakers: 0 },
          metrics: {
            api_request_rate: { current: 1000, unit: 'req/min' },
            agent_task_success_rate: { current: 0.95, unit: '%' },
            queue_depth: { current: 10, unit: 'tasks' },
            active_agents: { current: 5, unit: 'agents' },
          },
          agents: [],
          alerts: [],
        },
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledWith(
          '/phase7/monitoring/dashboard',
          { method: 'GET' }
        );
      });
    });
  });

  describe('Mock Data Fallback', () => {
    it('should display mock data warning in development', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 404,
        data: null,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Development Mode - Mock Data/i)).toBeInTheDocument();
        expect(screen.getByText(/Do not use this data for production decisions/i)).toBeInTheDocument();
      });
    });

    it('should use mock data when API is unavailable in development', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 404,
        data: null,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Metrics Dashboard')).toBeInTheDocument();
        expect(screen.getByText(/Development Mode - Mock Data/i)).toBeInTheDocument();
      });
    });
  });

  describe('Dashboard Display', () => {
    const mockData = {
      system_health: {
        overall_status: 'healthy',
        error_rate: 0.02,
        avg_latency: 0.15,
        open_circuit_breakers: 0,
      },
      metrics: {
        api_request_rate: { current: 1250, unit: 'req/min', trend: 'up' },
        agent_task_success_rate: { current: 0.96, unit: '%', trend: 'stable' },
        queue_depth: { current: 12, unit: 'tasks', trend: 'down' },
        active_agents: { current: 5, unit: 'agents', trend: 'stable' },
      },
      agents: [
        {
          agent_id: 'agent-123',
          agent_type: 'dev_agent',
          status: 'active',
          reputation_score: 750,
          task_success_rate: 0.95,
          active_tasks: 3,
        },
      ],
      alerts: [
        {
          id: '1',
          severity: 'warning',
          message: 'Test alert message',
          timestamp: new Date().toISOString(),
        },
      ],
    };

    it('should display dashboard title', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Metrics Dashboard')).toBeInTheDocument();
      });
    });

    it('should display system health status', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });
    });

    it('should display key metrics', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('API Request Rate')).toBeInTheDocument();
        expect(screen.getByText('Task Success Rate')).toBeInTheDocument();
        expect(screen.getByText('Queue Depth')).toBeInTheDocument();
        expect(screen.getByText('Active Agents')).toBeInTheDocument();
      });
    });

    it('should display metric values correctly', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/1250\.00 req\/min/)).toBeInTheDocument();
        expect(screen.getByText(/96\.00 %/)).toBeInTheDocument();
      });
    });

    it('should display alerts when present', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Test alert message')).toBeInTheDocument();
        expect(screen.getByText('WARNING')).toBeInTheDocument();
      });
    });

    it('should display agent information', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('DEV AGENT')).toBeInTheDocument();
        expect(screen.getByText('active')).toBeInTheDocument();
      });
    });
  });

  describe('Auto-refresh', () => {
    it('should set up auto-refresh interval', async () => {
      const mockData = {
        system_health: { overall_status: 'healthy', error_rate: 0, avg_latency: 0, open_circuit_breakers: 0 },
        metrics: {
          api_request_rate: { current: 1000, unit: 'req/min' },
          agent_task_success_rate: { current: 0.95, unit: '%' },
          queue_depth: { current: 10, unit: 'tasks' },
          active_agents: { current: 5, unit: 'agents' },
        },
        agents: [],
        alerts: [],
      };

      mockApiClientWithMeta.mockResolvedValue({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Auto-refresh: ON')).toBeInTheDocument();
      });
    });
  });
});
