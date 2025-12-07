import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react'

// Mock @morningai/shared-ui
vi.mock('@morningai/shared-ui', () => ({
  Badge: ({ children, variant, className }) => (
    <span data-testid="badge" data-variant={variant} className={className}>{children}</span>
  ),
  Skeleton: ({ className }) => (
    <div data-testid="skeleton" className={className} />
  ),
  Progress: ({ value, className }) => (
    <div data-testid="progress" data-value={value} className={className} />
  ),
}))

// Mock AppleButton
vi.mock('@/components/apple/apple-button', () => ({
  AppleButton: ({ children, onClick, variant, size, haptic, ...props }) => (
    <button onClick={onClick} data-variant={variant} data-size={size} {...props}>{children}</button>
  ),
}))

import SessionInsights from '../SessionInsights'

// Mock react-i18next with proper interpolation support
// Handles: t('key', 'default'), t('key', { count: n }), t('key', 'default {{count}}', { count: n })
const mockT = (key, defaultValueOrOptions, options) => {
  // Case 1: t('key', 'default string')
  if (typeof defaultValueOrOptions === 'string' && !options) {
    return defaultValueOrOptions
  }
  
  // Case 2: t('key', { count: n }) - options as second arg
  if (typeof defaultValueOrOptions === 'object' && defaultValueOrOptions !== null) {
    if (typeof defaultValueOrOptions.count === 'number') {
      // For durationValue, return formatted string
      if (key === 'sessions.insights.durationValue') {
        return `${defaultValueOrOptions.count}m`
      }
      return String(defaultValueOrOptions.count)
    }
    return key
  }
  
  // Case 3: t('key', 'default {{count}}', { count: n }) - default with interpolation
  if (typeof defaultValueOrOptions === 'string' && options && typeof options === 'object') {
    let result = defaultValueOrOptions
    if (typeof options.count === 'number') {
      result = result.replace('{{count}}', String(options.count))
    }
    return result
  }
  
  // Fallback to key
  return defaultValueOrOptions || key
}

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: mockT,
  }),
}))

// Mock api-client
const mockApiClientWithMeta = vi.fn()
vi.mock('@/lib/api-client', () => ({
  apiClientWithMeta: (...args) => mockApiClientWithMeta(...args),
  handleApiError: (err, options) => options.defaultMessage || 'Error',
}))

describe('SessionInsights', () => {
  const mockInsights = {
    session_id: 'test-session-123',
    insight_type: 'session_analysis',
    summary: 'This session completed 5 tasks successfully with high confidence.',
    recommendations: [
      'Consider adding more unit tests',
      'Review error handling patterns',
      'Optimize database queries'
    ],
    metrics: {
      tasks_completed: 5,
      tasks_failed: 1,
      duration_seconds: 3600,
      confidence: 0.85
    },
    source: 'cached',
    timestamp: '2025-12-07T12:00:00Z'
  }

  const defaultProps = {
    sessionId: 'test-session-123',
    isOpen: true,
    className: ''
  }

  beforeEach(() => {
    vi.clearAllMocks()
    mockApiClientWithMeta.mockResolvedValue({ data: mockInsights })
  })

  describe('Loading State', () => {
    it('should show loading skeleton when fetching insights', async () => {
      mockApiClientWithMeta.mockImplementation(() => new Promise(() => {})) // Never resolves
      render(<SessionInsights {...defaultProps} />)
      
      // Should show skeleton elements
      const skeletons = document.querySelectorAll('.h-5, .h-4, .h-8')
      expect(skeletons.length).toBeGreaterThan(0)
    })

    it('should not render when isOpen is false', () => {
      render(<SessionInsights {...defaultProps} isOpen={false} />)
      expect(screen.queryByText('Session Insights')).not.toBeInTheDocument()
    })
  })

  describe('Error State', () => {
    it('should display error message when fetch fails', async () => {
      mockApiClientWithMeta.mockRejectedValue(new Error('Network error'))
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Unable to load insights')).toBeInTheDocument()
      })
    })

    it('should show refresh button in error state', async () => {
      mockApiClientWithMeta.mockRejectedValue(new Error('Network error'))
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Unable to load insights')).toBeInTheDocument()
      })
      
      // Should have a refresh button
      const refreshButton = document.querySelector('button')
      expect(refreshButton).toBeInTheDocument()
    })

    it('should retry fetch when refresh button is clicked', async () => {
      mockApiClientWithMeta.mockRejectedValueOnce(new Error('Network error'))
      mockApiClientWithMeta.mockResolvedValueOnce({ data: mockInsights })
      
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Unable to load insights')).toBeInTheDocument()
      })
      
      const refreshButton = document.querySelector('button')
      fireEvent.click(refreshButton)
      
      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledTimes(2)
      })
    })
  })

  describe('Empty State', () => {
    it('should display no insights message when data is null', async () => {
      mockApiClientWithMeta.mockResolvedValue({ data: null })
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('No insights available for this session')).toBeInTheDocument()
      })
    })
  })

  describe('Insights Display', () => {
    it('should display session insights title', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Session Insights')).toBeInTheDocument()
      })
    })

    it('should display summary when available', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
        expect(screen.getByText(mockInsights.summary)).toBeInTheDocument()
      })
    })

    it('should display recommendations when available', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Recommendations')).toBeInTheDocument()
        expect(screen.getByText('Consider adding more unit tests')).toBeInTheDocument()
        expect(screen.getByText('Review error handling patterns')).toBeInTheDocument()
        expect(screen.getByText('Optimize database queries')).toBeInTheDocument()
      })
    })

    it('should display recommendation numbers', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        // Get the recommendations section and verify list items exist
        const recommendationsHeading = screen.getByText('Recommendations')
        const recommendationsSection = recommendationsHeading.closest('div')
        expect(recommendationsSection).not.toBeNull()
        
        // Get all list items and verify they have numbered badges
        const listItems = within(recommendationsSection).getAllByRole('listitem')
        expect(listItems).toHaveLength(3)
        
        // Verify each recommendation has its number
        expect(within(listItems[0]).getByText('1')).toBeInTheDocument()
        expect(within(listItems[1]).getByText('2')).toBeInTheDocument()
        expect(within(listItems[2]).getByText('3')).toBeInTheDocument()
      })
    })
  })

  describe('Metrics Display', () => {
    it('should display tasks completed metric', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Completed')).toBeInTheDocument()
        expect(screen.getByText('5')).toBeInTheDocument()
      })
    })

    it('should display tasks failed metric', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        const failedLabel = screen.getByText('Failed')
        expect(failedLabel).toBeInTheDocument()
        
        // Get the metric tile container and verify the value within it
        const failedTile = failedLabel.closest('div.p-3')
        expect(failedTile).not.toBeNull()
        expect(within(failedTile).getByText('1')).toBeInTheDocument()
      })
    })

    it('should display duration metric in minutes', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Duration')).toBeInTheDocument()
        // 3600 seconds = 60 minutes
        expect(screen.getByText('60m')).toBeInTheDocument()
      })
    })

    it('should display confidence metric as percentage', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Confidence')).toBeInTheDocument()
        expect(screen.getByText('85%')).toBeInTheDocument()
      })
    })

    it('should not display metrics section when metrics is empty', async () => {
      mockApiClientWithMeta.mockResolvedValue({ 
        data: { ...mockInsights, metrics: {} } 
      })
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Session Insights')).toBeInTheDocument()
      })
      
      expect(screen.queryByText('Completed')).not.toBeInTheDocument()
    })
  })

  describe('Source Badge', () => {
    it('should display Cached badge when source is cached', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Cached')).toBeInTheDocument()
      })
    })

    it('should display Generated badge when source is generated', async () => {
      mockApiClientWithMeta.mockResolvedValue({ 
        data: { ...mockInsights, source: 'generated' } 
      })
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Generated')).toBeInTheDocument()
      })
    })
  })

  describe('Timestamp Display', () => {
    it('should display last updated timestamp', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText(/Last updated/)).toBeInTheDocument()
      })
    })
  })

  describe('Expand/Collapse Functionality', () => {
    it('should be expanded by default', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
      })
    })

    it('should collapse content when header is clicked', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
      })
      
      const header = screen.getByRole('button', { expanded: true })
      fireEvent.click(header)
      
      expect(screen.queryByText('Summary')).not.toBeInTheDocument()
    })

    it('should expand content when collapsed header is clicked', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
      })
      
      const header = screen.getByRole('button', { expanded: true })
      fireEvent.click(header) // Collapse
      fireEvent.click(header) // Expand
      
      expect(screen.getByText('Summary')).toBeInTheDocument()
    })

    it('should toggle on Enter key press', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
      })
      
      const header = screen.getByRole('button', { expanded: true })
      fireEvent.keyDown(header, { key: 'Enter' })
      
      expect(screen.queryByText('Summary')).not.toBeInTheDocument()
    })
  })

  describe('Refresh Functionality', () => {
    it('should have a refresh button in header', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Session Insights')).toBeInTheDocument()
      })
      
      const refreshButton = screen.getByLabelText('Refresh insights')
      expect(refreshButton).toBeInTheDocument()
    })

    it('should refetch insights when refresh button is clicked', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Session Insights')).toBeInTheDocument()
      })
      
      const refreshButton = screen.getByLabelText('Refresh insights')
      fireEvent.click(refreshButton)
      
      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledTimes(2)
      })
    })

    it('should not trigger collapse when refresh button is clicked', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
      })
      
      const refreshButton = screen.getByLabelText('Refresh insights')
      fireEvent.click(refreshButton)
      
      // Content should still be visible
      await waitFor(() => {
        expect(screen.getByText('Summary')).toBeInTheDocument()
      })
    })
  })

  describe('API Integration', () => {
    it('should call API with correct session ID', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledWith(
          '/api/deepwiki/insights/test-session-123',
          { method: 'GET' }
        )
      })
    })

    it('should not fetch when sessionId is not provided', () => {
      render(<SessionInsights {...defaultProps} sessionId={null} />)
      expect(mockApiClientWithMeta).not.toHaveBeenCalled()
    })

    it('should not fetch when isOpen is false', () => {
      render(<SessionInsights {...defaultProps} isOpen={false} />)
      expect(mockApiClientWithMeta).not.toHaveBeenCalled()
    })

    it('should refetch when sessionId changes', async () => {
      const { rerender } = render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledTimes(1)
      })
      
      rerender(<SessionInsights {...defaultProps} sessionId="new-session-456" />)
      
      await waitFor(() => {
        expect(mockApiClientWithMeta).toHaveBeenCalledTimes(2)
        expect(mockApiClientWithMeta).toHaveBeenLastCalledWith(
          '/api/deepwiki/insights/new-session-456',
          { method: 'GET' }
        )
      })
    })
  })

  describe('Accessibility', () => {
    it('should have proper aria-expanded attribute on header', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        const header = screen.getByRole('button', { expanded: true })
        expect(header).toHaveAttribute('aria-expanded', 'true')
      })
    })

    it('should have proper tabIndex on header', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        const header = screen.getByRole('button', { expanded: true })
        expect(header).toHaveAttribute('tabIndex', '0')
      })
    })

    it('should have aria-label on refresh button', async () => {
      render(<SessionInsights {...defaultProps} />)
      
      await waitFor(() => {
        const refreshButton = screen.getByLabelText('Refresh insights')
        expect(refreshButton).toBeInTheDocument()
      })
    })
  })

  describe('Custom className', () => {
    it('should apply custom className', async () => {
      render(<SessionInsights {...defaultProps} className="custom-class" />)
      
      await waitFor(() => {
        expect(screen.getByText('Session Insights')).toBeInTheDocument()
      })
      
      const container = screen.getByText('Session Insights').closest('.custom-class')
      expect(container).toBeInTheDocument()
    })
  })
})
