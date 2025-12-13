/**
 * ARIA Attributes Accessibility Tests
 * 
 * Tests for WCAG 2.1 Success Criteria:
 * - 1.3.1 Info and Relationships (Level A)
 * - 4.1.2 Name, Role, Value (Level A)
 * - 4.1.3 Status Messages (Level AA)
 * 
 * @module aria-attributes.a11y.test
 */

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import React from 'react'
import { Button } from '../components/ui/button'
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../components/ui/card'
import { Alert, AlertTitle, AlertDescription } from '../components/ui/alert'
import { Slider } from '../components/ui/slider'

describe('ARIA Attributes Accessibility', () => {
  describe('Button Component ARIA', () => {
    it('should have correct role="button"', () => {
      render(<Button>Click me</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeInTheDocument()
    })

    it('should support aria-label for icon-only buttons', () => {
      render(<Button aria-label="Close dialog">X</Button>)
      const button = screen.getByRole('button', { name: 'Close dialog' })
      expect(button).toBeInTheDocument()
      expect(button).toHaveAttribute('aria-label', 'Close dialog')
    })

    it('should support aria-disabled state', () => {
      render(<Button disabled>Disabled</Button>)
      const button = screen.getByRole('button')
      expect(button).toBeDisabled()
    })

    it('should support aria-pressed for toggle buttons', () => {
      render(<Button aria-pressed="true">Toggle</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-pressed', 'true')
    })

    it('should support aria-expanded for expandable buttons', () => {
      render(<Button aria-expanded="false">Expand</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-expanded', 'false')
    })

    it('should support aria-haspopup for menu buttons', () => {
      render(<Button aria-haspopup="menu">Menu</Button>)
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-haspopup', 'menu')
    })

    it('should support aria-describedby for additional context', () => {
      render(
        <div>
          <Button aria-describedby="help-text">Submit</Button>
          <span id="help-text">Click to submit the form</span>
        </div>
      )
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-describedby', 'help-text')
    })
  })

  describe('Input Component ARIA', () => {
    it('should have correct role for text input', () => {
      render(<Input type="text" placeholder="Enter text" />)
      const input = screen.getByPlaceholderText('Enter text')
      expect(input).toHaveAttribute('type', 'text')
    })

    it('should support aria-label', () => {
      render(<Input aria-label="Search" />)
      const input = screen.getByRole('textbox', { name: 'Search' })
      expect(input).toBeInTheDocument()
    })

    it('should support aria-required', () => {
      render(<Input aria-required="true" placeholder="Required field" />)
      const input = screen.getByPlaceholderText('Required field')
      expect(input).toHaveAttribute('aria-required', 'true')
    })

    it('should support aria-invalid for validation errors', () => {
      render(<Input aria-invalid="true" placeholder="Invalid input" />)
      const input = screen.getByPlaceholderText('Invalid input')
      expect(input).toHaveAttribute('aria-invalid', 'true')
    })

    it('should support aria-describedby for error messages', () => {
      render(
        <div>
          <Input aria-describedby="error-msg" aria-invalid="true" placeholder="Email" />
          <span id="error-msg">Please enter a valid email</span>
        </div>
      )
      const input = screen.getByPlaceholderText('Email')
      expect(input).toHaveAttribute('aria-describedby', 'error-msg')
    })

    it('should support disabled state', () => {
      render(<Input disabled placeholder="Disabled" />)
      const input = screen.getByPlaceholderText('Disabled')
      expect(input).toBeDisabled()
    })
  })

  describe('Badge Component ARIA', () => {
    it('should have status role when conveying information', () => {
      render(<Badge role="status">New</Badge>)
      const badge = screen.getByRole('status')
      expect(badge).toHaveTextContent('New')
    })

    it('should support aria-label for status badges', () => {
      render(<Badge aria-label="3 new notifications">3</Badge>)
      const badge = screen.getByLabelText('3 new notifications')
      expect(badge).toBeInTheDocument()
    })
  })

  describe('Card Component ARIA', () => {
    it('should have appropriate structure with accessible content', () => {
      render(
        <Card>
          <CardHeader>
            <CardTitle>Card Title</CardTitle>
            <CardDescription>Card description</CardDescription>
          </CardHeader>
          <CardContent>Card content</CardContent>
        </Card>
      )
      
      const title = screen.getByText('Card Title')
      expect(title).toBeInTheDocument()
      expect(title).toHaveAttribute('data-slot', 'card-title')
      expect(screen.getByText('Card description')).toBeInTheDocument()
      expect(screen.getByText('Card content')).toBeInTheDocument()
    })

    it('should support role="article" for standalone cards', () => {
      render(
        <Card role="article">
          <CardContent>Article content</CardContent>
        </Card>
      )
      const card = screen.getByRole('article')
      expect(card).toBeInTheDocument()
    })

    it('should support aria-labelledby for card title', () => {
      render(
        <Card aria-labelledby="card-title">
          <CardHeader>
            <CardTitle id="card-title">Important Card</CardTitle>
          </CardHeader>
        </Card>
      )
      const card = screen.getByLabelText('Important Card')
      expect(card).toBeInTheDocument()
    })
  })

  describe('Alert Component ARIA', () => {
    it('should have role="alert" for important messages', () => {
      render(
        <Alert>
          <AlertTitle>Alert</AlertTitle>
          <AlertDescription>This is an alert message</AlertDescription>
        </Alert>
      )
      const alert = screen.getByRole('alert')
      expect(alert).toBeInTheDocument()
    })

    it('should contain accessible title and description', () => {
      render(
        <Alert>
          <AlertTitle>Warning</AlertTitle>
          <AlertDescription>Please review your input</AlertDescription>
        </Alert>
      )
      expect(screen.getByText('Warning')).toBeInTheDocument()
      expect(screen.getByText('Please review your input')).toBeInTheDocument()
    })
  })

  describe('ARIA Live Regions', () => {
    it('should support aria-live for dynamic content', () => {
      render(
        <div aria-live="polite" aria-atomic="true" data-testid="live-region">
          Status: Loading...
        </div>
      )
      const liveRegion = screen.getByTestId('live-region')
      expect(liveRegion).toHaveAttribute('aria-live', 'polite')
    })

    it('should support aria-busy for loading states', () => {
      render(
        <div aria-busy="true" aria-live="polite">
          Loading content...
        </div>
      )
      const element = screen.getByText('Loading content...')
      expect(element).toHaveAttribute('aria-busy', 'true')
    })
  })

  describe('ARIA Relationships', () => {
    it('should support aria-controls', () => {
      render(
        <div>
          <Button aria-controls="panel" aria-expanded="false">
            Toggle Panel
          </Button>
          <div id="panel" hidden>Panel content</div>
        </div>
      )
      const button = screen.getByRole('button')
      expect(button).toHaveAttribute('aria-controls', 'panel')
    })

    it('should support aria-owns for composite widgets', () => {
      render(
        <div aria-owns="owned-element" data-testid="parent-element">
          Parent
          <div id="owned-element">Owned child</div>
        </div>
      )
      const parent = screen.getByTestId('parent-element')
      expect(parent).toHaveAttribute('aria-owns', 'owned-element')
    })
  })

  describe('Accessible Names (WCAG 4.1.2)', () => {
    it('should have accessible name from text content', () => {
      render(<Button>Submit Form</Button>)
      const button = screen.getByRole('button', { name: 'Submit Form' })
      expect(button).toBeInTheDocument()
    })

    it('should have accessible name from aria-label', () => {
      render(<Button aria-label="Close">X</Button>)
      const button = screen.getByRole('button', { name: 'Close' })
      expect(button).toBeInTheDocument()
    })

    it('should have accessible name from aria-labelledby', () => {
      render(
        <div>
          <span id="btn-label">Custom Label</span>
          <Button aria-labelledby="btn-label">Button</Button>
        </div>
      )
      const button = screen.getByRole('button', { name: 'Custom Label' })
      expect(button).toBeInTheDocument()
    })
  })

  describe('Slider Component ARIA', () => {
    it('should support thumbLabel for single thumb slider', () => {
      render(<Slider defaultValue={[50]} thumbLabel="Volume" />)
      const slider = screen.getByRole('slider', { name: 'Volume' })
      expect(slider).toBeInTheDocument()
      expect(slider).toHaveAttribute('aria-label', 'Volume')
    })

    it('should support thumbLabel array for range slider', () => {
      render(
        <Slider 
          defaultValue={[25, 75]} 
          thumbLabel={['Minimum price', 'Maximum price']} 
        />
      )
      const minSlider = screen.getByRole('slider', { name: 'Minimum price' })
      const maxSlider = screen.getByRole('slider', { name: 'Maximum price' })
      expect(minSlider).toBeInTheDocument()
      expect(maxSlider).toBeInTheDocument()
    })

    it('should have correct aria-valuemin and aria-valuemax', () => {
      render(<Slider defaultValue={[50]} min={0} max={100} thumbLabel="Value" />)
      const slider = screen.getByRole('slider', { name: 'Value' })
      expect(slider).toHaveAttribute('aria-valuemin', '0')
      expect(slider).toHaveAttribute('aria-valuemax', '100')
    })

    it('should have correct aria-valuenow', () => {
      render(<Slider defaultValue={[75]} thumbLabel="Progress" />)
      const slider = screen.getByRole('slider', { name: 'Progress' })
      expect(slider).toHaveAttribute('aria-valuenow', '75')
    })

    it('should support disabled state', () => {
      render(<Slider defaultValue={[50]} disabled thumbLabel="Disabled slider" />)
      const slider = screen.getByRole('slider', { name: 'Disabled slider' })
      expect(slider).toHaveAttribute('data-disabled', '')
    })

    it('should provide fallback label when thumbLabel array is shorter than thumb count', () => {
      render(<Slider defaultValue={[25, 50, 75]} thumbLabel={['First']} />)
      const firstSlider = screen.getByRole('slider', { name: 'First' })
      const secondSlider = screen.getByRole('slider', { name: 'Slider thumb 2' })
      const thirdSlider = screen.getByRole('slider', { name: 'Slider thumb 3' })
      expect(firstSlider).toBeInTheDocument()
      expect(secondSlider).toBeInTheDocument()
      expect(thirdSlider).toBeInTheDocument()
    })
  })

  describe('Form Accessibility', () => {
    it('should associate labels with inputs', () => {
      render(
        <div>
          <label htmlFor="email-input">Email Address</label>
          <Input id="email-input" type="email" />
        </div>
      )
      const input = screen.getByLabelText('Email Address')
      expect(input).toBeInTheDocument()
    })

    it('should support fieldset and legend for grouped inputs', () => {
      render(
        <fieldset>
          <legend>Contact Information</legend>
          <Input placeholder="Name" aria-label="Name" />
          <Input placeholder="Email" aria-label="Email" />
        </fieldset>
      )
      const fieldset = screen.getByRole('group')
      expect(fieldset).toBeInTheDocument()
      expect(screen.getByText('Contact Information')).toBeInTheDocument()
    })
  })
})

describe('Screen Reader Compatibility', () => {
  describe('Hidden Content', () => {
    it('should support aria-hidden for decorative elements', () => {
      render(
        <div>
          <span aria-hidden="true">Decorative icon</span>
          <span>Visible text</span>
        </div>
      )
      const hidden = screen.getByText('Decorative icon')
      expect(hidden).toHaveAttribute('aria-hidden', 'true')
    })

    it('should support sr-only class for screen reader only content', () => {
      render(
        <div>
          <span className="sr-only">Screen reader only</span>
          <span>Visible</span>
        </div>
      )
      const srOnly = screen.getByText('Screen reader only')
      expect(srOnly).toHaveClass('sr-only')
    })
  })
})
