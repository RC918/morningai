import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import Sessions from '../Sessions';
import * as apiClient from '@/lib/api-client';

vi.mock('@/lib/api-client', () => ({
  apiClientWithMeta: vi.fn(),
  handleApiError: vi.fn((err, options) => options.defaultMessage || 'Error'),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key, fallback) => fallback || key,
  }),
}));

const mockSessionsWithActive = {
  data: {
    sessions: [
      {
        id: 'session_001',
        title: 'Running session',
        goal: 'Test goal',
        status: 'running',
        confidence: 0.85,
        startedAt: '2024-01-15T10:30:00Z',
        updatedAt: '2024-01-15T11:45:00Z',
        progress: 50,
        currentTask: 'Testing',
        plan: { totalTasks: 4, completedTasks: 2, tasks: [] },
        logs: [],
      },
    ],
    counts: { all: 1, running: 1, paused: 0, completed: 0, failed: 0 },
  },
};

const mockSessionsNoActive = {
  data: {
    sessions: [
      {
        id: 'session_002',
        title: 'Completed session',
        goal: 'Test goal',
        status: 'completed',
        confidence: 1.0,
        startedAt: '2024-01-15T09:00:00Z',
        updatedAt: '2024-01-15T10:00:00Z',
        progress: 100,
        currentTask: 'Done',
        plan: { totalTasks: 4, completedTasks: 4, tasks: [] },
        logs: [],
      },
    ],
    counts: { all: 1, running: 0, paused: 0, completed: 1, failed: 0 },
  },
};

const mockEmptySessions = {
  data: {
    sessions: [],
    counts: { all: 0, running: 0, paused: 0, completed: 0, failed: 0 },
  },
};

describe('Sessions Page - Polling Toggle Behavior (#2000)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers({ shouldAdvanceTime: true });
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  describe('Auto-refresh Toggle State', () => {
    it('should have auto-refresh enabled by default with active sessions', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        const autoButton = screen.getByTitle('Auto-refresh enabled (10s)');
        expect(autoButton).toBeInTheDocument();
      });
    });

    it('should toggle auto-refresh off when clicked', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh enabled (10s)')).toBeInTheDocument();
      });

      const autoButton = screen.getByText('Auto');
      fireEvent.click(autoButton);

      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh disabled')).toBeInTheDocument();
      });
    });

    it('should toggle auto-refresh back on when clicked again', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh enabled (10s)')).toBeInTheDocument();
      });

      const autoButton = screen.getByText('Auto');
      
      fireEvent.click(autoButton);
      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh disabled')).toBeInTheDocument();
      });

      fireEvent.click(autoButton);
      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh enabled (10s)')).toBeInTheDocument();
      });
    });
  });

  describe('Polling Behavior with Active Sessions', () => {
    it('should start polling when auto-refresh is on and active sessions exist', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const initialCallCount = apiClient.apiClientWithMeta.mock.calls.length;

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(apiClient.apiClientWithMeta.mock.calls.length).toBeGreaterThan(initialCallCount);
    });

    it('should stop polling when auto-refresh is toggled off', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const autoButton = screen.getByText('Auto');
      fireEvent.click(autoButton);

      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh disabled')).toBeInTheDocument();
      });

      const callCountAfterToggle = apiClient.apiClientWithMeta.mock.calls.length;

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(callCountAfterToggle);
    });

    it('should resume polling when auto-refresh is toggled back on', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const autoButton = screen.getByText('Auto');
      
      fireEvent.click(autoButton);
      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh disabled')).toBeInTheDocument();
      });

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });
      
      const callCountBeforeResume = apiClient.apiClientWithMeta.mock.calls.length;

      fireEvent.click(autoButton);
      await waitFor(() => {
        expect(screen.getByTitle('Auto-refresh enabled (10s)')).toBeInTheDocument();
      });

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(apiClient.apiClientWithMeta.mock.calls.length).toBeGreaterThan(callCountBeforeResume);
    });
  });

  describe('Polling Behavior without Active Sessions', () => {
    it('should not poll when no active sessions exist', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsNoActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const initialCallCount = apiClient.apiClientWithMeta.mock.calls.length;

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(initialCallCount);
    });

    it('should not poll when sessions list is empty', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockEmptySessions);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const initialCallCount = apiClient.apiClientWithMeta.mock.calls.length;

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(initialCallCount);
    });
  });

  describe('Polling Interval', () => {
    it('should poll every 10 seconds (POLLING_INTERVAL_MS)', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const initialCallCount = apiClient.apiClientWithMeta.mock.calls.length;

      await act(async () => {
        vi.advanceTimersByTime(5000);
      });
      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(initialCallCount);

      await act(async () => {
        vi.advanceTimersByTime(5000);
      });
      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(initialCallCount + 1);

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });
      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(initialCallCount + 2);
    });
  });

  describe('AbortController Integration (#1996)', () => {
    it('should pass signal to API calls during polling', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      await act(async () => {
        vi.advanceTimersByTime(10000);
      });

      const pollingCalls = apiClient.apiClientWithMeta.mock.calls.filter(
        call => call[1]?.signal !== undefined
      );
      expect(pollingCalls.length).toBeGreaterThan(0);
    });
  });

  describe('Cleanup on Unmount', () => {
    it('should clear interval when component unmounts', async () => {
      apiClient.apiClientWithMeta.mockResolvedValue(mockSessionsWithActive);

      const { unmount } = render(<Sessions />);

      await waitFor(() => {
        expect(screen.getByText('Auto')).toBeInTheDocument();
      });

      const callCountBeforeUnmount = apiClient.apiClientWithMeta.mock.calls.length;

      unmount();

      await act(async () => {
        vi.advanceTimersByTime(20000);
      });

      expect(apiClient.apiClientWithMeta).toHaveBeenCalledTimes(callCountBeforeUnmount);
    });
  });
});
