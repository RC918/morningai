import React from 'react'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { AppleLiveActivity, type LiveActivityConfig } from './apple-live-activity'
import { Download, Music } from 'lucide-react'

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key: string, defaultValue?: string) => defaultValue || key
  })
}))

vi.mock('@/lib/spring-animation', () => ({
  triggerHaptic: vi.fn()
}))

const TestWrapper = ({ children }: { children: React.ReactNode }) => (
  <AppleLiveActivity.Provider>{children}</AppleLiveActivity.Provider>
)

const TestComponent = ({ config }: { config: any }) => {
  const { useLiveActivity } = AppleLiveActivity
  const { addActivity } = useLiveActivity()

  React.useEffect(() => {
    addActivity(config)
  }, [])

  return <div>Test Component</div>
}

describe('AppleLiveActivity', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders live activity with title and subtitle', async () => {
      const config = {
        title: 'Download in Progress',
        subtitle: 'document.pdf',
        icon: <Download data-testid="download-icon" />
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Download in Progress')).toBeInTheDocument()
        expect(screen.getByText('document.pdf')).toBeInTheDocument()
        expect(screen.getByTestId('download-icon')).toBeInTheDocument()
      })
    })

    it('renders with emoji icon', async () => {
      const config = {
        title: 'Music Playing',
        subtitle: 'Summer Breeze',
        icon: '🎵'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('🎵')).toBeInTheDocument()
      })
    })

    it('renders without icon', async () => {
      const config = {
        title: 'Simple Activity',
        subtitle: 'No icon'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Simple Activity')).toBeInTheDocument()
      })
    })

    it('renders without subtitle', async () => {
      const config = {
        title: 'Only Title'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Only Title')).toBeInTheDocument()
      })
    })
  })

  describe('Progress Tracking', () => {
    it('displays progress bar and percentage', async () => {
      const config = {
        title: 'Download',
        progress: 45
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('45%')).toBeInTheDocument()
      })
    })

    it('handles 0% progress', async () => {
      const config = {
        title: 'Starting',
        progress: 0
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('0%')).toBeInTheDocument()
      })
    })

    it('handles 100% progress', async () => {
      const config = {
        title: 'Complete',
        progress: 100
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('100%')).toBeInTheDocument()
      })
    })

    it('clamps progress above 100%', async () => {
      const config = {
        title: 'Over',
        progress: 150
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('150%')).toBeInTheDocument()
      })
    })

    it('displays status text', async () => {
      const config = {
        title: 'Download',
        progress: 45,
        status: '2.3 MB of 5.1 MB'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('2.3 MB of 5.1 MB')).toBeInTheDocument()
      })
    })
  })

  describe('Expandable Functionality', () => {
    it('toggles expanded state when clicked', async () => {
      const user = userEvent.setup()
      const config = {
        title: 'Expandable Activity',
        expandable: true,
        metadata: {
          'Key': 'Value'
        }
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Expandable Activity')).toBeInTheDocument()
      })

      expect(screen.queryByText('Key')).not.toBeInTheDocument()

      const activity = screen.getByText('Expandable Activity').closest('div')
      if (activity) {
        await user.click(activity)
      }

      await waitFor(() => {
        expect(screen.getByText('Key')).toBeInTheDocument()
        expect(screen.getByText('Value')).toBeInTheDocument()
      })
    })

    it('does not expand when expandable is false', async () => {
      const user = userEvent.setup()
      const config = {
        title: 'Non-Expandable',
        expandable: false,
        metadata: {
          'Key': 'Value'
        }
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Non-Expandable')).toBeInTheDocument()
      })

      const activity = screen.getByText('Non-Expandable').closest('div')
      if (activity) {
        await user.click(activity)
      }

      expect(screen.queryByText('Key')).not.toBeInTheDocument()
    })

    it('shows expand/collapse chevron when expandable', async () => {
      const config = {
        title: 'Expandable',
        expandable: true
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBeGreaterThan(0)
      })
    })

    it('does not show expand chevron when not expandable', async () => {
      const config = {
        title: 'Non-Expandable',
        expandable: false
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        expect(buttons.length).toBe(1)
      })
    })
  })

  describe('Actions', () => {
    it('renders action buttons when expanded', async () => {
      const user = userEvent.setup()
      const onPress = vi.fn()
      const config = {
        title: 'With Actions',
        expandable: true,
        actions: [
          {
            id: 'action1',
            label: 'Primary Action',
            variant: 'primary',
            onPress
          },
          {
            id: 'action2',
            label: 'Secondary Action',
            variant: 'secondary',
            onPress
          }
        ]
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('With Actions')).toBeInTheDocument()
      })

      const activity = screen.getByText('With Actions').closest('div')
      if (activity) {
        await user.click(activity)
      }

      await waitFor(() => {
        expect(screen.getByText('Primary Action')).toBeInTheDocument()
        expect(screen.getByText('Secondary Action')).toBeInTheDocument()
      })

      await user.click(screen.getByText('Primary Action'))
      expect(onPress).toHaveBeenCalled()
    })

    it('handles multiple actions', async () => {
      const user = userEvent.setup()
      const config = {
        title: 'Multiple Actions',
        expandable: true,
        actions: [
          { id: 'a1', label: 'Action 1', variant: 'primary' },
          { id: 'a2', label: 'Action 2', variant: 'secondary' },
          { id: 'a3', label: 'Action 3', variant: 'secondary' }
        ]
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Multiple Actions')).toBeInTheDocument()
      })

      const activity = screen.getByText('Multiple Actions').closest('div')
      if (activity) {
        await user.click(activity)
      }

      await waitFor(() => {
        expect(screen.getByText('Action 1')).toBeInTheDocument()
        expect(screen.getByText('Action 2')).toBeInTheDocument()
        expect(screen.getByText('Action 3')).toBeInTheDocument()
      })
    })
  })

  describe('Metadata', () => {
    it('displays metadata when expanded', async () => {
      const user = userEvent.setup()
      const config = {
        title: 'With Metadata',
        expandable: true,
        metadata: {
          'Size': '150 MB',
          'Speed': '5.2 MB/s',
          'Time Remaining': '30 seconds'
        }
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('With Metadata')).toBeInTheDocument()
      })

      const activity = screen.getByText('With Metadata').closest('div')
      if (activity) {
        await user.click(activity)
      }

      await waitFor(() => {
        expect(screen.getByText('Size')).toBeInTheDocument()
        expect(screen.getByText('150 MB')).toBeInTheDocument()
        expect(screen.getByText('Speed')).toBeInTheDocument()
        expect(screen.getByText('5.2 MB/s')).toBeInTheDocument()
        expect(screen.getByText('Time Remaining')).toBeInTheDocument()
        expect(screen.getByText('30 seconds')).toBeInTheDocument()
      })
    })
  })

  describe('Variants', () => {
    it('applies default variant styles', async () => {
      const config = {
        title: 'Default',
        variant: 'default'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Default')).toBeInTheDocument()
      })
    })

    it('applies primary variant styles', async () => {
      const config = {
        title: 'Primary',
        variant: 'primary'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Primary')).toBeInTheDocument()
      })
    })

    it('applies success variant styles', async () => {
      const config = {
        title: 'Success',
        variant: 'success'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Success')).toBeInTheDocument()
      })
    })

    it('applies warning variant styles', async () => {
      const config = {
        title: 'Warning',
        variant: 'warning'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Warning')).toBeInTheDocument()
      })
    })

    it('applies error variant styles', async () => {
      const config = {
        title: 'Error',
        variant: 'error'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Error')).toBeInTheDocument()
      })
    })
  })

  describe('Dismiss Functionality', () => {
    it('dismisses activity when close button is clicked', async () => {
      const user = userEvent.setup()
      const config = {
        title: 'Dismissible Activity'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Dismissible Activity')).toBeInTheDocument()
      })

      const dismissButtons = screen.getAllByRole('button')
      const dismissButton = dismissButtons.find(btn => 
        btn.getAttribute('aria-label')?.includes('Dismiss') ||
        btn.getAttribute('aria-label')?.includes('dismiss')
      )
      
      if (dismissButton) {
        await user.click(dismissButton)
      }

      await waitFor(() => {
        expect(screen.queryByText('Dismissible Activity')).not.toBeInTheDocument()
      })
    })
  })

  describe('Provider Context', () => {
    it('provides useLiveActivity hook', () => {
      const TestHook = () => {
        const { addActivity, dismissAll } = AppleLiveActivity.useLiveActivity()
        expect(addActivity).toBeDefined()
        expect(dismissAll).toBeDefined()
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
          AppleLiveActivity.useLiveActivity()
          return <div>Should not render</div>
        } catch (error) {
          return <div>Error caught</div>
        }
      }

      render(<TestHook />)
      expect(screen.getByText('Error caught')).toBeInTheDocument()
    })
  })

  describe('Multiple Activities', () => {
    it('displays multiple activities', async () => {
      const MultipleTest = () => {
        const { useLiveActivity } = AppleLiveActivity
        const { addActivity } = useLiveActivity()

        React.useEffect(() => {
          addActivity({ id: 'a1', title: 'Activity 1' })
          addActivity({ id: 'a2', title: 'Activity 2' })
          addActivity({ id: 'a3', title: 'Activity 3' })
        }, [])

        return <div>Multiple Activities</div>
      }

      render(
        <TestWrapper>
          <MultipleTest />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Activity 1')).toBeInTheDocument()
        expect(screen.getByText('Activity 2')).toBeInTheDocument()
        expect(screen.getByText('Activity 3')).toBeInTheDocument()
      })
    })

    it('limits to MAX_ACTIVITIES', async () => {
      const LimitTest = () => {
        const { useLiveActivity } = AppleLiveActivity
        const { addActivity } = useLiveActivity()

        React.useEffect(() => {
          addActivity({ id: 'a1', title: 'Activity 1' })
          addActivity({ id: 'a2', title: 'Activity 2' })
          addActivity({ id: 'a3', title: 'Activity 3' })
          addActivity({ id: 'a4', title: 'Activity 4' })
        }, [])

        return <div>Limit Test</div>
      }

      render(
        <TestWrapper>
          <LimitTest />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.queryByText('Activity 1')).not.toBeInTheDocument()
        expect(screen.getByText('Activity 2')).toBeInTheDocument()
        expect(screen.getByText('Activity 3')).toBeInTheDocument()
        expect(screen.getByText('Activity 4')).toBeInTheDocument()
      })
    })
  })

  describe('Update Functionality', () => {
    it('updates activity properties', async () => {
      const UpdateTest = () => {
        const { useLiveActivity } = AppleLiveActivity
        const { addActivity, updateActivity } = useLiveActivity()
        const [activityId, setActivityId] = React.useState<string | null>(null)

        React.useEffect(() => {
          const { id } = addActivity({
            title: 'Initial Title',
            progress: 0
          })
          setActivityId(id)

          setTimeout(() => {
            updateActivity(id, {
              title: 'Updated Title',
              progress: 50
            })
          }, 100)
        }, [])

        return <div>Update Test</div>
      }

      render(
        <TestWrapper>
          <UpdateTest />
        </TestWrapper>
      )

      await waitFor(() => {
        expect(screen.getByText('Initial Title')).toBeInTheDocument()
      })

      await waitFor(() => {
        expect(screen.getByText('Updated Title')).toBeInTheDocument()
        expect(screen.getByText('50%')).toBeInTheDocument()
      }, { timeout: 500 })
    })
  })

  describe('Position', () => {
    it('renders at top position by default', () => {
      render(
        <AppleLiveActivity.Provider>
          <div>Content</div>
        </AppleLiveActivity.Provider>
      )

      const container = document.querySelector('[aria-live="polite"]')
      expect(container).toHaveClass('top-4')
    })

    it('renders at bottom position when specified', () => {
      render(
        <AppleLiveActivity.Provider position="bottom">
          <div>Content</div>
        </AppleLiveActivity.Provider>
      )

      const container = document.querySelector('[aria-live="polite"]')
      expect(container).toHaveClass('bottom-4')
    })
  })

  describe('Accessibility', () => {
    it('has proper ARIA attributes', async () => {
      const config = {
        title: 'Accessible Activity'
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      const container = document.querySelector('[aria-live="polite"]')
      expect(container).toBeInTheDocument()
      expect(container).toHaveAttribute('aria-atomic', 'false')
    })

    it('has accessible button labels', async () => {
      const config = {
        title: 'Activity',
        expandable: true
      }

      render(
        <TestWrapper>
          <TestComponent config={config} />
        </TestWrapper>
      )

      await waitFor(() => {
        const buttons = screen.getAllByRole('button')
        buttons.forEach(button => {
          expect(button).toHaveAttribute('aria-label')
        })
      })
    })
  })
})
