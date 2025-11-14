import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { StatusBadge } from '../status-badge'

describe('StatusBadge', () => {
  it('renders with default status (queued)', () => {
    render(<StatusBadge>Queued</StatusBadge>)
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })

  it('renders completed status with correct styling', () => {
    const { container } = render(<StatusBadge status="completed">Completed</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('bg-green-100', 'text-green-800', 'border-green-300')
    expect(screen.getByText('Completed')).toBeInTheDocument()
  })

  it('renders running status with correct styling', () => {
    const { container } = render(<StatusBadge status="running">Running</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('bg-blue-100', 'text-blue-800', 'border-blue-300')
    expect(screen.getByText('Running')).toBeInTheDocument()
  })

  it('renders failed status with correct styling', () => {
    const { container } = render(<StatusBadge status="failed">Failed</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('bg-red-100', 'text-red-800', 'border-red-300')
    expect(screen.getByText('Failed')).toBeInTheDocument()
  })

  it('renders queued status with correct styling', () => {
    const { container } = render(<StatusBadge status="queued">Queued</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('bg-gray-100', 'text-gray-800', 'border-gray-300')
    expect(screen.getByText('Queued')).toBeInTheDocument()
  })

  it('renders assigned status with correct styling', () => {
    const { container } = render(<StatusBadge status="assigned">Assigned</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('bg-yellow-100', 'text-yellow-800', 'border-yellow-300')
    expect(screen.getByText('Assigned')).toBeInTheDocument()
  })

  it('renders cancelled status with correct styling', () => {
    const { container } = render(<StatusBadge status="cancelled">Cancelled</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('bg-orange-100', 'text-orange-800', 'border-orange-300')
    expect(screen.getByText('Cancelled')).toBeInTheDocument()
  })

  it('renders with icon by default', () => {
    const { container } = render(<StatusBadge status="completed">Completed</StatusBadge>)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })

  it('hides icon when showIcon is false', () => {
    const { container } = render(
      <StatusBadge status="completed" showIcon={false}>
        Completed
      </StatusBadge>
    )
    const svg = container.querySelector('svg')
    expect(svg).not.toBeInTheDocument()
  })

  it('renders custom icon when provided', () => {
    const CustomIcon = () => <span data-testid="custom-icon">★</span>
    render(
      <StatusBadge status="completed" icon={<CustomIcon />}>
        Completed
      </StatusBadge>
    )
    expect(screen.getByTestId('custom-icon')).toBeInTheDocument()
  })

  it('applies custom className', () => {
    const { container } = render(
      <StatusBadge status="completed" className="custom-class">
        Completed
      </StatusBadge>
    )
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('custom-class')
  })

  it('forwards additional props', () => {
    render(
      <StatusBadge status="completed" data-testid="status-badge">
        Completed
      </StatusBadge>
    )
    expect(screen.getByTestId('status-badge')).toBeInTheDocument()
  })

  it('renders running status with animated icon (respects prefers-reduced-motion)', () => {
    const { container } = render(<StatusBadge status="running">Running</StatusBadge>)
    const svg = container.querySelector('svg')
    expect(svg).toHaveClass('motion-safe:animate-pulse')
    expect(svg).toHaveClass('motion-reduce:animate-none')
  })

  it('includes gap-1 for icon/text spacing', () => {
    const { container } = render(<StatusBadge status="completed">Completed</StatusBadge>)
    const badge = container.firstChild as HTMLElement
    expect(badge).toHaveClass('gap-1')
  })
})
