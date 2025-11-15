import type { Meta, StoryObj } from '@storybook/react'
import { Progress } from './progress'

const meta = {
  title: 'Components/Progress',
  component: Progress,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    value: {
      control: { type: 'range', min: 0, max: 100, step: 1 },
      description: 'The progress value (0-100)',
    },
  },
} satisfies Meta<typeof Progress>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    value: 50,
  },
}

export const Empty: Story = {
  args: {
    value: 0,
  },
}

export const Quarter: Story = {
  args: {
    value: 25,
  },
}

export const Half: Story = {
  args: {
    value: 50,
  },
}

export const ThreeQuarters: Story = {
  args: {
    value: 75,
  },
}

export const Complete: Story = {
  args: {
    value: 100,
  },
}

export const WithLabel: Story = {
  render: () => (
    <div className="w-full space-y-2">
      <div className="flex justify-between text-sm">
        <span>Uploading...</span>
        <span>65%</span>
      </div>
      <Progress value={65} />
    </div>
  ),
}

export const MultipleProgress: Story = {
  render: () => (
    <div className="w-full space-y-6">
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium">Project Alpha</span>
          <span className="text-muted-foreground">25%</span>
        </div>
        <Progress value={25} />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium">Project Beta</span>
          <span className="text-muted-foreground">60%</span>
        </div>
        <Progress value={60} />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium">Project Gamma</span>
          <span className="text-muted-foreground">90%</span>
        </div>
        <Progress value={90} />
      </div>
    </div>
  ),
}

export const AllStates: Story = {
  render: () => (
    <div className="w-full space-y-4">
      <div className="space-y-2">
        <span className="text-sm">0% - Not Started</span>
        <Progress value={0} />
      </div>
      <div className="space-y-2">
        <span className="text-sm">25% - In Progress</span>
        <Progress value={25} />
      </div>
      <div className="space-y-2">
        <span className="text-sm">50% - Half Way</span>
        <Progress value={50} />
      </div>
      <div className="space-y-2">
        <span className="text-sm">75% - Almost Done</span>
        <Progress value={75} />
      </div>
      <div className="space-y-2">
        <span className="text-sm">100% - Complete</span>
        <Progress value={100} />
      </div>
    </div>
  ),
}

export const CustomWidth: Story = {
  render: () => (
    <div className="space-y-4">
      <div className="space-y-2">
        <span className="text-sm">Small (200px)</span>
        <Progress value={60} className="w-[200px]" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Medium (400px)</span>
        <Progress value={60} className="w-[400px]" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Large (600px)</span>
        <Progress value={60} className="w-[600px]" />
      </div>
    </div>
  ),
}

export const CustomHeight: Story = {
  render: () => (
    <div className="w-full space-y-4">
      <div className="space-y-2">
        <span className="text-sm">Thin (h-1)</span>
        <Progress value={60} className="h-1" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Default (h-2)</span>
        <Progress value={60} className="h-2" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Thick (h-4)</span>
        <Progress value={60} className="h-4" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Extra Thick (h-6)</span>
        <Progress value={60} className="h-6" />
      </div>
    </div>
  ),
}
