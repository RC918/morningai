import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from './badge';

const meta = {
  title: 'UI/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'outline'],
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Badge',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
};

export const Destructive: Story = {
  args: {
    children: 'Destructive',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const WithIcon: Story = {
  render: () => (
    <Badge>
      <span className="mr-1">✓</span>
      Success
    </Badge>
  ),
};

export const StatusBadges: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Pending</Badge>
      <Badge variant="destructive">Error</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Badge className="text-xs">Small</Badge>
      <Badge>Medium</Badge>
      <Badge className="text-base px-3 py-1">Large</Badge>
    </div>
  ),
};

export const WithCount: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge>New 3</Badge>
      <Badge variant="destructive">Errors 12</Badge>
      <Badge variant="secondary">Pending 5</Badge>
    </div>
  ),
};

export const Clickable: Story = {
  render: () => (
    <Badge 
      className="cursor-pointer hover:opacity-80"
      onClick={() => alert('Badge clicked!')}
    >
      Click me
    </Badge>
  ),
};
