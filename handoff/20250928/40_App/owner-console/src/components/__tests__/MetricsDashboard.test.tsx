import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { MetricsDashboard } from '../MetricsDashboard';

const mockFetch = vi.fn();
global.fetch = mockFetch;

describe('MetricsDashboard Component (P1)', () => {
  beforeEach(() => {
    mockFetch.mockClear();
    vi.stubEnv('NODE_ENV', 'development');
    vi.stubEnv('VITE_API_BASE_URL', 'http://localhost:5000');
  });

  afterEach(() => {
    vi.unstubAllEnvs();
  });

  describe('Loading State', () => {
    it('should display loading spinner initially', () => {
      mockFetch.mockImplementation(() => new Promise(() => {}));

      render(<MetricsDashboard />);

      expect(screen.getByText('Loading metrics...')).toBeInTheDocument();
    });
  });

  describe('Error Handling', () => {
    it('should fall back to mock data when fetch fails in development', async () => {
      mockFetch.mockRejectedValueOnce(new Error('Network error'));

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Development Mode - Mock Data/i)).toBeInTheDocument();
      });
    });

    it('should display error for production without API URL', async () => {
      vi.stubEnv('NODE_ENV', 'production');
      vi.stubEnv('VITE_API_BASE_URL', '');

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/CRITICAL.*must be configured/i)).toBeInTheDocument();
      });
    });
  });

  describe('Data Fetching', () => {
    it('should fetch data from correct API endpoint', async () => {
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

      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(mockFetch).toHaveBeenCalledWith(
          'http://localhost:5000/api/phase7/monitoring/dashboard',
          expect.objectContaining({
            credentials: 'include',
          })
        );
      });
    });

    it('should include credentials in API request', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          system_health: { overall_status: 'healthy', error_rate: 0, avg_latency: 0, open_circuit_breakers: 0 },
          metrics: {
            api_request_rate: { current: 1000, unit: 'req/min' },
            agent_task_success_rate: { current: 0.95, unit: '%' },
            queue_depth: { current: 10, unit: 'tasks' },
            active_agents: { current: 5, unit: 'agents' },
          },
          agents: [],
          alerts: [],
        }),
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        const fetchCall = mockFetch.mock.calls[0];
        expect(fetchCall[1].credentials).toBe('include');
      });
    });
  });

  describe('Mock Data Fallback', () => {
    it('should display mock data warning in development', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/Development Mode - Mock Data/i)).toBeInTheDocument();
        expect(screen.getByText(/Do not use this data for production decisions/i)).toBeInTheDocument();
      });
    });

    it('should use mock data when API is unavailable in development', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: false,
        status: 404,
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
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Metrics Dashboard')).toBeInTheDocument();
      });
    });

    it('should display system health status', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('HEALTHY')).toBeInTheDocument();
      });
    });

    it('should display key metrics', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
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
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText(/1250\.00 req\/min/)).toBeInTheDocument();
        expect(screen.getByText(/96\.00 %/)).toBeInTheDocument();
      });
    });

    it('should display alerts when present', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Test alert message')).toBeInTheDocument();
        expect(screen.getByText('WARNING')).toBeInTheDocument();
      });
    });

    it('should display agent information', async () => {
      mockFetch.mockResolvedValueOnce({
        ok: true,
        json: async () => mockData,
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

      mockFetch.mockResolvedValue({
        ok: true,
        json: async () => mockData,
      });

      render(<MetricsDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Auto-refresh: ON')).toBeInTheDocument();
      });
    });
  });
});
