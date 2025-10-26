import { describe, it, expect, vi } from 'vitest'
import { render, waitFor } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { AppleControlCenter } from './apple-control-center'
import React from 'react'

expect.extend(toHaveNoViolations)

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => vi.fn(),
  useFocusTrap: () => {}
}))

describe('AppleControlCenter Accessibility', () => {
  it('should not have any automatically detectable accessibility issues', async () => {
    const TestComponent = () => {
      const { open } = AppleControlCenter.useControlCenter()
      React.useEffect(() => {
        open()
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleControlCenter.Provider
        controls={[
          { id: 'wifi', title: 'Wi-Fi', icon: <span>📶</span>, active: true }
        ]}
      >
        <TestComponent />
      </AppleControlCenter.Provider>
    )

    await waitFor(() => {
      expect(container.querySelector('[role="dialog"]')).toBeInTheDocument()
    })

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have proper dialog ARIA attributes', async () => {
    const TestComponent = () => {
      const { open } = AppleControlCenter.useControlCenter()
      React.useEffect(() => {
        open()
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleControlCenter.Provider
        controls={[
          { id: 'wifi', title: 'Wi-Fi', icon: <span>📶</span>, active: true }
        ]}
      >
        <TestComponent />
      </AppleControlCenter.Provider>
    )

    await waitFor(() => {
      const dialog = container.querySelector('[role="dialog"]')
      expect(dialog).toBeInTheDocument()
      expect(dialog).toHaveAttribute('aria-modal', 'true')
      expect(dialog).toHaveAttribute('aria-label')
    })
  })

  it('should have keyboard accessible controls', async () => {
    const TestComponent = () => {
      const { open } = AppleControlCenter.useControlCenter()
      React.useEffect(() => {
        open()
      }, [])
      return <div>Test</div>
    }

    const { container } = render(
      <AppleControlCenter.Provider
        controls={[
          { id: 'wifi', title: 'Wi-Fi', icon: <span>📶</span>, active: true }
        ]}
      >
        <TestComponent />
      </AppleControlCenter.Provider>
    )

    await waitFor(() => {
      const controls = container.querySelectorAll('[role="button"]')
      controls.forEach(control => {
        expect(control).toHaveAttribute('tabIndex')
        expect(control).toHaveAttribute('aria-label')
      })
    })
  })
})
