import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Badge } from '../badge'

describe('Badge', () => {
  it('renders with default variant', () => {
    render(<Badge>Default Badge</Badge>)
    expect(screen.getByText('Default Badge')).toBeInTheDocument()
  })

  describe('variants', () => {
    it('renders default variant with correct styling', () => {
      const { container } = render(<Badge variant="default">Default</Badge>)
      const badge = container.firstChild as HTMLElement
      expect(badge).toHaveClass('bg-primary-500', 'text-white', 'border-transparent')
    })

    it('renders secondary variant with correct styling', () => {
      const { container } = render(<Badge variant="secondary">Secondary</Badge>)
      const badge = container.firstChild as HTMLElement
      expect(badge).toHaveClass('bg-neutral-100', 'text-neutral-700', 'border-transparent')
    })

    it('renders destructive variant with correct styling', () => {
      const { container } = render(<Badge variant="destructive">Destructive</Badge>)
      const badge = container.firstChild as HTMLElement
      expect(badge).toHaveClass('bg-error-500', 'text-white', 'border-transparent')
    })

    it('renders outline variant with correct styling', () => {
      const { container } = render(<Badge variant="outline">Outline</Badge>)
      const badge = container.firstChild as HTMLElement
      expect(badge).toHaveClass('text-neutral-700', 'bg-white')
      expect(badge).not.toHaveClass('border-transparent')
    })
  })

  it('renders as child component when asChild is true', () => {
    render(
      <Badge asChild>
        <a href="/badge">Badge Link</a>
      </Badge>
    )
    const link = screen.getByRole('link', { name: 'Badge Link' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/badge')
  })

  it('renders as span by default', () => {
    const { container } = render(<Badge>Badge</Badge>)
    const badge = container.firstChild as HTMLElement
    expect(badge.tagName).toBe('SPAN')
  })

  it('applies custom className', () => {
    const { container } = render(<Badge className="custom-badge">Custom</Badge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('custom-badge')
  })

  it('forwards additional props', () => {
    render(<Badge data-testid="test-badge" aria-label="Test Badge">Badge</Badge>)
    const badge = screen.getByTestId('test-badge')
    expect(badge).toHaveAttribute('aria-label', 'Test Badge')
  })

  it('includes data-slot attribute', () => {
    const { container } = render(<Badge>Badge</Badge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveAttribute('data-slot', 'badge')
  })

  it('renders with icon', () => {
    render(
      <Badge>
        <svg data-testid="badge-icon" />
        Badge with Icon
      </Badge>
    )
    expect(screen.getByTestId('badge-icon')).toBeInTheDocument()
    expect(screen.getByText('Badge with Icon')).toBeInTheDocument()
  })

  it('renders empty badge', () => {
    const { container } = render(<Badge />)
    const badge = container.firstChild as HTMLElement
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveAttribute('data-slot', 'badge')
  })

  it('handles long text with whitespace-nowrap', () => {
    const { container } = render(
      <Badge>This is a very long badge text that should not wrap</Badge>
    )
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('whitespace-nowrap')
  })

  it('applies focus-visible styles', () => {
    const { container } = render(<Badge>Badge</Badge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('focus-visible:border-ring', 'focus-visible:ring-ring/50')
  })

  it('applies hover styles when used as link', () => {
    const { container } = render(
      <Badge asChild>
        <a href="/test">Link Badge</a>
      </Badge>
    )
    const badge = container.firstChild as HTMLElement
    expect(badge.className).toContain('[a&]:hover:bg-primary-600')
  })
})
