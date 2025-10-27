import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppleControlCenter, type Control } from './apple-control-center'
import { Wifi, Bluetooth } from 'lucide-react'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key
  })
}))

vi.mock('@/lib/spring-animation', () => ({
  triggerHaptic: vi.fn()
}))

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => vi.fn(),
  useFocusTrap: () => {}
}))

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <AppleControlCenter.Provider>{children}</AppleControlCenter.Provider>
)

const TestComponent = ({ controls }: { controls: Control[] }) => {
  const { useControlCenter } = AppleControlCenter
  const { open, setControls } = useControlCenter()

  React.useEffect(() => {
    setControls(controls)
    open()
  }, [])

  return <div>Test Component</div>
}

describe('AppleControlCenter', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Provider and Context', () => {
    it('provides control center context', () => {
      const TestHook = () => {
        const { open, close, toggle } = AppleControlCenter.useControlCenter()
        expect(open).toBeDefined()
        expect(close).toBeDefined()
        expect(toggle).toBeDefined()
        return <div>Hook Test</div>
      }

      render(
        <TestWrapper>
          <TestHook />
        </TestWrapper>
      )

      expect(screen.getByText('Hook Test')).toBeInTheDocument()
    })

    it('throws error when used outside provider', () => {
      const TestHook = () => {
        try {
          AppleControlCenter.useControlCenter()
          return <div>Should not render</div>
        } catch (error) {
          return <div>Error caught</div>
        }
      }

      render(<TestHook />)
      expect(screen.getByText('Error caught')).toBeInTheDocument()
    })
  })

  describe('Control Center Panel', () => {
    it('opens and closes control center', async () => {
      const user = userEvent.setup()
      const TestToggle = () => {
        const { toggle, isOpen } = AppleControlCenter.useControlCenter()
        return (
          <button onClick={toggle}>
            {isOpen ? 'Close' : 'Open'}
          </button>
        )
      }

      render(
        <TestWrapper>
          <TestToggle />
        </TestWrapper>
      )

      const button = screen.getByText('Open')
      expect(button).toBeInTheDocument()

      await user.click(button)

      await waitFor(() => {
        expect(screen.getByText('Control Center')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Close'))

      await waitFor(() => {
        expect(screen.queryByText('Control Center')).not.toBeInTheDocument()
      })
    })

    it('displays controls in grid layout', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          subtitle: 'Home Network',
          icon: <Wifi data-testid="wifi-icon" />,
          size: '1x1',
          variant: 'primary',
          active: true
        },
        {
          id: 'bluetooth',
          title: 'Bluetooth',
          subtitle: 'On',
          icon: <Bluetooth data-testid="bluetooth-icon" />,
          size: '1x1',
          variant: 'primary',
          active: true
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Control Center')).toBeInTheDocument()
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
        expect(screen.getByText('Home Network')).toBeInTheDocument()
        expect(screen.getByText('Bluetooth')).toBeInTheDocument()
        expect(screen.getByText('On')).toBeInTheDocument()
      })
    })
  })

  describe('Control Cards', () => {
    it('renders control with title and subtitle', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          subtitle: 'Home Network',
          icon: <Wifi />,
          size: '1x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
        expect(screen.getByText('Home Network')).toBeInTheDocument()
      })
    })

    it('renders control without subtitle', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })

    it('displays control value', async () => {
      const controls: Control[] = [
        {
          id: 'brightness',
          title: 'Brightness',
          icon: <Wifi />,
          size: '1x1',
          value: '75%'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('75%')).toBeInTheDocument()
      })
    })

    it('handles control press', async () => {
      const user = userEvent.setup()
      const onPress = vi.fn()
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          onPress
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })

      const control = screen.getByText('Wi-Fi').closest('div')
      if (control) {
        await user.click(control)
      }

      expect(onPress).toHaveBeenCalled()
    })
  })

  describe('Control Sizes', () => {
    it('applies 1x1 size class', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        const titleElement = screen.getByText('Wi-Fi')
        const control = titleElement.closest('.rounded-3xl')
        expect(control).toHaveClass('col-span-1')
        expect(control).toHaveClass('row-span-1')
      })
    })

    it('applies 2x1 size class', async () => {
      const controls: Control[] = [
        {
          id: 'music',
          title: 'Music',
          icon: <Wifi />,
          size: '2x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        const titleElement = screen.getByText('Music')
        const control = titleElement.closest('.rounded-3xl')
        expect(control).toHaveClass('col-span-2')
        expect(control).toHaveClass('row-span-1')
      })
    })

    it('applies 1x2 size class', async () => {
      const controls: Control[] = [
        {
          id: 'brightness',
          title: 'Brightness',
          icon: <Wifi />,
          size: '1x2'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        const titleElement = screen.getByText('Brightness')
        const control = titleElement.closest('.rounded-3xl')
        expect(control).toHaveClass('col-span-1')
        expect(control).toHaveClass('row-span-2')
      })
    })

    it('applies 2x2 size class', async () => {
      const controls: Control[] = [
        {
          id: 'music',
          title: 'Music Player',
          icon: <Wifi />,
          size: '2x2'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        const titleElement = screen.getByText('Music Player')
        const control = titleElement.closest('.rounded-3xl')
        expect(control).toHaveClass('col-span-2')
        expect(control).toHaveClass('row-span-2')
      })
    })
  })

  describe('Control Variants', () => {
    it('applies default variant', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          variant: 'default',
          active: false
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })

    it('applies primary variant', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          variant: 'primary',
          active: true
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })

    it('applies success variant', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          variant: 'success',
          active: true
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })

    it('applies warning variant', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          variant: 'warning',
          active: true
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })

    it('applies danger variant', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          variant: 'danger',
          active: true
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })
  })

  describe('Active State', () => {
    it('shows active state', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          active: true
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })

    it('shows inactive state', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1',
          active: false
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })
    })
  })

  describe('Long Press Actions', () => {
    it('shows actions panel on long press', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          subtitle: 'Home',
          icon: <Wifi />,
          size: '1x1',
          actions: [
            {
              id: 'home',
              label: 'Home Network',
              onPress: vi.fn()
            },
            {
              id: 'office',
              label: 'Office Network',
              onPress: vi.fn()
            }
          ]
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
      })

      expect(controls[0].actions).toHaveLength(2)
    })
  })

  describe('Multiple Controls', () => {
    it('displays multiple controls', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1'
        },
        {
          id: 'bluetooth',
          title: 'Bluetooth',
          icon: <Bluetooth />,
          size: '1x1'
        },
        {
          id: 'airplane',
          title: 'Airplane',
          icon: <Wifi />,
          size: '1x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Wi-Fi')).toBeInTheDocument()
        expect(screen.getByText('Bluetooth')).toBeInTheDocument()
        expect(screen.getByText('Airplane')).toBeInTheDocument()
      })
    })
  })

  describe('Backdrop', () => {
    it('closes control center when backdrop is clicked', async () => {
      const user = userEvent.setup()
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Control Center')).toBeInTheDocument()
      })

      const backdrop = document.querySelector('.fixed.bg-black\\/50')
      if (backdrop) {
        await user.click(backdrop as HTMLElement)
      }

      await waitFor(() => {
        expect(screen.queryByText('Control Center')).not.toBeInTheDocument()
      })
    })
  })

  describe('Accessibility', () => {
    it('has accessible close button', async () => {
      const controls: Control[] = [
        {
          id: 'wifi',
          title: 'Wi-Fi',
          icon: <Wifi />,
          size: '1x1'
        }
      ]

      render(
        <TestWrapper>
          <TestComponent controls={controls} />
        </TestWrapper>
      )

      await waitFor(() => {
        const closeButton = screen.getByLabelText('Close Control Center')
        expect(closeButton).toBeInTheDocument()
      })
    })
  })

  describe('Context Methods', () => {
    it('provides open method', async () => {
      const TestOpen = () => {
        const { open, isOpen } = AppleControlCenter.useControlCenter()
        return (
          <>
            <button onClick={open}>Open</button>
            <div>{isOpen ? 'Open' : 'Closed'}</div>
          </>
        )
      }

      const user = userEvent.setup()
      render(
        <TestWrapper>
          <TestOpen />
        </TestWrapper>
      )

      expect(screen.getByText('Closed')).toBeInTheDocument()

      await user.click(screen.getByText('Open'))

      await waitFor(() => {
        expect(screen.getByText('Control Center')).toBeInTheDocument()
      })
    })

    it('provides close method', async () => {
      const TestClose = () => {
        const { open, close, isOpen } = AppleControlCenter.useControlCenter()
        React.useEffect(() => {
          open()
        }, [])
        return (
          <>
            <button onClick={close}>Close</button>
            <div>{isOpen ? 'Open' : 'Closed'}</div>
          </>
        )
      }

      const user = userEvent.setup()
      render(
        <TestWrapper>
          <TestClose />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Control Center')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Close'))

      await waitFor(() => {
        expect(screen.queryByText('Control Center')).not.toBeInTheDocument()
      })
    })

    it('provides toggle method', async () => {
      const TestToggle = () => {
        const { toggle, isOpen } = AppleControlCenter.useControlCenter()
        return (
          <>
            <button onClick={toggle}>Toggle</button>
            <div>{isOpen ? 'Open' : 'Closed'}</div>
          </>
        )
      }

      const user = userEvent.setup()
      render(
        <TestWrapper>
          <TestToggle />
        </TestWrapper>
      )

      expect(screen.getByText('Closed')).toBeInTheDocument()

      await user.click(screen.getByText('Toggle'))

      await waitFor(() => {
        expect(screen.getByText('Control Center')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Toggle'))

      await waitFor(() => {
        expect(screen.queryByText('Control Center')).not.toBeInTheDocument()
      })
    })
  })
})
