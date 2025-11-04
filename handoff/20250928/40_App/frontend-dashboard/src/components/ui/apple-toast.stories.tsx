import type { Meta, StoryObj } from '@storybook/react'
import { AppleToastProvider, useAppleToast } from './apple-toast'
import { AppleButton } from './apple-button'

const meta = {
  title: 'UI/AppleToast',
  component: AppleToastProvider,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'iOS-style toast notification system with Dynamic Island design, spring animations, and gesture support.'
      }
    }
  },
  tags: ['autodocs'],
  args: {
    children: null
  },
  argTypes: {
    children: { control: false }
  }
} satisfies Meta<typeof AppleToastProvider>

export default meta
type Story = StoryObj<typeof meta>

const ToastDemo = () => {
  const toast = useAppleToast()

  return (
    <div className="flex flex-col gap-4 p-8">
      <h2 className="text-2xl font-bold mb-4">Apple Dynamic Toast System</h2>
      
      <div className="grid grid-cols-2 gap-3">
        <AppleButton
          onClick={() => toast.success('Success!', 'Your changes have been saved successfully.')}
        >
          Show Success Toast
        </AppleButton>

        <AppleButton
          onClick={() => toast.error('Error!', 'Something went wrong. Please try again.')}
          variant="destructive"
        >
          Show Error Toast
        </AppleButton>

        <AppleButton
          onClick={() => toast.warning('Warning!', 'This action cannot be undone.')}
        >
          Show Warning Toast
        </AppleButton>

        <AppleButton
          onClick={() => toast.info('Info', 'New features are now available.')}
          variant="outline"
        >
          Show Info Toast
        </AppleButton>

        <AppleButton
          onClick={() => toast.toast({ title: 'Custom Toast', description: 'This is a custom toast message.' })}
          variant="ghost"
        >
          Show Default Toast
        </AppleButton>

        <AppleButton
          onClick={() => {
            toast.success('Multiple Toasts', 'You can show multiple toasts at once.')
            setTimeout(() => toast.info('Second Toast', 'This is the second toast.'), 500)
            setTimeout(() => toast.warning('Third Toast', 'This is the third toast.'), 1000)
          }}
        >
          Show Multiple Toasts
        </AppleButton>

        <AppleButton
          onClick={() => toast.toast({ 
            title: 'Persistent Toast', 
            description: 'This toast will not auto-dismiss.',
            duration: 0 
          })}
          variant="outline"
        >
          Show Persistent Toast
        </AppleButton>

        <AppleButton
          onClick={() => toast.dismissAll()}
          variant="destructive"
        >
          Dismiss All Toasts
        </AppleButton>
      </div>

      <div className="mt-8 p-4 bg-muted rounded-lg">
        <h3 className="font-semibold mb-2">Features:</h3>
        <ul className="text-sm space-y-1 list-disc list-inside">
          <li>Dynamic Island-inspired pill shape design</li>
          <li>Spring-based animations for natural feel</li>
          <li>Drag to dismiss gesture support</li>
          <li>Multiple toast variants (success, error, warning, info)</li>
          <li>Auto-dismiss with configurable duration</li>
          <li>Backdrop blur effect for iOS-style material</li>
          <li>Accessible with ARIA live regions</li>
          <li>Stacked layout for multiple toasts</li>
        </ul>
      </div>
    </div>
  )
}

export const Default: Story = {
  args: {},
  render: () => (
    <AppleToastProvider>
      <ToastDemo />
    </AppleToastProvider>
  )
}

export const SuccessToast: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <AppleButton onClick={() => toast.success('Success!', 'Your changes have been saved.')}>
          Show Success Toast
        </AppleButton>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const ErrorToast: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <AppleButton 
          onClick={() => toast.error('Error!', 'Failed to save changes.')}
          variant="destructive"
        >
          Show Error Toast
        </AppleButton>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const WarningToast: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <AppleButton onClick={() => toast.warning('Warning!', 'This action cannot be undone.')}>
          Show Warning Toast
        </AppleButton>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const InfoToast: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <AppleButton 
          onClick={() => toast.info('Info', 'New features are available.')}
          variant="outline"
        >
          Show Info Toast
        </AppleButton>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const LongContent: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <AppleButton onClick={() => toast.info(
          'Long Content Toast',
          'This is a toast with a much longer description to demonstrate how the component handles multi-line content. The text should wrap naturally and maintain readability.'
        )}>
          Show Long Content Toast
        </AppleButton>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const PersistentToast: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <div className="flex gap-3">
          <AppleButton onClick={() => toast.toast({
            title: 'Persistent Toast',
            description: 'This toast will not auto-dismiss. Click the X to close.',
            duration: 0
          })}>
            Show Persistent Toast
          </AppleButton>
          <AppleButton onClick={() => toast.dismissAll()} variant="outline">
            Dismiss All
          </AppleButton>
        </div>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const MultipleToasts: Story = {
  args: {},
  render: () => {
    const ToastTrigger = () => {
      const toast = useAppleToast()
      return (
        <AppleButton onClick={() => {
          toast.success('First Toast', 'This is the first toast.')
          setTimeout(() => toast.info('Second Toast', 'This is the second toast.'), 300)
          setTimeout(() => toast.warning('Third Toast', 'This is the third toast.'), 600)
          setTimeout(() => toast.error('Fourth Toast', 'This is the fourth toast.'), 900)
        }}>
          Show Multiple Toasts
        </AppleButton>
      )
    }

    return (
      <AppleToastProvider>
        <ToastTrigger />
      </AppleToastProvider>
    )
  }
}

export const DarkMode: Story = {
  args: {},
  render: () => (
    <div className="dark">
      <AppleToastProvider>
        <ToastDemo />
      </AppleToastProvider>
    </div>
  ),
  parameters: {
    backgrounds: { default: 'dark' }
  }
}
