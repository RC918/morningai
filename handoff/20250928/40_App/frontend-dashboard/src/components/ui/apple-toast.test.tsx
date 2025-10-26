import { describe, it, expect, vi } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

// Mock framer-motion before importing the component
vi.mock('framer-motion', () => {
  const React = require('react')
  return {
    motion: {
      div: React.forwardRef((props: any, ref: any) => {
        const { children, onDragEnd, drag, dragConstraints, dragElastic, initial, animate, exit, transition, layout, ...rest } = props
        return React.createElement('div', { ref, ...rest }, children)
      }),
      button: React.forwardRef((props: any, ref: any) => {
        const { children, whileHover, whileTap, ...rest } = props
        return React.createElement('button', { ref, ...rest }, children)
      })
    },
    AnimatePresence: ({ children }: any) => children
  }
})

import { AppleToastProvider, useAppleToast } from './apple-toast'

describe('AppleToast', () => {
  describe('AppleToastProvider', () => {
    it('renders children without crashing', () => {
      render(
        <AppleToastProvider>
          <div>Test Content</div>
        </AppleToastProvider>
      )
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('provides toast context to children', () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return <button onClick={() => toast.success('Test')}>Show Toast</button>
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      expect(screen.getByText('Show Toast')).toBeInTheDocument()
    })

    it('throws error when useAppleToast is used outside provider', () => {
      const TestComponent = () => {
        useAppleToast()
        return <div>Test</div>
      }

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => render(<TestComponent />)).toThrow(
        'useAppleToast must be used within AppleToastProvider'
      )

      consoleSpy.mockRestore()
    })
  })

  describe('Toast Display', () => {
    it('shows success toast', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.success('Success!', 'Operation completed')}>
            Show Success
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Success')
      await userEvent.click(button)

      expect(screen.getByText('Success!')).toBeInTheDocument()
      expect(screen.getByText('Operation completed')).toBeInTheDocument()
    })

    it('shows error toast', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.error('Error!', 'Something went wrong')}>
            Show Error
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Error')
      await userEvent.click(button)

      expect(screen.getByText('Error!')).toBeInTheDocument()
      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('shows warning toast', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.warning('Warning!', 'Be careful')}>
            Show Warning
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Warning')
      await userEvent.click(button)

      expect(screen.getByText('Warning!')).toBeInTheDocument()
      expect(screen.getByText('Be careful')).toBeInTheDocument()
    })

    it('shows info toast', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.info('Info', 'New features available')}>
            Show Info
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Info')
      await userEvent.click(button)

      expect(screen.getByText('Info')).toBeInTheDocument()
      expect(screen.getByText('New features available')).toBeInTheDocument()
    })

    it('shows toast with only title', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.toast('Simple message')}>
            Show Simple Toast
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Simple Toast')
      await userEvent.click(button)

      expect(screen.getByText('Simple message')).toBeInTheDocument()
    })
  })

  describe('Toast Dismissal', () => {
    it('dismisses toast when close button is clicked', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.success('Dismissible', 'Click X to close')}>
            Show Toast
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Toast')
      await userEvent.click(button)

      expect(screen.getByText('Dismissible')).toBeInTheDocument()

      const closeButton = screen.getByLabelText('Close notification')
      await userEvent.click(closeButton)

      expect(screen.queryByText('Dismissible')).not.toBeInTheDocument()
    })

    it('dismisses all toasts when dismissAll is called', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <>
            <button onClick={() => {
              toast.success('Toast 1')
              toast.info('Toast 2')
              toast.warning('Toast 3')
            }}>
              Show Multiple Toasts
            </button>
            <button onClick={() => toast.dismissAll()}>
              Dismiss All
            </button>
          </>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const showButton = screen.getByText('Show Multiple Toasts')
      await userEvent.click(showButton)

      expect(screen.getByText('Toast 1')).toBeInTheDocument()
      expect(screen.getByText('Toast 2')).toBeInTheDocument()
      expect(screen.getByText('Toast 3')).toBeInTheDocument()

      const dismissButton = screen.getByText('Dismiss All')
      await userEvent.click(dismissButton)

      expect(screen.queryByText('Toast 1')).not.toBeInTheDocument()
      expect(screen.queryByText('Toast 2')).not.toBeInTheDocument()
      expect(screen.queryByText('Toast 3')).not.toBeInTheDocument()
    })
  })

  describe('Multiple Toasts', () => {
    it('displays multiple toasts simultaneously', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => {
            toast.success('First')
            toast.error('Second')
            toast.info('Third')
          }}>
            Show Multiple
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Multiple')
      await userEvent.click(button)

      expect(screen.getByText('First')).toBeInTheDocument()
      expect(screen.getByText('Second')).toBeInTheDocument()
      expect(screen.getByText('Third')).toBeInTheDocument()
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.success('Accessible Toast')}>
            Show Toast
          </button>
        )
      }

      const { container } = render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const liveRegion = container.querySelector('[aria-live="polite"]')
      expect(liveRegion).toBeInTheDocument()
      expect(liveRegion).toHaveAttribute('aria-atomic', 'false')
    })

    it('close button has accessible label', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.success('Test')}>
            Show Toast
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Toast')
      await userEvent.click(button)

      const closeButton = screen.getByLabelText('Close notification')
      expect(closeButton).toBeInTheDocument()
    })
  })

  describe('Toast Return Value', () => {
    it('returns toast object with dismiss function', async () => {
      let toastInstance: any

      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => {
            toastInstance = toast.success('Test Toast')
          }}>
            Show Toast
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Toast')
      await userEvent.click(button)

      expect(screen.getByText('Test Toast')).toBeInTheDocument()

      expect(toastInstance).toBeDefined()
      expect(toastInstance.id).toBeDefined()
      expect(typeof toastInstance.dismiss).toBe('function')

      act(() => { toastInstance.dismiss() })

      expect(screen.queryByText('Test Toast')).not.toBeInTheDocument()
    })
  })

  describe('Toast Variants', () => {
    it('supports custom toast options', async () => {
      const TestComponent = () => {
        const toast = useAppleToast()
        return (
          <button onClick={() => toast.toast({
            title: 'Custom Toast',
            description: 'Custom description',
            variant: 'info',
            duration: 0
          })}>
            Show Custom
          </button>
        )
      }

      render(
        <AppleToastProvider>
          <TestComponent />
        </AppleToastProvider>
      )

      const button = screen.getByText('Show Custom')
      await userEvent.click(button)

      expect(screen.getByText('Custom Toast')).toBeInTheDocument()
      expect(screen.getByText('Custom description')).toBeInTheDocument()
    })
  })
})
