import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
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
        'metricsDashboard.devInfo.title': 'Development Info',
        'metricsDashboard.devInfo.description': 'The Metrics Dashboard requires the backend API endpoint:',
        'metricsDashboard.devInfo.endpoint': 'GET /phase7/monitoring/dashboard',
        'metricsDashboard.devInfo.hint': 'Ensure your backend server is running and the endpoint is implemented.',
        'common.retry': 'Retry',
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
        'metricsDashboard.agents.noData': 'No agent data available. Agent metrics will be displayed here once the monitoring system collects data.',
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

vi.mock('../../lib/api-client', async () => {
  const actual = await vi.importActual<typeof import('../../lib/api-client')>('../../lib/api-client');
  return {
    ...actual,
    apiClientWithMeta: vi.fn(),
  };
});

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
    it('should display error state when API call fails', async () => {
      mockApiClientWithMeta.mockRejectedValueOnce(new Error('Network error'));

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });

    it('should display error state when API endpoint not found', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({ 
        status: 404,
        data: null,
        headers: new Headers()
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByText(/API endpoint not found/i)).toBeInTheDocument();
      });
    });

    it('should display development info in error state when in development mode', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({ 
        status: 404,
        data: null,
        headers: new Headers()
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Development Info')).toBeInTheDocument();
        expect(screen.getByText(/GET \/phase7\/monitoring\/dashboard/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('should call apiClientWithMeta with correct endpoint', async () => {
      const mockData = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: {
          overall_status: 'healthy',
          error_rate: 0.01,
          avg_latency: 0.1,
          open_circuit_breakers: 0,
        },
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: { active_sagas: 5 },
        storage: {},
        trends: {},
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
          timestamp: '2025-11-05T00:00:00Z',
          system_health: { overall_status: 'healthy', error_rate: 0, avg_latency: 0, open_circuit_breakers: 0 },
          circuit_breakers: {},
          bulkheads: {},
          saga_orchestrator: { active_sagas: 5 },
          storage: {},
          trends: {},
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

  describe('Error State Display', () => {
    it('should display error message when API fails', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 404,
        data: null,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument();
        expect(screen.getByText(/API endpoint not found/i)).toBeInTheDocument();
      });
    });

    it('should display retry button in error state', async () => {
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 404,
        data: null,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
      });
    });
  });

  describe('Dashboard Display', () => {
    const mockData = {
      timestamp: '2025-11-05T00:00:00Z',
      system_health: {
        overall_status: 'healthy',
        error_rate: 0.02,
        avg_latency: 0.15,
        open_circuit_breakers: 0,
      },
      circuit_breakers: {},
      bulkheads: {},
      saga_orchestrator: {
        active_sagas: 5,
        completed_sagas: 100,
      },
      storage: {},
      trends: {},
      alerts: [
        {
          level: 'warning',
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
        expect(screen.getByText(/98\.00 %/)).toBeInTheDocument();
        expect(screen.getByText(/5\.00 agents/)).toBeInTheDocument();
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

    it('should display empty agent state when no agents', async () => {
      const user = userEvent.setup();
      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: mockData,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });

      const agentsTab = screen.getByRole('tab', { name: /agents/i });
      await user.click(agentsTab);

      const emptyStateText = await screen.findByText(/No agent data available/i, {}, { timeout: 3000 });
      expect(emptyStateText).toBeInTheDocument();
    });
  });

  describe('Auto-refresh', () => {
    it('should set up auto-refresh interval', async () => {
      const mockData = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: { overall_status: 'healthy', error_rate: 0, avg_latency: 0, open_circuit_breakers: 0 },
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: { active_sagas: 5 },
        storage: {},
        trends: {},
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

  describe('Backend Response Normalization (P0 Fix)', () => {
    it('should handle backend response with object system_health', async () => {
      const backendResponse = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: {
          overall_status: 'healthy',
          error_rate: 0.02,
          avg_latency: 150,
          open_circuit_breakers: 0,
          rejected_requests: 5,
          active_sagas: 3,
        },
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: {
          active_sagas: 3,
          completed_sagas: 100,
        },
        storage: {},
        trends: {},
        alerts: [
          {
            level: 'warning',
            message: 'High error rate detected',
            timestamp: '2025-11-05T00:00:00Z',
          },
        ],
      };

      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: backendResponse,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
        expect(screen.getByText(/98\.00 %/)).toBeInTheDocument();
        expect(screen.getByText('High error rate detected')).toBeInTheDocument();
      });
    });

    it('should handle backend response with string system_health (no metrics history)', async () => {
      const backendResponse = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: 'healthy',
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: {
          active_sagas: 0,
          completed_sagas: 0,
        },
        storage: { total_tables: 5 },
        trends: {},
        alerts: [],
      };

      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: backendResponse,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
        expect(screen.getByText(/100\.00 %/)).toBeInTheDocument();
      });
    });

    it('should map backend alert level to frontend severity', async () => {
      const backendResponse = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: 'healthy',
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: { active_sagas: 0 },
        storage: {},
        trends: {},
        alerts: [
          {
            level: 'critical',
            message: 'Critical system error',
            timestamp: '2025-11-05T00:00:00Z',
          },
          {
            level: 'warning',
            message: 'Warning message',
            timestamp: '2025-11-05T00:01:00Z',
          },
        ],
      };

      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: backendResponse,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('CRITICAL')).toBeInTheDocument();
        expect(screen.getByText('WARNING')).toBeInTheDocument();
        expect(screen.getByText('Critical system error')).toBeInTheDocument();
        expect(screen.getByText('Warning message')).toBeInTheDocument();
      });
    });

    it('should synthesize metrics from backend data', async () => {
      const backendResponse = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: {
          overall_status: 'degraded',
          error_rate: 0.15,
          avg_latency: 500,
          open_circuit_breakers: 2,
        },
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: {
          active_sagas: 7,
          completed_sagas: 50,
        },
        storage: {},
        trends: {},
        alerts: [],
      };

      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: backendResponse,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('DEGRADED')).toBeInTheDocument();
        expect(screen.getByText(/85\.00 %/)).toBeInTheDocument();
        expect(screen.getByText(/7\.00 agents/)).toBeInTheDocument();
      });
    });

    it('should handle empty agents array and show empty state', async () => {
      const user = userEvent.setup();
      const backendResponse = {
        timestamp: '2025-11-05T00:00:00Z',
        system_health: 'healthy',
        circuit_breakers: {},
        bulkheads: {},
        saga_orchestrator: { active_sagas: 0 },
        storage: {},
        trends: {},
        alerts: [],
      };

      mockApiClientWithMeta.mockResolvedValueOnce({
        status: 200,
        data: backendResponse,
        headers: new Headers(),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });

      const agentsTab = screen.getByRole('tab', { name: /agents/i });
      await user.click(agentsTab);

      const emptyStateText = await screen.findByText(/No agent data available/i, {}, { timeout: 3000 });
      expect(emptyStateText).toBeInTheDocument();
    });
  });
});
