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
    variant: {
      control: 'select',
      options: ['default', 'success', 'warning', 'error', 'pink', 'cyan'],
      description: 'The color variant (iotask design system)',
    },
    showLabel: {
      control: 'boolean',
      description: 'Whether to show the percentage label',
    },
  },
} satisfies Meta<typeof Progress>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    value: 50,
    'aria-label': 'Progress: 50%',
  },
}

export const Empty: Story = {
  args: {
    value: 0,
    'aria-label': 'Progress: 0%',
  },
}

export const Quarter: Story = {
  args: {
    value: 25,
    'aria-label': 'Progress: 25%',
  },
}

export const Half: Story = {
  args: {
    value: 50,
    'aria-label': 'Progress: 50%',
  },
}

export const ThreeQuarters: Story = {
  args: {
    value: 75,
    'aria-label': 'Progress: 75%',
  },
}

export const Complete: Story = {
  args: {
    value: 100,
    'aria-label': 'Progress: 100%',
  },
}

export const WithShowLabel: Story = {
  args: {
    value: 65,
    showLabel: true,
    'aria-label': 'Progress: 65%',
  },
}

export const SuccessVariant: Story = {
  args: {
    value: 75,
    variant: 'success',
    'aria-label': 'Success progress: 75%',
  },
}

export const WarningVariant: Story = {
  args: {
    value: 45,
    variant: 'warning',
    'aria-label': 'Warning progress: 45%',
  },
}

export const ErrorVariant: Story = {
  args: {
    value: 30,
    variant: 'error',
    'aria-label': 'Error progress: 30%',
  },
}

export const PinkVariant: Story = {
  args: {
    value: 60,
    variant: 'pink',
    'aria-label': 'Pink progress: 60%',
  },
}

export const CyanVariant: Story = {
  args: {
    value: 80,
    variant: 'cyan',
    'aria-label': 'Cyan progress: 80%',
  },
}

export const AllColorVariants: Story = {
  render: () => (
    <div className="w-full space-y-4">
      <div className="space-y-2">
        <span className="text-sm font-medium">Default (Primary Blue)</span>
        <Progress value={60} aria-label="Default: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm font-medium">Success (Green)</span>
        <Progress value={60} variant="success" aria-label="Success: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm font-medium">Warning (Orange)</span>
        <Progress value={60} variant="warning" aria-label="Warning: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm font-medium">Error (Red)</span>
        <Progress value={60} variant="error" aria-label="Error: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm font-medium">Pink</span>
        <Progress value={60} variant="pink" aria-label="Pink: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm font-medium">Cyan</span>
        <Progress value={60} variant="cyan" aria-label="Cyan: 60%" />
      </div>
    </div>
  ),
}

export const WithLabel: Story = {
  render: () => (
    <div className="w-full space-y-2">
      <div className="flex justify-between text-sm">
        <span>Uploading...</span>
        <span>65%</span>
      </div>
      <Progress value={65} aria-label="Uploading: 65%" />
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
        <Progress value={25} aria-label="Project Alpha: 25%" />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium">Project Beta</span>
          <span className="text-muted-foreground">60%</span>
        </div>
        <Progress value={60} aria-label="Project Beta: 60%" />
      </div>
      <div className="space-y-2">
        <div className="flex justify-between text-sm">
          <span className="font-medium">Project Gamma</span>
          <span className="text-muted-foreground">90%</span>
        </div>
        <Progress value={90} aria-label="Project Gamma: 90%" />
      </div>
    </div>
  ),
}

export const AllStates: Story = {
  render: () => (
    <div className="w-full space-y-4">
      <div className="space-y-2">
        <span className="text-sm">0% - Not Started</span>
        <Progress value={0} aria-label="Not Started: 0%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">25% - In Progress</span>
        <Progress value={25} aria-label="In Progress: 25%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">50% - Half Way</span>
        <Progress value={50} aria-label="Half Way: 50%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">75% - Almost Done</span>
        <Progress value={75} aria-label="Almost Done: 75%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">100% - Complete</span>
        <Progress value={100} aria-label="Complete: 100%" />
      </div>
    </div>
  ),
}

export const CustomWidth: Story = {
  render: () => (
    <div className="space-y-4">
      <div className="space-y-2">
        <span className="text-sm">Small (200px)</span>
        <Progress value={60} className="w-[200px]" aria-label="Small progress: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Medium (400px)</span>
        <Progress value={60} className="w-[400px]" aria-label="Medium progress: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Large (600px)</span>
        <Progress value={60} className="w-[600px]" aria-label="Large progress: 60%" />
      </div>
    </div>
  ),
}

export const CustomHeight: Story = {
  render: () => (
    <div className="w-full space-y-4">
      <div className="space-y-2">
        <span className="text-sm">Thin (h-1)</span>
        <Progress value={60} className="h-1" aria-label="Thin progress: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Default (h-2)</span>
        <Progress value={60} className="h-2" aria-label="Default progress: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Thick (h-4)</span>
        <Progress value={60} className="h-4" aria-label="Thick progress: 60%" />
      </div>
      <div className="space-y-2">
        <span className="text-sm">Extra Thick (h-6)</span>
        <Progress value={60} className="h-6" aria-label="Extra thick progress: 60%" />
      </div>
    </div>
  ),
}
