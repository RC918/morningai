import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { AppleSegmentedControl, AppleSegmentedControlItem } from './apple-segmented-control'

describe('AppleSegmentedControl', () => {
  it('renders segmented control with items', () => {
    render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    expect(screen.getByRole('tablist')).toBeInTheDocument()
    expect(screen.getByText('All')).toBeInTheDocument()
    expect(screen.getByText('Active')).toBeInTheDocument()
  })

  it('marks active segment with aria-selected', () => {
    render(
      <AppleSegmentedControl value="active" onValueChange={vi.fn()}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const allSegment = screen.getByText('All')
    const activeSegment = screen.getByText('Active')
    
    expect(allSegment).toHaveAttribute('aria-selected', 'false')
    expect(activeSegment).toHaveAttribute('aria-selected', 'true')
  })

  it('calls onValueChange when segment is clicked', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    fireEvent.click(screen.getByText('Active'))
    expect(handleChange).toHaveBeenCalledWith('active')
  })

  it('does not call onValueChange when disabled segment is clicked', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active" disabled>Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    fireEvent.click(screen.getByText('Active'))
    expect(handleChange).not.toHaveBeenCalled()
  })

  it('handles keyboard navigation with Enter key', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const activeSegment = screen.getByText('Active')
    fireEvent.keyDown(activeSegment, { key: 'Enter' })
    expect(handleChange).toHaveBeenCalledWith('active')
  })

  it('handles keyboard navigation with Space key', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const activeSegment = screen.getByText('Active')
    fireEvent.keyDown(activeSegment, { key: ' ' })
    expect(handleChange).toHaveBeenCalledWith('active')
  })

  it('does not trigger on other keys', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const activeSegment = screen.getByText('Active')
    fireEvent.keyDown(activeSegment, { key: 'a' })
    expect(handleChange).not.toHaveBeenCalled()
  })

  it('applies disabled styles to disabled segments', () => {
    render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active" disabled>Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const disabledSegment = screen.getByText('Active')
    expect(disabledSegment).toBeDisabled()
  })

  it('renders with small size', () => {
    const { container } = render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()} size="sm">
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const tablist = container.querySelector('[role="tablist"]')
    expect(tablist).toHaveClass('h-8')
  })

  it('renders with default size', () => {
    const { container } = render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()} size="default">
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const tablist = container.querySelector('[role="tablist"]')
    expect(tablist).toHaveClass('h-10')
  })

  it('renders with large size', () => {
    const { container } = render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()} size="lg">
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const tablist = container.querySelector('[role="tablist"]')
    expect(tablist).toHaveClass('h-12')
  })

  it('renders multiple segments correctly', () => {
    render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="archived">Archived</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    expect(screen.getAllByRole('tab')).toHaveLength(4)
  })

  it('handles custom className', () => {
    const { container } = render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()} className="custom-class">
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const tablist = container.querySelector('[role="tablist"]')
    expect(tablist).toHaveClass('custom-class')
  })

  it('handles custom onClick handler', () => {
    const handleClick = vi.fn()
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="active" onClick={handleClick}>
          Active
        </AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    fireEvent.click(screen.getByText('Active'))
    expect(handleClick).toHaveBeenCalled()
    expect(handleChange).toHaveBeenCalledWith('active')
  })

  it('has proper accessibility attributes', () => {
    render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()}>
        <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const tablist = screen.getByRole('tablist')
    expect(tablist).toHaveAttribute('aria-label', 'Segmented control')
    
    const tabs = screen.getAllByRole('tab')
    tabs.forEach(tab => {
      expect(tab).toHaveAttribute('aria-selected')
      expect(tab).toHaveAttribute('type', 'button')
    })
  })

  it('renders with icons', () => {
    render(
      <AppleSegmentedControl value="all" onValueChange={vi.fn()}>
        <AppleSegmentedControlItem value="all">
          <span data-testid="icon">📋</span>
          All
        </AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    expect(screen.getByTestId('icon')).toBeInTheDocument()
    expect(screen.getByText('All')).toBeInTheDocument()
  })

  it('prevents default on Enter key', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const activeSegment = screen.getByText('Active')
    const event = new KeyboardEvent('keydown', { key: 'Enter', bubbles: true })
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
    
    activeSegment.dispatchEvent(event)
    expect(preventDefaultSpy).toHaveBeenCalled()
  })

  it('prevents default on Space key', () => {
    const handleChange = vi.fn()
    
    render(
      <AppleSegmentedControl value="all" onValueChange={handleChange}>
        <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      </AppleSegmentedControl>
    )
    
    const activeSegment = screen.getByText('Active')
    const event = new KeyboardEvent('keydown', { key: ' ', bubbles: true })
    const preventDefaultSpy = vi.spyOn(event, 'preventDefault')
    
    activeSegment.dispatchEvent(event)
    expect(preventDefaultSpy).toHaveBeenCalled()
  })
})
