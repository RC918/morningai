import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, act } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key
  })
}))

vi.mock('@/lib/spring-animation', () => ({
  triggerHaptic: vi.fn()
}))

vi.mock('framer-motion', () => {
  const React = require('react')
  return {
    motion: {
      div: React.forwardRef((props: any, ref: any) => {
        const { children, onClick, onDragEnd, drag, dragConstraints, dragElastic, initial, animate, exit, transition, style, layout, ...rest } = props
        return React.createElement('div', { ref, onClick, style, ...rest }, children)
      }),
      button: React.forwardRef((props: any, ref: any) => {
        const { children, whileHover, whileTap, ...rest } = props
        return React.createElement('button', { ref, ...rest }, children)
      })
    },
    AnimatePresence: ({ children }: any) => children,
    useMotionValue: () => ({ get: () => 0, set: vi.fn() }),
    useTransform: () => ({ get: () => 1 })
  }
})

import { AppleModalProvider, useAppleModal } from './apple-modal'

describe('AppleModal', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('AppleModalProvider', () => {
    it('renders children without crashing', () => {
      render(
        <AppleModalProvider>
          <div>Test Content</div>
        </AppleModalProvider>
      )
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('provides modal context to children', () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return <button onClick={() => modal.openModal({ title: 'Test' })}>Open Modal</button>
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      expect(screen.getByText('Open Modal')).toBeInTheDocument()
    })

    it('throws error when useAppleModal is used outside provider', () => {
      const TestComponent = () => {
        useAppleModal()
        return <div>Test</div>
      }

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => render(<TestComponent />)).toThrow(
        'useAppleModal must be used within AppleModalProvider'
      )

      consoleSpy.mockRestore()
    })
  })

  describe('Modal Display', () => {
    it('opens modal with title and description', async () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <button onClick={() => modal.openModal({
            title: 'Test Modal',
            description: 'Test Description',
            children: <div>Modal Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      const button = screen.getByText('Open')
      await userEvent.click(button)

      expect(screen.getByText('Test Modal')).toBeInTheDocument()
      expect(screen.getByText('Test Description')).toBeInTheDocument()
      expect(screen.getByText('Modal Content')).toBeInTheDocument()
    })

    it('shows close button by default', async () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <button onClick={() => modal.openModal({
            title: 'Test',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      expect(screen.getByLabelText('Close modal')).toBeInTheDocument()
    })

    it('hides close button when showClose is false', async () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <button onClick={() => modal.openModal({
            title: 'Test',
            showClose: false,
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      expect(screen.queryByLabelText('Close modal')).not.toBeInTheDocument()
    })
  })

  describe('Modal Dismissal', () => {
    it('closes modal when close button is clicked', async () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <button onClick={() => modal.openModal({
            title: 'Test Modal',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      await userEvent.click(screen.getByText('Open'))
      expect(screen.getByText('Test Modal')).toBeInTheDocument()

      const closeButton = screen.getByLabelText('Close modal')
      await userEvent.click(closeButton)

      expect(screen.queryByText('Test Modal')).not.toBeInTheDocument()
    })

    it('closes all modals when closeAll is called', async () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <>
            <button onClick={() => {
              modal.openModal({ title: 'Modal 1', children: <div>Content 1</div> })
              modal.openModal({ title: 'Modal 2', children: <div>Content 2</div> })
            }}
            >
              Open Multiple
            </button>
            <button onClick={() => modal.closeAll()}>
              Close All
            </button>
          </>
        )
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      await userEvent.click(screen.getByText('Open Multiple'))
      expect(screen.getByText('Modal 1')).toBeInTheDocument()
      expect(screen.getByText('Modal 2')).toBeInTheDocument()

      await userEvent.click(screen.getByText('Close All'))
      expect(screen.queryByText('Modal 1')).not.toBeInTheDocument()
      expect(screen.queryByText('Modal 2')).not.toBeInTheDocument()
    })
  })

  describe('Modal Sizes', () => {
    it('applies correct size class', async () => {
      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <button onClick={() => modal.openModal({
            title: 'Large Modal',
            size: 'lg',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      const { container } = render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      const modalContent = container.querySelector('.max-w-lg')
      expect(modalContent).toBeInTheDocument()
    })
  })

  describe('Modal Return Value', () => {
    it('returns modal object with close function', async () => {
      let modalInstance: any

      const TestComponent = () => {
        const modal = useAppleModal()
        return (
          <button onClick={() => {
            modalInstance = modal.openModal({
              title: 'Test Modal',
              children: <div>Content</div>
            })
          }}
          >
            Open
          </button>
        )
      }

      render(
        <AppleModalProvider>
          <TestComponent />
        </AppleModalProvider>
      )

      await userEvent.click(screen.getByText('Open'))
      expect(screen.getByText('Test Modal')).toBeInTheDocument()

      expect(modalInstance).toBeDefined()
      expect(modalInstance.id).toBeDefined()
      expect(typeof modalInstance.close).toBe('function')

      act(() => { modalInstance.close() })
      expect(screen.queryByText('Test Modal')).not.toBeInTheDocument()
    })
  })
})
