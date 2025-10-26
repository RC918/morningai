import { describe, it, expect, vi } from 'vitest'
import { render, waitFor, fireEvent } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { AppleSpotlight } from './apple-spotlight'
import React from 'react'

expect.extend(toHaveNoViolations)

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => vi.fn(),
  useFocusTrap: () => {}
}))

describe('AppleSpotlight Accessibility', () => {
  it('should have proper searchbox ARIA attributes', async () => {
    const TestComponent = () => {
      const { open } = AppleSpotlight.useSpotlight()
      React.useEffect(() => {
        open()
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleSpotlight.Provider
        onSearch={(query) => []}
      >
        <TestComponent />
      </AppleSpotlight.Provider>
    )

    await waitFor(() => {
      const searchbox = container.querySelector('[role="searchbox"]')
      expect(searchbox).toBeInTheDocument()
      expect(searchbox).toHaveAttribute('aria-label')
      expect(searchbox).toHaveAttribute('aria-autocomplete', 'list')
      expect(searchbox).toHaveAttribute('aria-controls')
    })
  })

  it('should have proper listbox ARIA attributes', async () => {
    const TestComponent = () => {
      const { open } = AppleSpotlight.useSpotlight()
      React.useEffect(() => {
        open()
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleSpotlight.Provider
        onSearch={(query) => []}
      >
        <TestComponent />
      </AppleSpotlight.Provider>
    )

    await waitFor(() => {
      const listbox = container.querySelector('[role="listbox"]')
      expect(listbox).toBeInTheDocument()
      expect(listbox).toHaveAttribute('id', 'search-results')
    })
  })

  it('should have proper dialog ARIA attributes', async () => {
    const TestComponent = () => {
      const { open } = AppleSpotlight.useSpotlight()
      React.useEffect(() => {
        open()
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleSpotlight.Provider
        onSearch={(query) => []}
      >
        <TestComponent />
      </AppleSpotlight.Provider>
    )

    await waitFor(() => {
      const dialog = container.querySelector('[role="dialog"]')
      expect(dialog).toBeInTheDocument()
      expect(dialog).toHaveAttribute('aria-label')
      expect(dialog).toHaveAttribute('aria-modal', 'true')
    })
  })
})
