import type { Meta, StoryObj } from '@storybook/react'
import { AppleActionSheet } from './apple-action-sheet'
import { Trash2, Share2, Edit, Copy, Download, Mail, MessageSquare, Star } from 'lucide-react'

const meta: Meta<typeof AppleActionSheet.Provider> = {
  title: 'Apple Components/AppleActionSheet',
  component: AppleActionSheet.Provider,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'iOS-style Action Sheet component for presenting action options to users.'
      }
    }
  },
  tags: ['autodocs']
}

export default meta
type Story = StoryObj<typeof AppleActionSheet.Provider>

const ActionSheetDemo = ({ 
  title, 
  message, 
  actions, 
  cancelLabel 
}: { 
  title?: string
  message?: string
  actions: any[]
  cancelLabel?: string
}) => {
  const { show } = AppleActionSheet.useActionSheet()

  const handleShow = () => {
    show({
      title,
      message,
      actions,
      cancelLabel,
      onCancel: () => console.log('Cancelled')
    })
  }

  return (
    <div className="p-8">
      <button
        onClick={handleShow}
        className="px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
      >
        Show Action Sheet
      </button>
    </div>
  )
}

export const Default: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Choose an action"
        message="Select one of the options below"
        actions={[
          {
            id: '1',
            label: 'Edit',
            icon: <Edit className="w-5 h-5" />,
            onSelect: () => console.log('Edit selected')
          },
          {
            id: '2',
            label: 'Share',
            icon: <Share2 className="w-5 h-5" />,
            onSelect: () => console.log('Share selected')
          },
          {
            id: '3',
            label: 'Delete',
            icon: <Trash2 className="w-5 h-5" />,
            destructive: true,
            onSelect: () => console.log('Delete selected')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const SimpleActions: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        actions={[
          {
            id: '1',
            label: 'Copy',
            onSelect: () => console.log('Copy')
          },
          {
            id: '2',
            label: 'Paste',
            onSelect: () => console.log('Paste')
          },
          {
            id: '3',
            label: 'Delete',
            destructive: true,
            onSelect: () => console.log('Delete')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const WithIcons: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="File Actions"
        actions={[
          {
            id: '1',
            label: 'Download',
            icon: <Download className="w-5 h-5" />,
            onSelect: () => console.log('Download')
          },
          {
            id: '2',
            label: 'Share',
            icon: <Share2 className="w-5 h-5" />,
            onSelect: () => console.log('Share')
          },
          {
            id: '3',
            label: 'Copy Link',
            icon: <Copy className="w-5 h-5" />,
            onSelect: () => console.log('Copy Link')
          },
          {
            id: '4',
            label: 'Delete',
            icon: <Trash2 className="w-5 h-5" />,
            destructive: true,
            onSelect: () => console.log('Delete')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const DestructiveAction: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Delete Item"
        message="This action cannot be undone. Are you sure you want to delete this item?"
        actions={[
          {
            id: '1',
            label: 'Delete',
            destructive: true,
            onSelect: () => console.log('Deleted')
          }
        ]}
        cancelLabel="Keep Item"
      />
    </AppleActionSheet.Provider>
  )
}

export const MultipleDestructive: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Danger Zone"
        message="These actions are permanent and cannot be undone"
        actions={[
          {
            id: '1',
            label: 'Delete All Messages',
            destructive: true,
            onSelect: () => console.log('Delete All Messages')
          },
          {
            id: '2',
            label: 'Clear History',
            destructive: true,
            onSelect: () => console.log('Clear History')
          },
          {
            id: '3',
            label: 'Reset Settings',
            destructive: true,
            onSelect: () => console.log('Reset Settings')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const WithDisabledActions: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Document Actions"
        message="Some actions are not available for this document"
        actions={[
          {
            id: '1',
            label: 'Edit',
            icon: <Edit className="w-5 h-5" />,
            onSelect: () => console.log('Edit')
          },
          {
            id: '2',
            label: 'Share',
            icon: <Share2 className="w-5 h-5" />,
            disabled: true,
            onSelect: () => console.log('Share')
          },
          {
            id: '3',
            label: 'Download',
            icon: <Download className="w-5 h-5" />,
            disabled: true,
            onSelect: () => console.log('Download')
          },
          {
            id: '4',
            label: 'Delete',
            icon: <Trash2 className="w-5 h-5" />,
            destructive: true,
            onSelect: () => console.log('Delete')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const ShareSheet: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Share"
        message="Choose how you want to share this content"
        actions={[
          {
            id: '1',
            label: 'Message',
            icon: <MessageSquare className="w-5 h-5" />,
            onSelect: () => console.log('Share via Message')
          },
          {
            id: '2',
            label: 'Mail',
            icon: <Mail className="w-5 h-5" />,
            onSelect: () => console.log('Share via Mail')
          },
          {
            id: '3',
            label: 'Copy Link',
            icon: <Copy className="w-5 h-5" />,
            onSelect: () => console.log('Copy Link')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const LongList: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Choose an option"
        actions={[
          {
            id: '1',
            label: 'Option 1',
            onSelect: () => console.log('Option 1')
          },
          {
            id: '2',
            label: 'Option 2',
            onSelect: () => console.log('Option 2')
          },
          {
            id: '3',
            label: 'Option 3',
            onSelect: () => console.log('Option 3')
          },
          {
            id: '4',
            label: 'Option 4',
            onSelect: () => console.log('Option 4')
          },
          {
            id: '5',
            label: 'Option 5',
            onSelect: () => console.log('Option 5')
          },
          {
            id: '6',
            label: 'Option 6',
            onSelect: () => console.log('Option 6')
          },
          {
            id: '7',
            label: 'Delete All',
            destructive: true,
            onSelect: () => console.log('Delete All')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const NoTitle: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        actions={[
          {
            id: '1',
            label: 'Save',
            icon: <Download className="w-5 h-5" />,
            onSelect: () => console.log('Save')
          },
          {
            id: '2',
            label: 'Share',
            icon: <Share2 className="w-5 h-5" />,
            onSelect: () => console.log('Share')
          },
          {
            id: '3',
            label: 'Delete',
            icon: <Trash2 className="w-5 h-5" />,
            destructive: true,
            onSelect: () => console.log('Delete')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const CustomCancelLabel: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Confirm Action"
        message="Are you sure you want to proceed?"
        actions={[
          {
            id: '1',
            label: 'Proceed',
            onSelect: () => console.log('Proceed')
          }
        ]}
        cancelLabel="Go Back"
      />
    </AppleActionSheet.Provider>
  )
}

export const FavoriteActions: Story = {
  render: () => (
    <AppleActionSheet.Provider>
      <ActionSheetDemo
        title="Favorite"
        message="Add this item to your favorites?"
        actions={[
          {
            id: '1',
            label: 'Add to Favorites',
            icon: <Star className="w-5 h-5" />,
            onSelect: () => console.log('Added to favorites')
          },
          {
            id: '2',
            label: 'Create New List',
            icon: <Edit className="w-5 h-5" />,
            onSelect: () => console.log('Create new list')
          }
        ]}
      />
    </AppleActionSheet.Provider>
  )
}

export const Interactive: Story = {
  render: () => {
    const InteractiveDemo = () => {
      const { show, isVisible } = AppleActionSheet.useActionSheet()

      const handleShow = () => {
        show({
          title: 'Interactive Demo',
          message: 'This is a fully interactive action sheet',
          actions: [
            {
              id: '1',
              label: 'Action 1',
              icon: <Edit className="w-5 h-5" />,
              onSelect: () => alert('Action 1 selected')
            },
            {
              id: '2',
              label: 'Action 2',
              icon: <Share2 className="w-5 h-5" />,
              onSelect: () => alert('Action 2 selected')
            },
            {
              id: '3',
              label: 'Destructive Action',
              icon: <Trash2 className="w-5 h-5" />,
              destructive: true,
              onSelect: () => alert('Destructive action selected')
            }
          ],
          onCancel: () => alert('Cancelled')
        })
      }

      return (
        <div className="p-8 space-y-4">
          <button
            onClick={handleShow}
            className="px-6 py-3 bg-primary-600 text-white rounded-xl font-medium hover:bg-primary-700 transition-colors"
          >
            Show Action Sheet
          </button>
          <div className="text-sm text-neutral-600">
            Status: {isVisible ? 'Visible' : 'Hidden'}
          </div>
        </div>
      )
    }

    return (
      <AppleActionSheet.Provider>
        <InteractiveDemo />
      </AppleActionSheet.Provider>
    )
  }
}
