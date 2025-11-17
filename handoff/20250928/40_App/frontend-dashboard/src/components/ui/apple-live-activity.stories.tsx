import type { Meta, StoryObj } from '@storybook/react'
import { AppleLiveActivity, type LiveActivityConfig } from './apple-live-activity'
import { Download, Music, Timer, Package, Zap } from 'lucide-react'
import { useEffect, useState } from 'react'

const meta = {
  title: 'Apple Design System/AppleLiveActivity',
  component: AppleLiveActivity.Provider,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'iOS-style Live Activities component for displaying real-time updates and ongoing activities. Features expandable views, progress tracking, and quick actions.'
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
} satisfies Meta<typeof AppleLiveActivity.Provider>

export default meta
type Story = StoryObj<typeof meta>

const LiveActivityDemo = ({ config }: { config: any }) => {
  const { useLiveActivity } = AppleLiveActivity
  const { addActivity } = useLiveActivity()

  useEffect(() => {
    addActivity(config)
  }, [])

  return (
    <div className="w-full h-[600px] flex items-center justify-center bg-neutral-100 dark:bg-neutral-900">
      <p className="text-neutral-500 text-sm">Live Activity appears at the top</p>
    </div>
  )
}

export const Default: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Download in Progress',
          subtitle: 'document.pdf',
          icon: <Download />,
          progress: 45,
          status: '2.3 MB of 5.1 MB'
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const WithActions: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Now Playing',
          subtitle: 'Summer Breeze - Artist Name',
          icon: '🎵',
          expandable: true,
          actions: [
            {
              id: 'pause',
              label: 'Pause',
              variant: 'secondary',
              onPress: () => console.log('Pause pressed')
            },
            {
              id: 'next',
              label: 'Next',
              variant: 'primary',
              onPress: () => console.log('Next pressed')
            }
          ]
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const WithMetadata: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Timer Running',
          subtitle: 'Focus Session',
          icon: <Timer />,
          progress: 60,
          status: '15:00 remaining',
          expandable: true,
          metadata: {
            'Started': '2:30 PM',
            'Duration': '25 minutes',
            'Type': 'Deep Work'
          },
          actions: [
            {
              id: 'stop',
              label: 'Stop',
              variant: 'secondary',
              onPress: () => console.log('Stop pressed')
            },
            {
              id: 'pause',
              label: 'Pause',
              variant: 'primary',
              onPress: () => console.log('Pause pressed')
            }
          ]
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const SuccessVariant: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Download Complete',
          subtitle: 'document.pdf',
          icon: <Download />,
          progress: 100,
          status: 'Ready to view',
          variant: 'success',
          actions: [
            {
              id: 'open',
              label: 'Open',
              variant: 'primary',
              onPress: () => console.log('Open pressed')
            }
          ]
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const ErrorVariant: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Download Failed',
          subtitle: 'document.pdf',
          icon: <Download />,
          status: 'Network error',
          variant: 'error',
          actions: [
            {
              id: 'retry',
              label: 'Retry',
              variant: 'primary',
              onPress: () => console.log('Retry pressed')
            }
          ]
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const WarningVariant: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Low Storage',
          subtitle: 'Download may fail',
          icon: <Package />,
          progress: 75,
          status: 'Only 500 MB remaining',
          variant: 'warning',
          expandable: true,
          metadata: {
            'Available': '500 MB',
            'Required': '1.2 GB',
            'Location': 'Internal Storage'
          },
          actions: [
            {
              id: 'manage',
              label: 'Manage Storage',
              variant: 'primary',
              onPress: () => console.log('Manage pressed')
            }
          ]
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const PrimaryVariant: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Charging',
          subtitle: 'iPhone 15 Pro',
          icon: <Zap />,
          progress: 85,
          status: '15 minutes until full',
          variant: 'primary',
          expandable: true,
          metadata: {
            'Battery': '85%',
            'Time Remaining': '15 minutes',
            'Charging Speed': 'Fast Charging'
          }
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const NonExpandable: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Quick Update',
          subtitle: 'This activity cannot be expanded',
          icon: '📱',
          progress: 30,
          expandable: false
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const WithoutProgress: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Background Task',
          subtitle: 'Processing data...',
          icon: '⚙️',
          status: 'This may take a few moments'
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

export const EmojiIcon: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveActivityDemo
        config={{
          title: 'Pizza Delivery',
          subtitle: 'Your order is on the way',
          icon: '🍕',
          status: 'Arriving in 15 minutes',
          expandable: true,
          metadata: {
            'Order': '#12345',
            'Driver': 'John D.',
            'ETA': '3:45 PM'
          },
          actions: [
            {
              id: 'track',
              label: 'Track',
              variant: 'primary',
              onPress: () => console.log('Track pressed')
            },
            {
              id: 'contact',
              label: 'Contact',
              variant: 'secondary',
              onPress: () => console.log('Contact pressed')
            }
          ]
        }}
      />
    </AppleLiveActivity.Provider>
  )
}

const LiveProgressDemo = () => {
  const { useLiveActivity } = AppleLiveActivity
  const { addActivity, updateActivity } = useLiveActivity()
  const [activityId, setActivityId] = useState<string | null>(null)

  useEffect(() => {
    const { id } = addActivity({
      title: 'Downloading File',
      subtitle: 'large-file.zip',
      icon: <Download />,
      progress: 0,
      status: 'Starting download...',
      expandable: true,
      metadata: {
        'Size': '150 MB',
        'Speed': '0 MB/s',
        'Time Remaining': 'Calculating...'
      }
    })
    setActivityId(id)

    let progress = 0
    const interval = setInterval(() => {
      progress += 2
      if (progress <= 100) {
        const speed = (2.5 + Math.random() * 1.5).toFixed(1)
        const remaining = Math.ceil((100 - progress) / 2)
        updateActivity(id, {
          progress,
          status: `${progress}% complete`,
          metadata: {
            'Size': '150 MB',
            'Speed': `${speed} MB/s`,
            'Time Remaining': `${remaining} seconds`
          },
          variant: progress === 100 ? 'success' : 'default'
        })
      } else {
        clearInterval(interval)
        updateActivity(id, {
          title: 'Download Complete',
          status: 'Ready to open',
          variant: 'success',
          actions: [
            {
              id: 'open',
              label: 'Open',
              variant: 'primary',
              onPress: () => console.log('Open pressed')
            }
          ]
        })
      }
    }, 200)

    return () => clearInterval(interval)
  }, [])

  return (
    <div className="w-full h-[600px] flex items-center justify-center bg-neutral-100 dark:bg-neutral-900">
      <p className="text-neutral-500 text-sm">Watch the live progress update</p>
    </div>
  )
}

export const LiveProgress: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <LiveProgressDemo />
    </AppleLiveActivity.Provider>
  )
}

const MultipleActivitiesDemo = () => {
  const { useLiveActivity } = AppleLiveActivity
  const { addActivity } = useLiveActivity()

  useEffect(() => {
    addActivity({
      id: 'download',
      title: 'Download in Progress',
      subtitle: 'document.pdf',
      icon: <Download />,
      progress: 45,
      status: '2.3 MB of 5.1 MB'
    })

    setTimeout(() => {
      addActivity({
        id: 'music',
        title: 'Now Playing',
        subtitle: 'Summer Breeze',
        icon: <Music />,
        variant: 'primary',
        actions: [
          {
            id: 'pause',
            label: 'Pause',
            variant: 'primary',
            onPress: () => console.log('Pause')
          }
        ]
      })
    }, 500)

    setTimeout(() => {
      addActivity({
        id: 'timer',
        title: 'Timer Running',
        subtitle: 'Focus Session',
        icon: <Timer />,
        progress: 60,
        status: '15:00 remaining',
        variant: 'success'
      })
    }, 1000)
  }, [])

  return (
    <div className="w-full h-[600px] flex items-center justify-center bg-neutral-100 dark:bg-neutral-900">
      <p className="text-neutral-500 text-sm">Multiple activities stacked</p>
    </div>
  )
}

export const MultipleActivities: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider>
      <MultipleActivitiesDemo />
    </AppleLiveActivity.Provider>
  )
}

export const BottomPosition: Story = {
  args: {},
  render: () => (
    <AppleLiveActivity.Provider position="bottom">
      <LiveActivityDemo
        config={{
          title: 'Bottom Positioned',
          subtitle: 'Activity appears at the bottom',
          icon: '📍',
          progress: 50,
          status: 'Positioned at bottom'
        }}
      />
    </AppleLiveActivity.Provider>
  )
}
