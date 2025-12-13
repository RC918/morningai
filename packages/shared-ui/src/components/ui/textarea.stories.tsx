import type { Meta, StoryObj } from '@storybook/react'
import { Textarea } from './textarea'
import { Label } from './label'

const meta = {
  title: 'Components/Textarea',
  component: Textarea,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the textarea is disabled',
    },
    rows: {
      control: 'number',
      description: 'Number of visible text lines',
    },
  },
} satisfies Meta<typeof Textarea>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    placeholder: 'Type your message here.',
    'aria-label': 'Message input',
  },
}

export const WithLabel: Story = {
  render: () => (
    <div className="grid w-full gap-1.5">
      <Label htmlFor="message">Your message</Label>
      <Textarea placeholder="Type your message here." id="message" />
    </div>
  ),
}

export const WithText: Story = {
  render: () => (
    <div className="grid w-full gap-1.5">
      <Label htmlFor="message-2">Your Message</Label>
      <Textarea placeholder="Type your message here." id="message-2" />
      <p className="text-sm text-muted-foreground">
        Your message will be copied to the support team.
      </p>
    </div>
  ),
}

export const Disabled: Story = {
  args: {
    placeholder: 'This textarea is disabled.',
    disabled: true,
    'aria-label': 'Disabled textarea',
  },
}

export const WithDefaultValue: Story = {
  args: {
    defaultValue: 'This is some default text that appears in the textarea.',
    'aria-label': 'Textarea with default value',
  },
}

export const CustomRows: Story = {
  render: () => (
    <div className="flex flex-col gap-4 w-[400px]">
      <div className="grid gap-1.5">
        <Label htmlFor="small">Small (2 rows)</Label>
        <Textarea id="small" placeholder="Small textarea" rows={2} />
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="medium">Medium (4 rows)</Label>
        <Textarea id="medium" placeholder="Medium textarea" rows={4} />
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="large">Large (8 rows)</Label>
        <Textarea id="large" placeholder="Large textarea" rows={8} />
      </div>
    </div>
  ),
}

export const FormExample: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div className="grid gap-1.5">
        <Label htmlFor="bio">Bio</Label>
        <Textarea
          id="bio"
          placeholder="Tell us a little bit about yourself"
          className="resize-none"
        />
        <p className="text-sm text-muted-foreground">
          You can @mention other users and organizations.
        </p>
      </div>
    </div>
  ),
}
