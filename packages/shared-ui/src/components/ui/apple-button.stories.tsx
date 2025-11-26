import type { Meta, StoryObj } from '@storybook/react';
import React from 'react';
import { AppleButton } from './apple-button';

const meta: Meta<typeof AppleButton> = {
  title: 'Design System/Apple Button',
  component: AppleButton,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'destructive', 'outline', 'ghost', 'link', 'filled', 'tinted'],
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg', 'icon', 'icon-sm', 'icon-lg'],
    },
    haptic: {
      control: 'select',
      options: ['none', 'light', 'medium', 'heavy'],
    },
    disabled: {
      control: 'boolean',
    },
  },
};

export default meta;
type Story = StoryObj<typeof AppleButton>;

export const Primary: Story = {
  args: {
    children: 'Primary Button',
    variant: 'primary',
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Button Variants</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary">Primary</AppleButton>
          <AppleButton variant="secondary">Secondary</AppleButton>
          <AppleButton variant="destructive">Destructive</AppleButton>
          <AppleButton variant="outline">Outline</AppleButton>
          <AppleButton variant="ghost">Ghost</AppleButton>
          <AppleButton variant="link">Link</AppleButton>
          <AppleButton variant="filled">Filled</AppleButton>
          <AppleButton variant="tinted">Tinted</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Button Sizes</h3>
        <div className="flex items-center flex-wrap gap-3">
          <AppleButton size="sm">Small</AppleButton>
          <AppleButton size="default">Default</AppleButton>
          <AppleButton size="lg">Large</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const HapticAdapter: Story = {
  render: () => {
    const mockHapticFeedback = (element: HTMLButtonElement, type: string) => {
      console.log(`Haptic feedback triggered: ${type}`, element);
    };

    return (
      <div className="flex flex-col gap-4 p-8">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">Haptic Feedback Adapter</h3>
          <p className="text-sm text-muted-foreground">Click buttons to see haptic feedback in console</p>
          <div className="flex flex-wrap gap-3">
            <AppleButton haptic="none" onHapticFeedback={mockHapticFeedback}>No Haptic</AppleButton>
            <AppleButton haptic="light" onHapticFeedback={mockHapticFeedback}>Light</AppleButton>
            <AppleButton haptic="medium" onHapticFeedback={mockHapticFeedback}>Medium (Default)</AppleButton>
            <AppleButton haptic="heavy" onHapticFeedback={mockHapticFeedback}>Heavy</AppleButton>
          </div>
        </div>
      </div>
    );
  },
};

export const SpringAnimation: Story = {
  render: () => {
    const snappyConfig = {
      type: 'spring' as const,
      stiffness: 300,
      damping: 30,
      mass: 0.6,
    };

    const gentleConfig = {
      type: 'spring' as const,
      stiffness: 120,
      damping: 14,
      mass: 0.5,
    };

    return (
      <div className="flex flex-col gap-4 p-8">
        <div className="space-y-2">
          <h3 className="text-sm font-semibold text-muted-foreground">Spring Animation Adapter</h3>
          <p className="text-sm text-muted-foreground">Hover to see different spring animations</p>
          <div className="flex flex-wrap gap-3">
            <AppleButton springConfig={snappyConfig}>Snappy Spring</AppleButton>
            <AppleButton springConfig={gentleConfig}>Gentle Spring</AppleButton>
            <AppleButton>Default (No Config)</AppleButton>
          </div>
        </div>
      </div>
    );
  },
};

export const States: Story = {
  render: () => (
    <div className="flex flex-col gap-6 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Button States</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton>Normal</AppleButton>
          <AppleButton disabled>Disabled</AppleButton>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Interactive States</h3>
        <p className="text-sm text-muted-foreground">Hover and click to see spring animations</p>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary">Hover Me</AppleButton>
          <AppleButton variant="secondary">Click Me</AppleButton>
          <AppleButton variant="outline">Press Me</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const IconSizes: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Icon Button Sizes</h3>
        <div className="flex items-center flex-wrap gap-3">
          <AppleButton variant="primary" size="icon-sm">+</AppleButton>
          <AppleButton variant="primary" size="icon">+</AppleButton>
          <AppleButton variant="primary" size="icon-lg">+</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const VariantCombinations: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">Variant + Size Combinations</h3>
        <div className="flex flex-wrap gap-3">
          <AppleButton variant="primary" size="sm">Small Primary</AppleButton>
          <AppleButton variant="destructive" size="lg">Large Destructive</AppleButton>
          <AppleButton variant="outline" size="icon">+</AppleButton>
          <AppleButton variant="tinted" size="sm">Tinted Small</AppleButton>
        </div>
      </div>
    </div>
  ),
};

export const AsChild: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-8">
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-muted-foreground">AsChild Prop (Slot Pattern)</h3>
        <p className="text-sm text-muted-foreground">Button styles applied to a link element</p>
        <div className="flex flex-wrap gap-3">
          <AppleButton asChild>
            <a href="#" onClick={(e) => e.preventDefault()}>Link as Button</a>
          </AppleButton>
        </div>
      </div>
    </div>
  ),
};
