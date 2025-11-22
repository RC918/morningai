import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Button } from '../button'

describe('Button', () => {
  it('renders with default variant and size', () => {
    render(<Button>Click me</Button>)
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument()
  })

  describe('variants', () => {
    it('renders default variant with correct styling', () => {
      const { container } = render(<Button variant="default">Default</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('bg-primary', 'text-primary-foreground')
    })

    it('renders destructive variant with correct styling', () => {
      const { container } = render(<Button variant="destructive">Delete</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('bg-destructive', 'text-white')
    })

    it('renders outline variant with correct styling', () => {
      const { container } = render(<Button variant="outline">Outline</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('border', 'bg-background')
    })

    it('renders secondary variant with correct styling', () => {
      const { container } = render(<Button variant="secondary">Secondary</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('bg-secondary', 'text-secondary-foreground')
    })

    it('renders ghost variant with correct styling', () => {
      const { container } = render(<Button variant="ghost">Ghost</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('hover:bg-accent')
    })

    it('renders link variant with correct styling', () => {
      const { container } = render(<Button variant="link">Link</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('text-primary', 'underline-offset-4')
    })
  })

  describe('sizes', () => {
    it('renders default size', () => {
      const { container } = render(<Button size="default">Default</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('h-9', 'px-4', 'py-2')
    })

    it('renders small size', () => {
      const { container } = render(<Button size="sm">Small</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('h-8')
    })

    it('renders large size', () => {
      const { container } = render(<Button size="lg">Large</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('h-10')
    })

    it('renders icon size', () => {
      const { container } = render(<Button size="icon">🔍</Button>)
      const button = container.firstChild as HTMLElement
      expect(button).toHaveClass('size-9')
    })
  })

  it('handles click events', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<Button onClick={handleClick}>Click me</Button>)
    await user.click(screen.getByRole('button', { name: 'Click me' }))
    
    expect(handleClick).toHaveBeenCalledTimes(1)
  })

  it('does not trigger click when disabled', async () => {
    const handleClick = vi.fn()
    const user = userEvent.setup()
    
    render(<Button onClick={handleClick} disabled>Disabled</Button>)
    await user.click(screen.getByRole('button', { name: 'Disabled' }))
    
    expect(handleClick).not.toHaveBeenCalled()
  })

  it('applies disabled styling', () => {
    const { container } = render(<Button disabled>Disabled</Button>)
    const button = container.firstChild as HTMLElement
    expect(button).toHaveClass('disabled:pointer-events-none', 'disabled:opacity-50')
    expect(button).toBeDisabled()
  })

  it('renders as child component when asChild is true', () => {
    render(
      <Button asChild>
        <a href="/test">Link Button</a>
      </Button>
    )
    const link = screen.getByRole('link', { name: 'Link Button' })
    expect(link).toBeInTheDocument()
    expect(link).toHaveAttribute('href', '/test')
  })

  it('applies custom className', () => {
    const { container } = render(<Button className="custom-class">Custom</Button>)
    const button = container.firstChild as HTMLElement
    expect(button).toHaveClass('custom-class')
  })

  it('forwards additional props', () => {
    render(<Button data-testid="test-button" aria-label="Test">Button</Button>)
    const button = screen.getByTestId('test-button')
    expect(button).toHaveAttribute('aria-label', 'Test')
  })

  it('includes data-slot attribute for styling hooks', () => {
    render(<Button>Button</Button>)
    const button = screen.getByRole('button')
    expect(button).toHaveAttribute('data-slot', 'button')
  })

  it('applies focus-visible styles', () => {
    const { container } = render(<Button>Focus me</Button>)
    const button = container.firstChild as HTMLElement
    expect(button).toHaveClass('focus-visible:border-ring', 'focus-visible:ring-ring/50')
  })

  it('renders with empty children', () => {
    render(<Button />)
    expect(screen.getByRole('button')).toBeInTheDocument()
  })

  it('forwards type attribute', () => {
    render(<Button type="submit">Submit</Button>)
    expect(screen.getByRole('button')).toHaveAttribute('type', 'submit')
  })
})
