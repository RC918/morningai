import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { SessionStatusCard } from '../SessionStatusCard'
import { Activity, Play, Pause, CheckCircle, XCircle } from 'lucide-react'

describe('SessionStatusCard', () => {
  const defaultProps = {
    label: 'Test Label',
    value: '42',
    icon: <Activity data-testid="icon" />,
    onClick: vi.fn(),
  }

  describe('rendering', () => {
    it('renders label and value correctly', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      expect(screen.getByText('Test Label')).toBeInTheDocument()
      expect(screen.getByText('42')).toBeInTheDocument()
    })

    it('renders icon correctly', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      expect(screen.getByTestId('icon')).toBeInTheDocument()
    })

    it('renders as a button element', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
      expect(button).toHaveAttribute('type', 'button')
    })
  })

  describe('accessibility', () => {
    it('has aria-pressed attribute reflecting isActive state', () => {
      const { rerender } = render(<SessionStatusCard {...defaultProps} isActive={false} />)
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'false')
      
      rerender(<SessionStatusCard {...defaultProps} isActive={true} />)
      
      expect(screen.getByRole('button')).toHaveAttribute('aria-pressed', 'true')
    })

    it('has focus-visible ring with accessibility CSS variable', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('focus-visible:ring-[var(--accessibility-focus-outline-color)]')
    })
  })

  describe('interactions', () => {
    it('calls onClick when clicked', () => {
      const onClick = vi.fn()
      render(<SessionStatusCard {...defaultProps} onClick={onClick} />)
      
      fireEvent.click(screen.getByRole('button'))
      
      expect(onClick).toHaveBeenCalledTimes(1)
    })
  })

  describe('variants', () => {
    it('applies default variant styles when no variant specified', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    it('applies blue variant styles', () => {
      render(<SessionStatusCard {...defaultProps} variant="blue" isActive={true} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('bg-primary-50')
      expect(button.className).toContain('border-primary-500')
    })

    it('applies green variant styles', () => {
      render(<SessionStatusCard {...defaultProps} variant="green" isActive={true} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('bg-success-50')
      expect(button.className).toContain('border-success-500')
    })

    it('applies yellow variant styles', () => {
      render(<SessionStatusCard {...defaultProps} variant="yellow" isActive={true} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('bg-warning-50')
      expect(button.className).toContain('border-warning-500')
    })

    it('applies red variant styles', () => {
      render(<SessionStatusCard {...defaultProps} variant="red" isActive={true} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('bg-error-50')
      expect(button.className).toContain('border-error-500')
    })
  })

  describe('active state', () => {
    it('applies active background and border when active', () => {
      render(<SessionStatusCard {...defaultProps} variant="blue" isActive={true} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('bg-primary-50')
      expect(button.className).toContain('border-primary-500')
    })

    it('applies shadow-md when active', () => {
      render(<SessionStatusCard {...defaultProps} isActive={true} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('shadow-md')
    })
  })

  describe('dimensions', () => {
    it('has fixed height h-24 (96px)', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('h-24')
    })

    it('has minimum width min-w-[140px]', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('min-w-[140px]')
    })

    it('has consistent padding p-4 (matching StatCard)', () => {
      render(<SessionStatusCard {...defaultProps} />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('p-4')
    })
  })

  describe('icon container', () => {
    it('has icon container matching StatCard dimensions (h-10 w-10 rounded-full)', () => {
      const { container } = render(<SessionStatusCard {...defaultProps} />)
      
      const iconContainer = container.querySelector('.h-10.w-10.rounded-full')
      expect(iconContainer).toBeInTheDocument()
    })

    it('renders with Play icon for running status', () => {
      render(<SessionStatusCard {...defaultProps} icon={<Play data-testid="play-icon" />} variant="blue" />)
      
      expect(screen.getByTestId('play-icon')).toBeInTheDocument()
    })

    it('renders with Pause icon for paused status', () => {
      render(<SessionStatusCard {...defaultProps} icon={<Pause data-testid="pause-icon" />} variant="yellow" />)
      
      expect(screen.getByTestId('pause-icon')).toBeInTheDocument()
    })

    it('renders with CheckCircle icon for completed status', () => {
      render(<SessionStatusCard {...defaultProps} icon={<CheckCircle data-testid="check-icon" />} variant="green" />)
      
      expect(screen.getByTestId('check-icon')).toBeInTheDocument()
    })

    it('renders with XCircle icon for failed status', () => {
      render(<SessionStatusCard {...defaultProps} icon={<XCircle data-testid="x-icon" />} variant="red" />)
      
      expect(screen.getByTestId('x-icon')).toBeInTheDocument()
    })
  })

  describe('custom className', () => {
    it('applies custom className to button', () => {
      render(<SessionStatusCard {...defaultProps} className="custom-class" />)
      
      const button = screen.getByRole('button')
      expect(button.className).toContain('custom-class')
    })
  })
})
