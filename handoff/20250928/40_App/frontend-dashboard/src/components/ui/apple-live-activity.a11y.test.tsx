import { describe, it, expect, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { AppleLiveActivity } from './apple-live-activity'
import React from 'react'

expect.extend(toHaveNoViolations)

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => ({ announce: vi.fn() })
}))

describe('AppleLiveActivity Accessibility', () => {
  it('should not have any automatically detectable accessibility issues', async () => {
    const TestComponent = () => {
      const { addActivity } = AppleLiveActivity.useLiveActivity()
      React.useEffect(() => {
        addActivity({
          id: 'test-activity',
          title: 'Test Activity',
          subtitle: 'Test Subtitle',
          icon: <span>📱</span>,
          progress: 50
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleLiveActivity.Provider>
        <TestComponent />
      </AppleLiveActivity.Provider>
    )

    await waitFor(() => {
      expect(container.querySelector('[role="region"]')).toBeInTheDocument()
    })

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have proper ARIA attributes', async () => {
    const TestComponent = () => {
      const { addActivity } = AppleLiveActivity.useLiveActivity()
      React.useEffect(() => {
        addActivity({
          id: 'test-activity',
          title: 'Test Activity',
          subtitle: 'Test Subtitle',
          icon: <span>📱</span>
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleLiveActivity.Provider>
        <TestComponent />
      </AppleLiveActivity.Provider>
    )

    await waitFor(() => {
      const activity = container.querySelector('[role="region"]')
      expect(activity).toBeInTheDocument()
      expect(activity).toHaveAttribute('aria-label')
    })
  })

  it('should have keyboard accessible action buttons', async () => {
    const TestComponent = () => {
      const { addActivity } = AppleLiveActivity.useLiveActivity()
      React.useEffect(() => {
        addActivity({
          id: 'test-activity',
          title: 'Test Activity',
          subtitle: 'Test Subtitle',
          icon: <span>📱</span>,
          actions: [
            { id: 'action1', label: 'Action 1', variant: 'primary', onPress: () => {} }
          ]
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleLiveActivity.Provider>
        <TestComponent />
      </AppleLiveActivity.Provider>
    )

    await waitFor(() => {
      const buttons = container.querySelectorAll('button')
      expect(buttons.length).toBeGreaterThan(0)
      buttons.forEach(button => {
        expect(button).toHaveAttribute('tabIndex')
      })
    })
  })

  it('should have proper progress bar accessibility', async () => {
    const TestComponent = () => {
      const { addActivity } = AppleLiveActivity.useLiveActivity()
      React.useEffect(() => {
        addActivity({
          id: 'test-activity',
          title: 'Test Activity',
          subtitle: 'Test Subtitle',
          icon: <span>📱</span>,
          progress: 75
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleLiveActivity.Provider>
        <TestComponent />
      </AppleLiveActivity.Provider>
    )

    await waitFor(() => {
      const progressBar = container.querySelector('[role="progressbar"]')
      expect(progressBar).toBeInTheDocument()
      expect(progressBar).toHaveAttribute('aria-valuenow', '75')
      expect(progressBar).toHaveAttribute('aria-valuemin', '0')
      expect(progressBar).toHaveAttribute('aria-valuemax', '100')
    })
  })
})
