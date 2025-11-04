import { describe, it, expect, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { AppleActionSheet } from './apple-action-sheet'
import React from 'react'

expect.extend(toHaveNoViolations)

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => ({ announce: vi.fn() })
}))

describe('AppleActionSheet Accessibility', () => {
  it('should not have any automatically detectable accessibility issues', async () => {
    const TestComponent = () => {
      const { show } = AppleActionSheet.useActionSheet()
      React.useEffect(() => {
        show({
          title: 'Test Action Sheet',
          message: 'Test Message',
          actions: [
            { id: '1', label: 'Action 1', onSelect: () => {} }
          ]
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleActionSheet.Provider>
        <TestComponent />
      </AppleActionSheet.Provider>
    )

    await waitFor(() => {
      expect(container.querySelector('[role="dialog"]')).toBeInTheDocument()
    })

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have proper dialog ARIA attributes', async () => {
    const TestComponent = () => {
      const { show } = AppleActionSheet.useActionSheet()
      React.useEffect(() => {
        show({
          title: 'Test Title',
          message: 'Test Message',
          actions: [
            { id: '1', label: 'Action 1', onSelect: () => {} }
          ]
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleActionSheet.Provider>
        <TestComponent />
      </AppleActionSheet.Provider>
    )

    await waitFor(() => {
      const dialog = container.querySelector('[role="dialog"]')
      expect(dialog).toBeInTheDocument()
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-labelledby')
      expect(dialog).toHaveAttribute('aria-describedby')
    })
  })

  it('should have keyboard accessible action buttons', async () => {
    const TestComponent = () => {
      const { show } = AppleActionSheet.useActionSheet()
      React.useEffect(() => {
        show({
          title: 'Test',
          actions: [
            { id: '1', label: 'Action 1', onSelect: () => {} },
            { id: '2', label: 'Action 2', destructive: true, onSelect: () => {} }
          ]
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleActionSheet.Provider>
        <TestComponent />
      </AppleActionSheet.Provider>
    )

    await waitFor(() => {
      const buttons = container.querySelectorAll('button')
      buttons.forEach(button => {
        expect(button).toHaveAttribute('aria-label')
      })
    })
  })

  it('should properly label destructive actions', async () => {
    const TestComponent = () => {
      const { show } = AppleActionSheet.useActionSheet()
      React.useEffect(() => {
        show({
          title: 'Test',
          actions: [
            { id: '1', label: 'Delete', destructive: true, onSelect: () => {} }
          ]
        })
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleActionSheet.Provider>
        <TestComponent />
      </AppleActionSheet.Provider>
    )

    await waitFor(() => {
      const deleteButton = Array.from(container.querySelectorAll('button'))
        .find(btn => btn.textContent?.includes('Delete'))
      expect(deleteButton).toHaveAttribute('aria-label')
      expect(deleteButton?.getAttribute('aria-label')).toContain('destructive')
    })
  })
})
