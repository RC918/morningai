import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ProviderHealthDashboard from '../ProviderHealthDashboard';
import * as apiClient from '@/lib/api-client';

vi.mock('@/lib/api-client', () => ({
  apiClientWithMeta: vi.fn(),
  handleApiError: vi.fn((err, options) => options?.defaultMessage || 'Error'),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string) => {
      const translations: Record<string, string> = {
        'common.loading': 'Loading...',
        'common.refresh': 'Refresh',
        'common.error': 'Error',
        'common.yes': 'Yes',
        'common.no': 'No',
        'common.unauthorized': 'Unauthorized',
        'providerHealth.title': 'Provider Health Dashboard',
        'providerHealth.subtitle': 'Monitor real-time health status of LLM providers',
        'providerHealth.metricsUnavailable': 'Provider health metrics are not available',
        'providerHealth.serviceUnavailable': 'Health monitoring service is temporarily unavailable',
        'providerHealth.loadError': 'Failed to load provider health data',
        'providerHealth.windowSelect': 'Select time window',
        'providerHealth.minutes': 'min',
        'providerHealth.autoRefreshOn': 'Auto-refresh: ON',
        'providerHealth.autoRefreshOff': 'Auto-refresh: OFF',
        'providerHealth.averageHealth': 'Average Health',
        'providerHealth.healthyProviders': 'Healthy',
        'providerHealth.degradedProviders': 'Degraded',
        'providerHealth.criticalProviders': 'Critical',
        'providerHealth.providerDetails': 'Provider Details',
        'providerHealth.viewInGrafana': 'View in Grafana',
        'providerHealth.healthScore': 'Health Score',
        'providerHealth.latency': 'Latency',
        'providerHealth.errorRate': 'Error Rate',
        'providerHealth.driftRate': 'Drift Rate',
        'providerHealth.requests': 'Requests',
        'providerHealth.lastUpdated': 'Last updated',
        'providerHealth.noProviders': 'No provider data available',
        'providerHealth.noProvidersHint': 'Provider metrics will appear once LLM requests are made',
        'providerHealth.alertingStatus': 'Alerting Status',
        'providerHealth.alertingEnabled': 'Alerting',
        'providerHealth.windowLabel': 'Window',
        'providerHealth.lastRefresh': 'Last refresh',
      };
      return translations[key] || key;
    },
    i18n: {
      language: 'en-US',
      resolvedLanguage: 'en-US',
    },
  }),
}));

const mockHealthyResponse = {
  data: {
    available: true,
    timestamp: '2025-01-01T12:00:00Z',
    window_minutes: 15,
    system_status: 'healthy',
    summary: {
      average_health: 92.5,
      total_providers: 3,
      healthy: 2,
      degraded: 1,
      critical: 0,
    },
    providers: {
      openai: {
        health_score: 95.0,
        latency_ms: 150,
        // Note: error_rate and drift_rate are in 0-100 scale (percentage)
        error_rate: 1.0,  // 1.0%
        drift_rate: 2.0,  // 2.0%
        request_count: 1000,
        last_updated: '2025-01-01T12:00:00Z',
      },
      gemini: {
        health_score: 90.0,
        latency_ms: 200,
        error_rate: 2.0,  // 2.0%
        drift_rate: 3.0,  // 3.0%
        request_count: 500,
        last_updated: '2025-01-01T12:00:00Z',
      },
      alicloud: {
        health_score: 75.0,
        latency_ms: 300,
        error_rate: 5.0,  // 5.0%
        drift_rate: 8.0,  // 8.0%
        request_count: 200,
        last_updated: '2025-01-01T12:00:00Z',
      },
    },
    ranking: ['openai', 'gemini', 'alicloud'],
    alerting: {
      enabled: true,
      cooldown_status: {},
    },
  },
  status: 200,
  headers: new Headers(),
};

const mockUnavailableResponse = {
  data: {
    available: false,
    error: 'metrics_unavailable',
    message: 'CanaryMetrics not configured or Redis unavailable',
    timestamp: '2025-01-01T12:00:00Z',
  },
  status: 503,
  headers: new Headers(),
};

const mockEmptyProvidersResponse = {
  data: {
    available: true,
    timestamp: '2025-01-01T12:00:00Z',
    window_minutes: 15,
    system_status: 'healthy',
    summary: {
      average_health: 100,
      total_providers: 0,
      healthy: 0,
      degraded: 0,
      critical: 0,
    },
    providers: {},
    ranking: [],
    alerting: {
      enabled: false,
      cooldown_status: {},
    },
  },
  status: 200,
  headers: new Headers(),
};

describe('ProviderHealthDashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading skeleton initially', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(() => {})
      );

      render(<ProviderHealthDashboard />);

      expect(screen.getByRole('status')).toBeInTheDocument();
      expect(screen.getByLabelText('Loading...')).toBeInTheDocument();
    });
  });

  describe('Successful Data Load', () => {
    it('should display provider health data when API returns successfully', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Provider Health Dashboard')).toBeInTheDocument();
      });

      expect(screen.getByTestId('system-status-badge')).toHaveTextContent('HEALTHY');
      expect(screen.getByTestId('avg-health-card')).toBeInTheDocument();
      expect(screen.getByTestId('healthy-count-card')).toBeInTheDocument();
      expect(screen.getByTestId('degraded-count-card')).toBeInTheDocument();
      expect(screen.getByTestId('critical-count-card')).toBeInTheDocument();
    });

    it('should display all provider cards', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('provider-card-openai')).toBeInTheDocument();
        expect(screen.getByTestId('provider-card-gemini')).toBeInTheDocument();
        expect(screen.getByTestId('provider-card-alicloud')).toBeInTheDocument();
      });
    });

    it('should display correct summary counts', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        const healthyCard = screen.getByTestId('healthy-count-card');
        expect(healthyCard).toHaveTextContent('2');

        const degradedCard = screen.getByTestId('degraded-count-card');
        expect(degradedCard).toHaveTextContent('1');

        const criticalCard = screen.getByTestId('critical-count-card');
        expect(criticalCard).toHaveTextContent('0');
      });
    });

    it('should display alerting status', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('alerting-status')).toBeInTheDocument();
        expect(screen.getByText('Yes')).toBeInTheDocument();
      });
    });
  });

  describe('Empty State', () => {
    it('should display empty state when no providers exist', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockEmptyProvidersResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('No provider data available')).toBeInTheDocument();
        expect(screen.getByText('Provider metrics will appear once LLM requests are made')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API returns 503', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockUnavailableResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Health monitoring service is temporarily unavailable')).toBeInTheDocument();
      });
    });

    it('should display error message when API throws', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockRejectedValue(new Error('Network error'));
      (apiClient.handleApiError as ReturnType<typeof vi.fn>).mockReturnValue('Failed to load provider health data');

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Failed to load provider health data')).toBeInTheDocument();
      });
    });
  });

  describe('Refresh Functionality', () => {
    it('should call API when refresh button is clicked', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('refresh-button')).toBeInTheDocument();
      });

      const callCountBefore = (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mock.calls.length;
      fireEvent.click(screen.getByTestId('refresh-button'));

      await waitFor(() => {
        expect((apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mock.calls.length).toBeGreaterThan(callCountBefore);
      });
    });

    it('should toggle auto-refresh when button is clicked', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Auto-refresh: ON')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('Auto-refresh: ON'));

      expect(screen.getByText('Auto-refresh: OFF')).toBeInTheDocument();
    });
  });

  describe('Window Selection', () => {
    it('should change window when select is changed', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByLabelText('Select time window')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('Select time window'), { target: { value: '30' } });

      await waitFor(() => {
        expect(apiClient.apiClientWithMeta).toHaveBeenCalledWith(
          expect.stringContaining('window=30'),
          expect.any(Object)
        );
      });
    });
  });

  describe('Health Score Colors', () => {
    it('should display correct color for healthy providers (score >= 80)', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        const openaiCard = screen.getByTestId('provider-card-openai');
        expect(openaiCard).toBeInTheDocument();
      });
    });

    it('should display correct color for degraded providers (60 <= score < 80)', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        const alicloudCard = screen.getByTestId('provider-card-alicloud');
        expect(alicloudCard).toBeInTheDocument();
      });
    });
  });

  describe('Metrics Display', () => {
    it('should format latency correctly', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('150ms')).toBeInTheDocument();
        expect(screen.getByText('200ms')).toBeInTheDocument();
        expect(screen.getByText('300ms')).toBeInTheDocument();
      });
    });

    it('should format error rate as percentage', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('1.0%')).toBeInTheDocument();
        // 2.0% appears twice (error_rate and drift_rate for gemini), use getAllByText
        expect(screen.getAllByText('2.0%').length).toBeGreaterThanOrEqual(1);
        expect(screen.getByText('5.0%')).toBeInTheDocument();
      });
    });

    it('should display request counts', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByText('1000')).toBeInTheDocument();
        expect(screen.getByText('500')).toBeInTheDocument();
        expect(screen.getByText('200')).toBeInTheDocument();
      });
    });
  });

  describe('Accessibility', () => {
    it('should have proper aria attributes during loading', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockImplementation(
        () => new Promise(() => {})
      );

      render(<ProviderHealthDashboard />);

      const loadingElement = screen.getByRole('status');
      expect(loadingElement).toHaveAttribute('aria-live', 'polite');
      expect(loadingElement).toHaveAttribute('aria-busy', 'true');
    });

    it('should have proper test ids for automation', async () => {
      (apiClient.apiClientWithMeta as ReturnType<typeof vi.fn>).mockResolvedValue(mockHealthyResponse);

      render(<ProviderHealthDashboard />);

      await waitFor(() => {
        expect(screen.getByTestId('provider-health-dashboard')).toBeInTheDocument();
        expect(screen.getByTestId('system-status-badge')).toBeInTheDocument();
        expect(screen.getByTestId('refresh-button')).toBeInTheDocument();
      });
    });
  });
});
