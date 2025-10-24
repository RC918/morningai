import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from './card';
import { Input } from './input';
import { Spinner, Skeleton, LoadingDots, ProgressBar, PulseLoader } from './loading-states';

const meta = {
  title: 'UI/Micro Interactions',
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const ButtonInteractions: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Button Press Animation</h3>
        <div className="flex gap-4">
          <Button>Click Me</Button>
          <Button variant="outline">Outline Button</Button>
          <Button variant="destructive">Delete</Button>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Click buttons to see the press animation effect
        </p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Buttons have a subtle press animation when clicked, providing tactile feedback.',
      },
    },
  },
};

export const CardHoverEffects: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Interactive Cards</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <Card interactive>
            <CardHeader>
              <CardTitle>Hover Me</CardTitle>
              <CardDescription>This card lifts on hover</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Interactive cards provide visual feedback when hovered.</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Static Card</CardTitle>
              <CardDescription>This card doesn't have hover effect</CardDescription>
            </CardHeader>
            <CardContent>
              <p className="text-sm">Regular cards remain static for non-interactive content.</p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Interactive cards lift and cast a shadow on hover, indicating they are clickable.',
      },
    },
  },
};

export const InputFocusEffects: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Input Focus Glow</h3>
        <div className="space-y-4 max-w-md">
          <div>
            <label className="block text-sm font-medium mb-2">Email</label>
            <Input type="email" placeholder="Enter your email" />
          </div>
          <div>
            <label className="block text-sm font-medium mb-2">Password</label>
            <Input type="password" placeholder="Enter your password" />
          </div>
        </div>
        <p className="text-sm text-muted-foreground mt-2">
          Focus on inputs to see the glow effect
        </p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input fields have a subtle glow effect when focused, improving accessibility.',
      },
    },
  },
};

export const LoadingStates: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Spinner</h3>
        <div className="flex gap-4 items-center">
          <Spinner size="sm" />
          <Spinner size="md" />
          <Spinner size="lg" />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Skeleton Loaders</h3>
        <div className="space-y-4 max-w-md">
          <Skeleton variant="title" />
          <Skeleton variant="text" />
          <Skeleton variant="text" />
          <div className="flex gap-4">
            <Skeleton variant="avatar" />
            <div className="flex-1 space-y-2">
              <Skeleton variant="text" />
              <Skeleton variant="text" />
            </div>
          </div>
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Loading Dots</h3>
        <LoadingDots />
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Progress Bar</h3>
        <div className="space-y-4 max-w-md">
          <ProgressBar value={25} showLabel />
          <ProgressBar value={50} showLabel />
          <ProgressBar value={75} showLabel />
          <ProgressBar value={100} showLabel />
        </div>
      </div>

      <div>
        <h3 className="text-lg font-semibold mb-4">Pulse Loader</h3>
        <PulseLoader />
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Various loading state components with smooth animations.',
      },
    },
  },
};

export const StaggeredList: Story = {
  render: () => (
    <div className="space-y-8">
      <div>
        <h3 className="text-lg font-semibold mb-4">Staggered Animation</h3>
        <div className="space-y-2 max-w-md">
          {[1, 2, 3, 4, 5].map((item) => (
            <div
              key={item}
              className="stagger-item p-4 bg-card border rounded-lg"
            >
              <p className="font-medium">Item {item}</p>
              <p className="text-sm text-muted-foreground">
                This item animates in with a stagger effect
              </p>
            </div>
          ))}
        </div>
        <p className="text-sm text-muted-foreground mt-4">
          Reload the story to see the staggered animation
        </p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'List items animate in with a staggered delay, creating a smooth entrance effect.',
      },
    },
  },
};
