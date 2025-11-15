import type { Meta, StoryObj } from '@storybook/react'
import { ChevronRight, Download, Mail, Plus, Trash2 } from 'lucide-react'
import { Button } from './button'

const meta = {
  title: 'Components/Button',
  component: Button,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'The visual style variant',
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'The size of the button',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the button is disabled',
    },
    asChild: {
      control: 'boolean',
      description: 'Whether to render as a child component (Slot)',
    },
  },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    children: 'Button',
  },
}

export const Destructive: Story = {
  args: {
    variant: 'destructive',
    children: 'Delete',
  },
}

export const Outline: Story = {
  args: {
    variant: 'outline',
    children: 'Outline',
  },
}

export const Secondary: Story = {
  args: {
    variant: 'secondary',
    children: 'Secondary',
  },
}

export const Ghost: Story = {
  args: {
    variant: 'ghost',
    children: 'Ghost',
  },
}

export const Link: Story = {
  args: {
    variant: 'link',
    children: 'Link',
  },
}

export const Small: Story = {
  args: {
    size: 'sm',
    children: 'Small',
  },
}

export const Large: Story = {
  args: {
    size: 'lg',
    children: 'Large',
  },
}

export const WithIcon: Story = {
  render: () => (
    <div className="flex gap-2">
      <Button>
        <Mail />
        Login with Email
      </Button>
      <Button variant="outline">
        <Download />
        Download
      </Button>
      <Button variant="secondary">
        <Plus />
        Add Item
      </Button>
    </div>
  ),
}

export const IconOnly: Story = {
  render: () => (
    <div className="flex gap-2">
      <Button size="icon">
        <ChevronRight />
      </Button>
      <Button size="icon" variant="outline">
        <Download />
      </Button>
      <Button size="icon" variant="ghost">
        <Plus />
      </Button>
      <Button size="icon" variant="destructive">
        <Trash2 />
      </Button>
    </div>
  ),
}

export const Disabled: Story = {
  render: () => (
    <div className="flex gap-2">
      <Button disabled>Default</Button>
      <Button disabled variant="destructive">Destructive</Button>
      <Button disabled variant="outline">Outline</Button>
      <Button disabled variant="secondary">Secondary</Button>
      <Button disabled variant="ghost">Ghost</Button>
    </div>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex gap-2 items-center">
        <span className="w-24 text-sm font-medium">Default:</span>
        <Button>Button</Button>
        <Button size="sm">Small</Button>
        <Button size="lg">Large</Button>
      </div>
      <div className="flex gap-2 items-center">
        <span className="w-24 text-sm font-medium">Destructive:</span>
        <Button variant="destructive">Button</Button>
        <Button variant="destructive" size="sm">Small</Button>
        <Button variant="destructive" size="lg">Large</Button>
      </div>
      <div className="flex gap-2 items-center">
        <span className="w-24 text-sm font-medium">Outline:</span>
        <Button variant="outline">Button</Button>
        <Button variant="outline" size="sm">Small</Button>
        <Button variant="outline" size="lg">Large</Button>
      </div>
      <div className="flex gap-2 items-center">
        <span className="w-24 text-sm font-medium">Secondary:</span>
        <Button variant="secondary">Button</Button>
        <Button variant="secondary" size="sm">Small</Button>
        <Button variant="secondary" size="lg">Large</Button>
      </div>
      <div className="flex gap-2 items-center">
        <span className="w-24 text-sm font-medium">Ghost:</span>
        <Button variant="ghost">Button</Button>
        <Button variant="ghost" size="sm">Small</Button>
        <Button variant="ghost" size="lg">Large</Button>
      </div>
      <div className="flex gap-2 items-center">
        <span className="w-24 text-sm font-medium">Link:</span>
        <Button variant="link">Button</Button>
        <Button variant="link" size="sm">Small</Button>
        <Button variant="link" size="lg">Large</Button>
      </div>
    </div>
  ),
}

export const AllSizes: Story = {
  render: () => (
    <div className="flex gap-2 items-center">
      <Button size="sm">Small</Button>
      <Button size="default">Default</Button>
      <Button size="lg">Large</Button>
      <Button size="icon">
        <Plus />
      </Button>
    </div>
  ),
}

export const Loading: Story = {
  render: () => (
    <div className="flex gap-2">
      <Button disabled>
        <span className="animate-spin">⏳</span>
        Loading...
      </Button>
      <Button variant="outline" disabled>
        <span className="animate-spin">⏳</span>
        Processing
      </Button>
    </div>
  ),
}
