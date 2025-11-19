import type { Meta, StoryObj } from '@storybook/react'
import { StatusBadge } from './status-badge'

const meta = {
  title: 'Components/StatusBadge',
  component: StatusBadge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    status: {
      control: 'select',
      options: ['completed', 'running', 'failed', 'queued', 'assigned', 'cancelled'],
      description: 'The status to display',
    },
    showIcon: {
      control: 'boolean',
      description: 'Whether to show an icon',
    },
  },
} satisfies Meta<typeof StatusBadge>

export default meta
type Story = StoryObj<typeof meta>

export const Completed: Story = {
  args: {
    status: 'completed',
    children: 'Completed',
  },
}

export const Running: Story = {
  args: {
    status: 'running',
    children: 'Running',
  },
}

export const Failed: Story = {
  args: {
    status: 'failed',
    children: 'Failed',
  },
}

export const Queued: Story = {
  args: {
    status: 'queued',
    children: 'Queued',
  },
}

export const Assigned: Story = {
  args: {
    status: 'assigned',
    children: 'Assigned',
  },
}

export const Cancelled: Story = {
  args: {
    status: 'cancelled',
    children: 'Cancelled',
  },
}

export const WithoutIcon: Story = {
  args: {
    status: 'completed',
    showIcon: false,
    children: 'Completed',
  },
}

export const AllStatuses: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 items-center">
        <StatusBadge status="completed">Completed</StatusBadge>
        <span className="text-sm text-gray-600">Success state</span>
      </div>
      <div className="flex gap-2 items-center">
        <StatusBadge status="running">Running</StatusBadge>
        <span className="text-sm text-gray-600">In progress with animation</span>
      </div>
      <div className="flex gap-2 items-center">
        <StatusBadge status="failed">Failed</StatusBadge>
        <span className="text-sm text-gray-600">Error state</span>
      </div>
      <div className="flex gap-2 items-center">
        <StatusBadge status="queued">Queued</StatusBadge>
        <span className="text-sm text-gray-600">Waiting state</span>
      </div>
      <div className="flex gap-2 items-center">
        <StatusBadge status="assigned">Assigned</StatusBadge>
        <span className="text-sm text-gray-600">Assigned state</span>
      </div>
      <div className="flex gap-2 items-center">
        <StatusBadge status="cancelled">Cancelled</StatusBadge>
        <span className="text-sm text-gray-600">Cancelled state</span>
      </div>
    </div>
  ),
}
