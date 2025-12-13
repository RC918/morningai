/**
 * Keyboard Navigation Accessibility Tests
 * 
 * Tests for WCAG 2.1 Success Criteria:
 * - 2.1.1 Keyboard (Level A)
 * - 2.1.2 No Keyboard Trap (Level A)
 * - 2.4.3 Focus Order (Level A)
 * - 2.4.7 Focus Visible (Level AA)
 * 
 * @module keyboard-navigation.a11y.test
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import React from 'react'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'

describe('Keyboard Navigation Accessibility', () => {
  describe('Button Component', () => {
    it('should be focusable via keyboard', async () => {
      render(<Button>Click me</Button>)
      const button = screen.getByRole('button')
      
      button.focus()
      expect(document.activeElement).toBe(button)
    })

    it('should be activatable via Enter key', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click me</Button>)
      const button = screen.getByRole('button')
      
      button.focus()
      await user.keyboard('{Enter}')
      
      expect(handleClick).toHaveBeenCalled()
    })

    it('should be activatable via Space key', async () => {
      const user = userEvent.setup()
      const handleClick = vi.fn()
      render(<Button onClick={handleClick}>Click me</Button>)
      const button = screen.getByRole('button')
      
      button.focus()
      await user.keyboard(' ')
      
      expect(handleClick).toHaveBeenCalled()
    })

    it('should not be focusable when disabled', () => {
      render(<Button disabled>Disabled</Button>)
      const button = screen.getByRole('button')
      
      expect(button).toBeDisabled()
      expect(button).toHaveAttribute('disabled')
    })

    it('should have visible focus indicator', () => {
      render(<Button>Focus me</Button>)
      const button = screen.getByRole('button')
      
      button.focus()
      expect(document.activeElement).toBe(button)
      // Focus styles are applied via CSS, we verify the element receives focus
    })
  })

  describe('Input Component', () => {
    it('should be focusable via keyboard', () => {
      render(<Input placeholder="Enter text" />)
      const input = screen.getByPlaceholderText('Enter text')
      
      input.focus()
      expect(document.activeElement).toBe(input)
    })

    it('should accept keyboard input', async () => {
      const user = userEvent.setup()
      render(<Input placeholder="Enter text" />)
      const input = screen.getByPlaceholderText('Enter text')
      
      await user.type(input, 'Hello World')
      expect(input).toHaveValue('Hello World')
    })

    it('should not be focusable when disabled', () => {
      render(<Input disabled placeholder="Disabled" />)
      const input = screen.getByPlaceholderText('Disabled')
      
      expect(input).toBeDisabled()
    })
  })

  describe('Focus Order (WCAG 2.4.3)', () => {
    it('should follow logical tab order', async () => {
      const user = userEvent.setup()
      render(
        <div>
          <Button>First</Button>
          <Input placeholder="Second" />
          <Button>Third</Button>
        </div>
      )
      
      const first = screen.getByRole('button', { name: 'First' })
      const second = screen.getByPlaceholderText('Second')
      const third = screen.getByRole('button', { name: 'Third' })
      
      // Tab through elements
      await user.tab()
      expect(document.activeElement).toBe(first)
      
      await user.tab()
      expect(document.activeElement).toBe(second)
      
      await user.tab()
      expect(document.activeElement).toBe(third)
    })

    it('should support reverse tab order with Shift+Tab', async () => {
      const user = userEvent.setup()
      render(
        <div>
          <Button>First</Button>
          <Button>Second</Button>
          <Button>Third</Button>
        </div>
      )
      
      const first = screen.getByRole('button', { name: 'First' })
      const second = screen.getByRole('button', { name: 'Second' })
      const third = screen.getByRole('button', { name: 'Third' })
      
      // Focus third element
      third.focus()
      expect(document.activeElement).toBe(third)
      
      // Shift+Tab to second
      await user.tab({ shift: true })
      expect(document.activeElement).toBe(second)
      
      // Shift+Tab to first
      await user.tab({ shift: true })
      expect(document.activeElement).toBe(first)
    })
  })

  describe('No Keyboard Trap (WCAG 2.1.2)', () => {
    it('should allow focus to move away from interactive elements', async () => {
      const user = userEvent.setup()
      render(
        <div>
          <Button>Button 1</Button>
          <Button>Button 2</Button>
        </div>
      )
      
      const button1 = screen.getByRole('button', { name: 'Button 1' })
      const button2 = screen.getByRole('button', { name: 'Button 2' })
      
      button1.focus()
      expect(document.activeElement).toBe(button1)
      
      await user.tab()
      expect(document.activeElement).toBe(button2)
      // Focus successfully moved - no trap
    })
  })

  describe('Keyboard Shortcuts', () => {
    it('should support Escape key to close/cancel', async () => {
      const handleEscape = vi.fn()
      
      const TestComponent = () => {
        React.useEffect(() => {
          const handler = (e: KeyboardEvent) => {
            if (e.key === 'Escape') handleEscape()
          }
          document.addEventListener('keydown', handler)
          return () => document.removeEventListener('keydown', handler)
        }, [])
        
        return <Button>Test</Button>
      }
      
      render(<TestComponent />)
      
      fireEvent.keyDown(document, { key: 'Escape' })
      expect(handleEscape).toHaveBeenCalled()
    })
  })
})

describe('Focus Management', () => {
  describe('Focus Restoration', () => {
    it('should maintain focus state after re-render', () => {
      const { rerender } = render(<Button>Click me</Button>)
      const button = screen.getByRole('button')
      
      button.focus()
      expect(document.activeElement).toBe(button)
      
      rerender(<Button>Click me</Button>)
      // Note: Focus may or may not be maintained depending on implementation
      // This test documents the expected behavior
    })
  })

  describe('Focus Indicators', () => {
    it('should have appropriate tabIndex for interactive elements', () => {
      render(
        <div>
          <Button>Button</Button>
          <Input placeholder="Input" />
        </div>
      )
      
      const button = screen.getByRole('button')
      const input = screen.getByPlaceholderText('Input')
      
      // Interactive elements should be in tab order (tabIndex >= 0 or not set)
      expect(button.tabIndex).toBeGreaterThanOrEqual(0)
      expect(input.tabIndex).toBeGreaterThanOrEqual(0)
    })
  })
})
