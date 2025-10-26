import type { Meta, StoryObj } from '@storybook/react'
import { AppleModalProvider, useAppleModal } from './apple-modal'
import { AppleButton } from './apple-button'

const meta: Meta<typeof AppleModalProvider> = {
  title: 'UI/AppleModal',
  component: AppleModalProvider,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof AppleModalProvider>

const ModalDemo = ({ size = 'md', showClose = true }) => {
  const modal = useAppleModal()

  const handleOpen = () => {
    modal.openModal({
      title: 'Welcome to Apple Modal',
      description: 'This is an iOS-style modal dialog with spring animations',
      size,
      showClose,
      children: (
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            This modal features:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
            <li>Spring-based animations (stiffness: 500, damping: 30)</li>
            <li>Backdrop blur effect</li>
            <li>Rounded corners (iOS style)</li>
            <li>Haptic feedback on close</li>
            <li>Escape key support</li>
            <li>Click outside to close</li>
          </ul>
          <div className="flex gap-2 pt-4">
            <AppleButton onClick={() => modal.closeAll()}>
              Close
            </AppleButton>
            <AppleButton variant="secondary" onClick={() => modal.openModal({
              title: 'Nested Modal',
              children: <p>This is a nested modal!</p>
            })}>
              Open Nested
            </AppleButton>
          </div>
        </div>
      )
    })
  }

  return (
    <div className="p-8">
      <AppleButton onClick={handleOpen}>
        Open Modal
      </AppleButton>
    </div>
  )
}

export const Default: Story = {
  render: () => (
    <AppleModalProvider>
      <ModalDemo />
    </AppleModalProvider>
  ),
}

export const SmallSize: Story = {
  render: () => (
    <AppleModalProvider>
      <ModalDemo size="sm" />
    </AppleModalProvider>
  ),
}

export const LargeSize: Story = {
  render: () => (
    <AppleModalProvider>
      <ModalDemo size="lg" />
    </AppleModalProvider>
  ),
}

export const NoCloseButton: Story = {
  render: () => (
    <AppleModalProvider>
      <ModalDemo showClose={false} />
    </AppleModalProvider>
  ),
}

export const LongContent: Story = {
  render: () => {
    const LongContentDemo = () => {
      const modal = useAppleModal()
      
      return (
        <div className="p-8">
          <AppleButton onClick={() => modal.openModal({
            title: 'Terms and Conditions',
            description: 'Please read carefully',
            size: 'lg',
            children: (
              <div className="space-y-4">
                {Array.from({ length: 20 }).map((_, i) => (
                  <p key={i} className="text-gray-700 dark:text-gray-300">
                    Lorem ipsum dolor sit amet, consectetur adipiscing elit. 
                    Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.
                  </p>
                ))}
              </div>
            )
          })}>
            Open Long Content Modal
          </AppleButton>
        </div>
      )
    }
    
    return (
      <AppleModalProvider>
        <LongContentDemo />
      </AppleModalProvider>
    )
  },
}

export const MultipleModals: Story = {
  render: () => {
    const MultiModalDemo = () => {
      const modal = useAppleModal()
      
      return (
        <div className="p-8 space-x-4">
          <AppleButton onClick={() => modal.openModal({
            title: 'Modal 1',
            children: <p>First modal</p>
          })}>
            Open Modal 1
          </AppleButton>
          <AppleButton onClick={() => modal.openModal({
            title: 'Modal 2',
            children: <p>Second modal</p>
          })}>
            Open Modal 2
          </AppleButton>
          <AppleButton variant="destructive" onClick={() => modal.closeAll()}>
            Close All
          </AppleButton>
        </div>
      )
    }
    
    return (
      <AppleModalProvider>
        <MultiModalDemo />
      </AppleModalProvider>
    )
  },
}
