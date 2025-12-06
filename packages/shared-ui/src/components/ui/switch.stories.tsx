import type { Meta, StoryObj } from '@storybook/react'
import { Switch } from './switch'

const meta = {
  title: 'Components/Switch',
  component: Switch,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    checked: {
      control: 'boolean',
      description: 'Whether the switch is checked (on)',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the switch is disabled',
    },
    onCheckedChange: {
      action: 'checked changed',
      description: 'Callback when the checked state changes',
    },
  },
} satisfies Meta<typeof Switch>

export default meta
type Story = StoryObj<typeof meta>

/**
 * Default unchecked (OFF) state.
 * The switch should display a visible gray background (bg-input).
 */
export const Default: Story = {
  args: {
    checked: false,
  },
}

/**
 * Checked (ON) state.
 * The switch should display a blue background (bg-primary).
 */
export const Checked: Story = {
  args: {
    checked: true,
  },
}

/**
 * Disabled unchecked state.
 * The switch should appear faded and not respond to clicks.
 */
export const DisabledUnchecked: Story = {
  args: {
    checked: false,
    disabled: true,
  },
}

/**
 * Disabled checked state.
 * The switch should appear faded with blue background.
 */
export const DisabledChecked: Story = {
  args: {
    checked: true,
    disabled: true,
  },
}

/**
 * Interactive switch that can be toggled.
 * Click to toggle between ON and OFF states.
 */
export const Interactive: Story = {
  args: {
    defaultChecked: false,
  },
}

/**
 * All switch states displayed together for visual comparison.
 * This is useful for verifying that all states render correctly,
 * especially after design token changes.
 */
export const AllStates: Story = {
  render: () => (
    <div className="flex flex-col gap-4">
      <div className="flex items-center gap-4">
        <span className="w-32 text-sm text-gray-600">OFF (default):</span>
        <Switch checked={false} />
      </div>
      <div className="flex items-center gap-4">
        <span className="w-32 text-sm text-gray-600">ON (checked):</span>
        <Switch checked={true} />
      </div>
      <div className="flex items-center gap-4">
        <span className="w-32 text-sm text-gray-600">Disabled OFF:</span>
        <Switch checked={false} disabled />
      </div>
      <div className="flex items-center gap-4">
        <span className="w-32 text-sm text-gray-600">Disabled ON:</span>
        <Switch checked={true} disabled />
      </div>
    </div>
  ),
}

/**
 * Switch with label - common usage pattern.
 */
export const WithLabel: Story = {
  render: () => (
    <div className="flex items-center gap-3">
      <Switch id="notifications" defaultChecked />
      <label htmlFor="notifications" className="text-sm font-medium">
        Enable notifications
      </label>
    </div>
  ),
}

/**
 * Form example with multiple switches.
 * Demonstrates typical settings panel usage.
 */
export const FormExample: Story = {
  render: () => (
    <div className="flex flex-col gap-4 p-4 border rounded-lg w-80">
      <h3 className="font-semibold text-lg">Settings</h3>
      <div className="flex items-center justify-between">
        <label htmlFor="email" className="text-sm">Email notifications</label>
        <Switch id="email" defaultChecked />
      </div>
      <div className="flex items-center justify-between">
        <label htmlFor="push" className="text-sm">Push notifications</label>
        <Switch id="push" />
      </div>
      <div className="flex items-center justify-between">
        <label htmlFor="sms" className="text-sm text-gray-400">SMS alerts (coming soon)</label>
        <Switch id="sms" disabled />
      </div>
    </div>
  ),
}
