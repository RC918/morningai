import type { Meta, StoryObj } from '@storybook/react'
import { AppleSheetProvider, useAppleSheet, type SheetSize } from './apple-sheet'
import { AppleButton } from './apple-button'

const meta: Meta<typeof AppleSheetProvider> = {
  title: 'UI/AppleSheet',
  component: AppleSheetProvider,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
}

export default meta
type Story = StoryObj<typeof AppleSheetProvider>

const SheetDemo = ({ size = 'md' as SheetSize, showClose = true, showHandle = true }) => {
  const sheet = useAppleSheet()

  const handleOpen = () => {
    sheet.openSheet({
      title: 'Apple Bottom Sheet',
      description: 'Swipe down or drag to dismiss',
      size,
      showClose,
      showHandle,
      children: (
        <div className="space-y-4">
          <p className="text-gray-700 dark:text-gray-300">
            This bottom sheet features:
          </p>
          <ul className="list-disc list-inside space-y-2 text-gray-600 dark:text-gray-400">
            <li>Drag-to-dismiss gesture (swipe down)</li>
            <li>Spring-based animations</li>
            <li>Rounded top corners (iOS style)</li>
            <li>Drag handle indicator</li>
            <li>Haptic feedback</li>
            <li>Backdrop blur effect</li>
          </ul>
          <div className="flex gap-2 pt-4">
            <AppleButton onClick={() => sheet.closeAll()}>
              Close
            </AppleButton>
          </div>
        </div>
      )
    })
  }

  return (
    <div className="p-8">
      <AppleButton onClick={handleOpen}>
        Open Bottom Sheet
      </AppleButton>
    </div>
  )
}

export const Default: Story = {
  render: () => (
    <AppleSheetProvider>
      <SheetDemo />
    </AppleSheetProvider>
  ),
}

export const SmallSize: Story = {
  render: () => (
    <AppleSheetProvider>
      <SheetDemo size="sm" />
    </AppleSheetProvider>
  ),
}

export const LargeSize: Story = {
  render: () => (
    <AppleSheetProvider>
      <SheetDemo size="lg" />
    </AppleSheetProvider>
  ),
}

export const FullHeight: Story = {
  render: () => (
    <AppleSheetProvider>
      <SheetDemo size="full" />
    </AppleSheetProvider>
  ),
}

export const NoHandle: Story = {
  render: () => (
    <AppleSheetProvider>
      <SheetDemo showHandle={false} />
    </AppleSheetProvider>
  ),
}

export const NoCloseButton: Story = {
  render: () => (
    <AppleSheetProvider>
      <SheetDemo showClose={false} />
    </AppleSheetProvider>
  ),
}

export const ScrollableContent: Story = {
  render: () => {
    const ScrollableDemo = () => {
      const sheet = useAppleSheet()
      
      return (
        <div className="p-8">
          <AppleButton onClick={() => sheet.openSheet({
            title: 'Scrollable Content',
            description: 'Long content with scroll',
            size: 'lg',
            children: (
              <div className="space-y-4">
                {Array.from({ length: 30 }).map((_, i) => (
                  <p key={i} className="text-gray-700 dark:text-gray-300">
                    Item {i + 1}: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
                  </p>
                ))}
              </div>
            )
          })}>
            Open Scrollable Sheet
          </AppleButton>
        </div>
      )
    }
    
    return (
      <AppleSheetProvider>
        <ScrollableDemo />
      </AppleSheetProvider>
    )
  },
}

export const ActionSheet: Story = {
  render: () => {
    const ActionSheetDemo = () => {
      const sheet = useAppleSheet()
      
      const actions = [
        { label: 'Share', icon: '📤' },
        { label: 'Edit', icon: '✏️' },
        { label: 'Duplicate', icon: '📋' },
        { label: 'Delete', icon: '🗑️', destructive: true },
      ]
      
      return (
        <div className="p-8">
          <AppleButton onClick={() => sheet.openSheet({
            title: 'Actions',
            size: 'sm',
            children: (
              <div className="space-y-2">
                {actions.map((action, i) => (
                  <button
                    key={i}
                    className={`w-full p-4 rounded-xl text-left transition-colors ${
                      action.destructive
                        ? 'hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400'
                        : 'hover:bg-gray-100 dark:hover:bg-gray-800'
                    }`}
                    onClick={() => {
                      console.log(action.label)
                      sheet.closeAll()
                    }}
                  >
                    <span className="mr-3">{action.icon}</span>
                    {action.label}
                  </button>
                ))}
              </div>
            )
          })}>
            Show Actions
          </AppleButton>
        </div>
      )
    }
    
    return (
      <AppleSheetProvider>
        <ActionSheetDemo />
      </AppleSheetProvider>
    )
  },
}
