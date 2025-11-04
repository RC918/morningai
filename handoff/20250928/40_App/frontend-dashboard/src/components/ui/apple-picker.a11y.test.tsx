import { describe, it, expect, vi } from 'vitest'
import { render } from '@testing-library/react'
import { axe, toHaveNoViolations } from 'jest-axe'
import { ApplePicker, PickerColumn } from './apple-picker'

expect.extend(toHaveNoViolations)

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => ({ announce: vi.fn() })
}))

describe('ApplePicker Accessibility', () => {
  const testColumns: PickerColumn[] = [
    {
      id: 'hour',
      options: [
        { value: 1, label: '1' },
        { value: 2, label: '2' },
        { value: 3, label: '3' }
      ],
      selectedIndex: 0
    }
  ]

  it('should not have any automatically detectable accessibility issues', async () => {
    const { container } = render(
      <ApplePicker columns={testColumns} />
    )

    const results = await axe(container)
    expect(results).toHaveNoViolations()
  })

  it('should have proper listbox ARIA attributes', () => {
    const { container } = render(
      <ApplePicker columns={testColumns} />
    )

    const listbox = container.querySelector('[role="listbox"]')
    expect(listbox).toBeInTheDocument()
    expect(listbox).toHaveAttribute('aria-label')
    expect(listbox).toHaveAttribute('aria-activedescendant')
    expect(listbox).toHaveAttribute('tabIndex', '0')
  })

  it('should have proper option ARIA attributes', () => {
    const { container} = render(
      <ApplePicker columns={testColumns} />
    )

    const options = container.querySelectorAll('[role="option"]')
    expect(options.length).toBeGreaterThan(0)
    
    options.forEach(option => {
      expect(option).toHaveAttribute('id')
      expect(option).toHaveAttribute('aria-selected')
    })
  })

  it('should be keyboard navigable', () => {
    const { container } = render(
      <ApplePicker columns={testColumns} />
    )

    const listbox = container.querySelector('[role="listbox"]')
    expect(listbox).toHaveAttribute('tabIndex', '0')
  })

  it('should have focus ring styling', () => {
    const { container } = render(
      <ApplePicker columns={testColumns} />
    )

    const listbox = container.querySelector('[role="listbox"]')
    expect(listbox?.className).toContain('focus:ring')
  })
})
