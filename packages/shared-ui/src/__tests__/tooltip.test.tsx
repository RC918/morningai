import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'

// Mock @radix-ui/react-tooltip to avoid dealing with its internal context and portals
vi.mock('@radix-ui/react-tooltip', () => {
  const Provider = ({ children, ...props }: { children: React.ReactNode }) => (
    <div data-testid="tooltip-provider" {...props}>{children}</div>
  )
  const Root = ({ children, ...props }: { children: React.ReactNode }) => (
    <div data-testid="tooltip-root" {...props}>{children}</div>
  )
  const Trigger = ({ children, ...props }: { children: React.ReactNode }) => (
    <button data-testid="tooltip-trigger" {...props}>{children}</button>
  )
  const Portal = ({ children }: { children: React.ReactNode }) => (
    <>{children}</>
  )
  const Content = ({ children, className, ...props }: { children: React.ReactNode; className?: string }) => (
    <div data-testid="tooltip-content" className={className} {...props}>{children}</div>
  )
  const Arrow = ({ className, ...props }: { className?: string }) => (
    <div data-testid="tooltip-arrow" className={className} {...props} />
  )

  return {
    Provider,
    Root,
    Trigger,
    Portal,
    Content,
    Arrow,
  }
})

import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from '../components/ui/tooltip'

describe('Tooltip', () => {
  describe('TooltipContent', () => {
    it('renders children correctly', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent>Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      expect(screen.getByText('Tooltip text')).toBeInTheDocument()
    })

    it('applies custom className to content', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent className="custom-class">Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      const content = screen.getByTestId('tooltip-content')
      expect(content).toHaveClass('custom-class')
    })
  })

  describe('arrowClassName prop', () => {
    it('applies default primary styling when arrowClassName is not provided', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent>Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      const arrow = screen.getByTestId('tooltip-arrow')
      expect(arrow).toHaveClass('bg-primary')
      expect(arrow).toHaveClass('fill-primary')
    })

    it('applies base geometry classes regardless of arrowClassName', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent arrowClassName="bg-white fill-white">Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      const arrow = screen.getByTestId('tooltip-arrow')
      expect(arrow).toHaveClass('z-50')
      expect(arrow).toHaveClass('size-2.5')
      expect(arrow).toHaveClass('rotate-45')
      expect(arrow).toHaveClass('rounded-[2px]')
    })

    it('applies custom arrowClassName when provided', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent arrowClassName="bg-white fill-white">Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      const arrow = screen.getByTestId('tooltip-arrow')
      expect(arrow).toHaveClass('bg-white')
      expect(arrow).toHaveClass('fill-white')
    })

    it('overrides default primary styling when arrowClassName is provided', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent arrowClassName="bg-white fill-white">Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      const arrow = screen.getByTestId('tooltip-arrow')
      // When arrowClassName is provided, bg-primary and fill-primary should NOT be present
      expect(arrow.className).not.toContain('bg-primary')
      expect(arrow.className).not.toContain('fill-primary')
    })

    it('supports dark mode responsive classes in arrowClassName', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent arrowClassName="bg-white fill-white dark:bg-neutral-800 dark:fill-neutral-800">
            Tooltip text
          </TooltipContent>
        </Tooltip>
      )
      
      const arrow = screen.getByTestId('tooltip-arrow')
      expect(arrow).toHaveClass('bg-white')
      expect(arrow).toHaveClass('fill-white')
      expect(arrow).toHaveClass('dark:bg-neutral-800')
      expect(arrow).toHaveClass('dark:fill-neutral-800')
    })
  })

  describe('TooltipProvider', () => {
    it('renders with default delayDuration of 0', () => {
      render(
        <TooltipProvider>
          <div>Content</div>
        </TooltipProvider>
      )
      
      expect(screen.getByText('Content')).toBeInTheDocument()
    })

    it('accepts custom delayDuration', () => {
      render(
        <TooltipProvider delayDuration={500}>
          <div>Content</div>
        </TooltipProvider>
      )
      
      expect(screen.getByText('Content')).toBeInTheDocument()
    })
  })

  describe('TooltipTrigger', () => {
    it('renders trigger element', () => {
      render(
        <Tooltip>
          <TooltipTrigger>Click me</TooltipTrigger>
          <TooltipContent>Tooltip text</TooltipContent>
        </Tooltip>
      )
      
      expect(screen.getByText('Click me')).toBeInTheDocument()
    })
  })
})
