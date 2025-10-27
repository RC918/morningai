import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppleActionSheet, ActionSheetAction } from './apple-action-sheet'
import React from 'react'

vi.mock('@/hooks/use-accessibility', () => ({
  useScreenReaderAnnouncement: () => vi.fn()
}))

const TestWrapper = ({ children }: { children: React.ReactNode }) => {
  return (
    <AppleActionSheet.Provider>
      {children}
    </AppleActionSheet.Provider>
  )
}

const TestComponent = () => {
  const { show, hide, isVisible } = AppleActionSheet.useActionSheet()

  return (
    <div>
      <div>Test Component</div>
      <div>Status: {isVisible ? 'visible' : 'hidden'}</div>
      <button onClick={() => show({
        title: 'Test Title',
        message: 'Test Message',
        actions: [
          {
            id: '1',
            label: 'Action 1',
            onSelect: () => console.log('Action 1')
          }
        ]
      })}
      >
        Show
      </button>
      <button onClick={hide}>Hide</button>
    </div>
  )
}

describe('AppleActionSheet', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Provider and Context', () => {
    it('provides action sheet context', () => {
      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      expect(screen.getByText('Test Component')).toBeInTheDocument()
      expect(screen.getByText('Status: hidden')).toBeInTheDocument()
    })

    it('throws error when used outside provider', () => {
      const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})
      
      expect(() => {
        render(<TestComponent />)
      }).toThrow('useAppleActionSheet must be used within AppleActionSheetProvider')

      consoleError.mockRestore()
    })
  })

  describe('Action Sheet Display', () => {
    it('shows action sheet when show is called', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      const showButton = screen.getByText('Show')
      await user.click(showButton)

      await waitFor(() => {
        expect(screen.getByText('Test Title')).toBeInTheDocument()
        expect(screen.getByText('Test Message')).toBeInTheDocument()
        expect(screen.getByText('Action 1')).toBeInTheDocument()
        expect(screen.getByText('Status: visible')).toBeInTheDocument()
      })
    })

    it('hides action sheet when hide is called', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      const showButton = screen.getByText('Show')
      await user.click(showButton)

      await waitFor(() => {
        expect(screen.getByText('Test Title')).toBeInTheDocument()
      })

      const hideButton = screen.getByText('Hide')
      await user.click(hideButton)

      await waitFor(() => {
        expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
        expect(screen.getByText('Status: hidden')).toBeInTheDocument()
      })
    })

    it('displays cancel button', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })
    })

    it('displays custom cancel label', async () => {
      const user = userEvent.setup()

      const CustomCancelComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [{ id: '1', label: 'Action', onSelect: () => {} }],
            cancelLabel: 'Go Back'
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <CustomCancelComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Go Back')).toBeInTheDocument()
      })
    })
  })

  describe('Actions', () => {
    it('calls onSelect when action is clicked', async () => {
      const user = userEvent.setup()
      const onSelect = vi.fn()

      const ActionComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [
              {
                id: '1',
                label: 'Test Action',
                onSelect
              }
            ]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <ActionComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Test Action')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Test Action'))

      expect(onSelect).toHaveBeenCalledTimes(1)
    })

    it('closes action sheet after action is selected', async () => {
      const user = userEvent.setup()

      const ActionComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [
              {
                id: '1',
                label: 'Test Action',
                onSelect: () => {}
              }
            ]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <ActionComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Test Action')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Test Action'))

      await waitFor(() => {
        expect(screen.queryByText('Test Action')).not.toBeInTheDocument()
      })
    })

    it('does not call onSelect for disabled actions', async () => {
      const user = userEvent.setup()
      const onSelect = vi.fn()

      const ActionComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [
              {
                id: '1',
                label: 'Disabled Action',
                disabled: true,
                onSelect
              }
            ]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <ActionComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Disabled Action')).toBeInTheDocument()
      })

      const disabledButton = screen.getByText('Disabled Action').closest('button')
      expect(disabledButton).toBeDisabled()

      if (disabledButton) {
        await user.click(disabledButton)
      }

      expect(onSelect).not.toHaveBeenCalled()
    })

    it('displays destructive actions with warning icon', async () => {
      const user = userEvent.setup()

      const ActionComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [
              {
                id: '1',
                label: 'Delete',
                destructive: true,
                onSelect: () => {}
              }
            ]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <ActionComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        const deleteButton = screen.getByText('Delete').closest('button')
        expect(deleteButton).toBeInTheDocument()
        expect(deleteButton).toHaveClass('text-red-600', 'dark:text-red-500')
      })
    })

    it('renders multiple actions', async () => {
      const user = userEvent.setup()

      const ActionComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [
              { id: '1', label: 'Action 1', onSelect: () => {} },
              { id: '2', label: 'Action 2', onSelect: () => {} },
              { id: '3', label: 'Action 3', onSelect: () => {} }
            ]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <ActionComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Action 1')).toBeInTheDocument()
        expect(screen.getByText('Action 2')).toBeInTheDocument()
        expect(screen.getByText('Action 3')).toBeInTheDocument()
      })
    })
  })

  describe('Cancel Button', () => {
    it('closes action sheet when cancel is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Test Title')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Cancel'))

      await waitFor(() => {
        expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
      })
    })

    it('calls onCancel when cancel is clicked', async () => {
      const user = userEvent.setup()
      const onCancel = vi.fn()

      const CancelComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [{ id: '1', label: 'Action', onSelect: () => {} }],
            onCancel
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <CancelComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Cancel')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Cancel'))

      expect(onCancel).toHaveBeenCalledTimes(1)
    })
  })

  describe('Backdrop', () => {
    it('closes action sheet when backdrop is clicked', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Test Title')).toBeInTheDocument()
      })

      const backdrop = screen.getByRole('dialog').parentElement
      if (backdrop) {
        await user.click(backdrop)
      }

      await waitFor(() => {
        expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
      })
    })
  })

  describe('Keyboard Navigation', () => {
    it('closes on Escape key', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Test Title')).toBeInTheDocument()
      })

      await user.keyboard('{Escape}')

      await waitFor(() => {
        expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
      })
    })

    it('focuses first action on open', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        const firstAction = screen.getByText('Action 1').closest('button')
        expect(firstAction).toHaveFocus()
      })
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        const dialog = screen.getByRole('dialog')
        expect(dialog).toHaveAttribute('aria-modal', 'true')
        expect(dialog).toHaveAttribute('aria-labelledby')
        expect(dialog).toHaveAttribute('aria-describedby')
      })
    })

    it('restores focus after closing', async () => {
      const user = userEvent.setup()

      render(
        <TestWrapper>
          <TestComponent />
        </TestWrapper>
      )

      const showButton = screen.getByText('Show')
      showButton.focus()
      expect(showButton).toHaveFocus()

      await user.click(showButton)

      await waitFor(() => {
        expect(screen.getByText('Test Title')).toBeInTheDocument()
      })

      await user.keyboard('{Escape}')

      await waitFor(() => {
        expect(screen.queryByText('Test Title')).not.toBeInTheDocument()
      })

      await waitFor(() => {
        expect(showButton).toHaveFocus()
      })
    })
  })

  describe('Optional Props', () => {
    it('renders without title', async () => {
      const user = userEvent.setup()

      const NoTitleComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            actions: [{ id: '1', label: 'Action', onSelect: () => {} }]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <NoTitleComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Action')).toBeInTheDocument()
        expect(screen.queryByRole('heading')).not.toBeInTheDocument()
      })
    })

    it('renders without message', async () => {
      const user = userEvent.setup()

      const NoMessageComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Title Only',
            actions: [{ id: '1', label: 'Action', onSelect: () => {} }]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <NoMessageComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByText('Title Only')).toBeInTheDocument()
        expect(screen.getByText('Action')).toBeInTheDocument()
      })
    })

    it('renders with icons', async () => {
      const user = userEvent.setup()

      const IconComponent = () => {
        const { show } = AppleActionSheet.useActionSheet()

        return (
          <button onClick={() => show({
            title: 'Test',
            actions: [
              {
                id: '1',
                label: 'Action with Icon',
                icon: <span data-testid="test-icon">📝</span>,
                onSelect: () => {}
              }
            ]
          })}
          >
            Show
          </button>
        )
      }

      render(
        <TestWrapper>
          <IconComponent />
        </TestWrapper>
      )

      await user.click(screen.getByText('Show'))

      await waitFor(() => {
        expect(screen.getByTestId('test-icon')).toBeInTheDocument()
      })
    })
  })
})
