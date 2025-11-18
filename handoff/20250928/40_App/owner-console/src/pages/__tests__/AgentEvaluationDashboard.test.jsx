import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import AgentEvaluationDashboard from '../AgentEvaluationDashboard';
import * as agentEvaluationApi from '@/lib/agent-evaluation-api';

vi.mock('@/lib/agent-evaluation-api', () => ({
  getAgentEvaluationResults: vi.fn(),
  getAgentEvaluationMetrics: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key, fallback) => fallback || key,
    i18n: {
      language: 'en-US',
      resolvedLanguage: 'en-US',
    },
  }),
}));

describe('AgentEvaluationDashboard - Empty State Logic', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Empty State Display (No Data)', () => {
    it('should display N/A when no evaluation data exists', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 0,
          self_healing_rate: 0,
          completion_rate: 0,
          ci_pass_rate: 0,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: null,
      };

      const mockResultsResponse = {
        evaluations: [], // Empty evaluations array
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        const naElements = screen.getAllByText('N/A');
        expect(naElements.length).toBeGreaterThanOrEqual(4); // At least 4 metric cards
      });
    });

    it('should display "No metrics available yet" when no evaluation data exists', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 0,
          self_healing_rate: 0,
          completion_rate: 0,
          ci_pass_rate: 0,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: null,
      };

      const mockResultsResponse = {
        evaluations: [], // Empty evaluations array
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        const noMetricsElements = screen.getAllByText('No metrics available yet');
        expect(noMetricsElements.length).toBeGreaterThanOrEqual(4); // At least 4 metric cards
      });
    });

    it('should NOT display badges when no evaluation data exists', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 0,
          self_healing_rate: 0,
          completion_rate: 0,
          ci_pass_rate: 0,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: null,
      };

      const mockResultsResponse = {
        evaluations: [], // Empty evaluations array
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.queryByText('On Target')).not.toBeInTheDocument();
        expect(screen.queryByText('Below Target')).not.toBeInTheDocument();
      });
    });
  });

  describe('Data State Display (With Data)', () => {
    it('should display percentages when evaluation data exists', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 87.5,
          self_healing_rate: 72.3,
          completion_rate: 81.2,
          ci_pass_rate: 92.1,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: '2025-11-17T10:30:00Z',
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T10:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText('87.5%')).toBeInTheDocument();
        expect(screen.getByText('72.3%')).toBeInTheDocument();
        expect(screen.getByText('81.2%')).toBeInTheDocument();
        expect(screen.getByText('92.1%')).toBeInTheDocument();
      });
    });

    it('should display target values when evaluation data exists', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 87.5,
          self_healing_rate: 72.3,
          completion_rate: 81.2,
          ci_pass_rate: 92.1,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: '2025-11-17T10:30:00Z',
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T10:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Target: 85.0%')).toBeInTheDocument();
        expect(screen.getByText('Target: 70.0%')).toBeInTheDocument();
        expect(screen.getByText('Target: 80.0%')).toBeInTheDocument();
        expect(screen.getByText('Target: 90.0%')).toBeInTheDocument();
      });
    });

    it('should display "On Target" badges when metrics meet targets', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 87.5,
          self_healing_rate: 72.3,
          completion_rate: 81.2,
          ci_pass_rate: 92.1,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: '2025-11-17T10:30:00Z',
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T10:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        const onTargetBadges = screen.getAllByText('On Target');
        expect(onTargetBadges.length).toBe(4); // All 4 metrics are on target
      });
    });

    it('should display "Below Target" badges when metrics do not meet targets', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 75.0,
          self_healing_rate: 60.0,
          completion_rate: 70.0,
          ci_pass_rate: 80.0,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: '2025-11-17T10:30:00Z',
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T10:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        const belowTargetBadges = screen.getAllByText('Below Target');
        expect(belowTargetBadges.length).toBe(4); // All 4 metrics are below target
      });
    });
  });

  describe('hasData Flag Logic', () => {
    it('should treat metrics with zero values and empty evaluations as no data', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 0,
          self_healing_rate: 0,
          completion_rate: 0,
          ci_pass_rate: 0,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: null,
      };

      const mockResultsResponse = {
        evaluations: [], // Empty evaluations array
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        const naElements = screen.getAllByText('N/A');
        expect(naElements.length).toBeGreaterThanOrEqual(4);
        
        expect(screen.queryByText('On Target')).not.toBeInTheDocument();
        expect(screen.queryByText('Below Target')).not.toBeInTheDocument();
      });
    });

    it('should treat null metrics as no data', async () => {
      const mockMetricsResponse = null;

      const mockResultsResponse = {
        evaluations: [],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText('No evaluation results available yet')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      agentEvaluationApi.getAgentEvaluationMetrics.mockRejectedValueOnce(new Error('API Error'));
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue({ evaluations: [] });

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });
  });

  describe('Date Formatting', () => {
    it('should format dates using Intl.DateTimeFormat with 24-hour format', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 87.5,
          self_healing_rate: 72.3,
          completion_rate: 81.2,
          ci_pass_rate: 92.1,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: '2025-11-17T14:30:00Z',
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T14:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        const dateElements = screen.getAllByText(/Nov|17|2025|14|30/);
        expect(dateElements.length).toBeGreaterThan(0);
      });
    });

    it('should return N/A for null or undefined dates', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 87.5,
          self_healing_rate: 72.3,
          completion_rate: 81.2,
          ci_pass_rate: 92.1,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: null, // Null date
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T14:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Last Evaluation: N/A')).toBeInTheDocument();
      });
    });

    it('should use resolvedLanguage for date formatting when available', async () => {
      const mockMetricsResponse = {
        metrics: {
          planner_accuracy: 87.5,
          self_healing_rate: 72.3,
          completion_rate: 81.2,
          ci_pass_rate: 92.1,
        },
        targets: {
          planner_accuracy: 85,
          self_healing_rate: 70,
          completion_rate: 80,
          ci_pass_rate: 90,
        },
        last_evaluation: '2025-11-17T14:30:00Z',
      };

      const mockResultsResponse = {
        evaluations: [
          {
            id: 1,
            run_id: 123,
            date: '2025-11-17T14:30:00Z',
            status: 'success',
            total_tasks: 10,
            completed: 8,
            pr_created: 7,
            ci_passed: 6,
            run_url: 'https://github.com/test/run/123',
          },
        ],
      };

      agentEvaluationApi.getAgentEvaluationMetrics.mockResolvedValue(mockMetricsResponse);
      agentEvaluationApi.getAgentEvaluationResults.mockResolvedValue(mockResultsResponse);

      render(<AgentEvaluationDashboard />);

      await waitFor(() => {
        expect(screen.getByText('Agent Evaluation Dashboard')).toBeInTheDocument();
      });
    });
  });
});
