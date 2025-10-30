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

import { AppleSheetProvider, useAppleSheet } from './apple-sheet'

describe('AppleSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('AppleSheetProvider', () => {
    it('renders children without crashing', () => {
      render(
        <AppleSheetProvider>
          <div>Test Content</div>
        </AppleSheetProvider>
      )
      expect(screen.getByText('Test Content')).toBeInTheDocument()
    })

    it('provides sheet context to children', () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return <button onClick={() => sheet.openSheet({ title: 'Test', children: <div>Test Content</div> })}>Open Sheet</button>
      }

      render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      expect(screen.getByText('Open Sheet')).toBeInTheDocument()
    })

    it('throws error when useAppleSheet is used outside provider', () => {
      const TestComponent = () => {
        useAppleSheet()
        return <div>Test</div>
      }

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

      expect(() => render(<TestComponent />)).toThrow(
        'useAppleSheet must be used within AppleSheetProvider'
      )

      consoleSpy.mockRestore()
    })
  })

  describe('Sheet Display', () => {
    it('opens sheet with title and description', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => sheet.openSheet({
            title: 'Test Sheet',
            description: 'Test Description',
            children: <div>Sheet Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      const button = screen.getByText('Open')
      await userEvent.click(button)

      expect(screen.getByText('Test Sheet')).toBeInTheDocument()
      expect(screen.getByText('Test Description')).toBeInTheDocument()
      expect(screen.getByText('Sheet Content')).toBeInTheDocument()
    })

    it('shows drag handle by default', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => sheet.openSheet({
            title: 'Test',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      const { container } = render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      const handle = container.querySelector('.w-10.h-1')
      expect(handle).toBeInTheDocument()
    })

    it('hides drag handle when showHandle is false', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => sheet.openSheet({
            title: 'Test',
            showHandle: false,
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      const { container } = render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      const handle = container.querySelector('.w-10.h-1')
      expect(handle).not.toBeInTheDocument()
    })

    it('shows close button by default', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => sheet.openSheet({
            title: 'Test',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      expect(screen.getByLabelText('Close sheet')).toBeInTheDocument()
    })
  })

  describe('Sheet Dismissal', () => {
    it('closes sheet when close button is clicked', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => sheet.openSheet({
            title: 'Test Sheet',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open'))
      expect(screen.getByText('Test Sheet')).toBeInTheDocument()

      const closeButton = screen.getByLabelText('Close sheet')
      await userEvent.click(closeButton)

      expect(screen.queryByText('Test Sheet')).not.toBeInTheDocument()
    })

    it('closes all sheets when closeAll is called', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <>
            <button onClick={() => {
              sheet.openSheet({ title: 'Sheet 1', children: <div>Content 1</div> })
              sheet.openSheet({ title: 'Sheet 2', children: <div>Content 2</div> })
            }}
            >
              Open Multiple
            </button>
            <button onClick={() => sheet.closeAll()}>
              Close All
            </button>
          </>
        )
      }

      render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open Multiple'))
      expect(screen.getByText('Sheet 1')).toBeInTheDocument()
      expect(screen.getByText('Sheet 2')).toBeInTheDocument()

      await userEvent.click(screen.getByText('Close All'))
      expect(screen.queryByText('Sheet 1')).not.toBeInTheDocument()
      expect(screen.queryByText('Sheet 2')).not.toBeInTheDocument()
    })
  })

  describe('Sheet Sizes', () => {
    it('applies correct size class', async () => {
      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => sheet.openSheet({
            title: 'Large Sheet',
            size: 'lg',
            children: <div>Content</div>
          })}
          >
            Open
          </button>
        )
      }

      const { container } = render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open'))

      const sheetContent = container.querySelector('.max-h-\\[80vh\\]')
      expect(sheetContent).toBeInTheDocument()
    })
  })

  describe('Sheet Return Value', () => {
    it('returns sheet object with close function', async () => {
      let sheetInstance: any

      const TestComponent = () => {
        const sheet = useAppleSheet()
        return (
          <button onClick={() => {
            sheetInstance = sheet.openSheet({
              title: 'Test Sheet',
              children: <div>Content</div>
            })
          }}
          >
            Open
          </button>
        )
      }

      render(
        <AppleSheetProvider>
          <TestComponent />
        </AppleSheetProvider>
      )

      await userEvent.click(screen.getByText('Open'))
      expect(screen.getByText('Test Sheet')).toBeInTheDocument()

      expect(sheetInstance).toBeDefined()
      expect(sheetInstance.id).toBeDefined()
      expect(typeof sheetInstance.close).toBe('function')

      act(() => { sheetInstance.close() })
      expect(screen.queryByText('Test Sheet')).not.toBeInTheDocument()
    })
  })
})
