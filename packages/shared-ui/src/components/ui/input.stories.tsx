import type { Meta, StoryObj } from '@storybook/react'
import { Mail, Search as SearchIcon, Eye, EyeOff } from 'lucide-react'
import { Input } from './input'
import { Label } from './label'
import { Button } from './button'
import { useState } from 'react'

const meta = {
  title: 'Components/Input',
  component: Input,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search', 'date', 'time'],
      description: 'The input type',
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input is disabled',
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text',
    },
  },
} satisfies Meta<typeof Input>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
}

export const WithLabel: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <Label htmlFor="email">Email</Label>
      <Input id="email" type="email" placeholder="Enter your email" />
    </div>
  ),
}

export const Email: Story = {
  args: {
    type: 'email',
    placeholder: 'email@example.com',
  },
}

export const Password: Story = {
  args: {
    type: 'password',
    placeholder: 'Enter password',
  },
}

export const Number: Story = {
  args: {
    type: 'number',
    placeholder: '0',
  },
}

export const Search: Story = {
  render: () => (
    <div className="relative w-[300px]">
      <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
      <Input className="pl-9" placeholder="Search..." />
    </div>
  ),
}

export const WithIcon: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div className="relative">
        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input className="pl-9" type="email" placeholder="Email" />
      </div>
      <div className="relative">
        <SearchIcon className="absolute left-3 top-1/2 -translate-y-1/2 size-4 text-muted-foreground" />
        <Input className="pl-9" placeholder="Search" />
      </div>
    </div>
  ),
}

export const PasswordWithToggle: Story = {
  render: () => {
    const [showPassword, setShowPassword] = useState(false)
    return (
      <div className="relative w-[300px]">
        <Input
          type={showPassword ? 'text' : 'password'}
          placeholder="Enter password"
          className="pr-10"
        />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
          onClick={() => setShowPassword(!showPassword)}
        >
          {showPassword ? (
            <EyeOff className="size-4 text-muted-foreground" />
          ) : (
            <Eye className="size-4 text-muted-foreground" />
          )}
        </Button>
      </div>
    )
  },
}

export const Disabled: Story = {
  args: {
    disabled: true,
    placeholder: 'Disabled input',
    value: 'Cannot edit this',
  },
}

export const Invalid: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <Label htmlFor="invalid-email">Email</Label>
      <Input
        id="invalid-email"
        type="email"
        placeholder="email@example.com"
        aria-invalid="true"
        defaultValue="invalid-email"
      />
      <p className="text-sm text-destructive">Please enter a valid email address</p>
    </div>
  ),
}

export const WithHelperText: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <Label htmlFor="username">Username</Label>
      <Input id="username" placeholder="johndoe" />
      <p className="text-sm text-muted-foreground">
        Choose a unique username for your account
      </p>
    </div>
  ),
}

export const File: Story = {
  render: () => (
    <div className="w-[300px] space-y-2">
      <Label htmlFor="file">Upload file</Label>
      <Input id="file" type="file" />
    </div>
  ),
}

export const AllTypes: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div className="space-y-2">
        <Label>Text</Label>
        <Input type="text" placeholder="Text input" />
      </div>
      <div className="space-y-2">
        <Label>Email</Label>
        <Input type="email" placeholder="email@example.com" />
      </div>
      <div className="space-y-2">
        <Label>Password</Label>
        <Input type="password" placeholder="Password" />
      </div>
      <div className="space-y-2">
        <Label>Number</Label>
        <Input type="number" placeholder="0" />
      </div>
      <div className="space-y-2">
        <Label>Tel</Label>
        <Input type="tel" placeholder="+1 (555) 000-0000" />
      </div>
      <div className="space-y-2">
        <Label>URL</Label>
        <Input type="url" placeholder="https://example.com" />
      </div>
      <div className="space-y-2">
        <Label>Date</Label>
        <Input type="date" />
      </div>
      <div className="space-y-2">
        <Label>Time</Label>
        <Input type="time" />
      </div>
    </div>
  ),
}

export const FormExample: Story = {
  render: () => (
    <div className="w-[400px] space-y-4">
      <div className="space-y-2">
        <Label htmlFor="form-name">Full Name</Label>
        <Input id="form-name" placeholder="John Doe" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="form-email">Email</Label>
        <Input id="form-email" type="email" placeholder="john@example.com" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="form-phone">Phone</Label>
        <Input id="form-phone" type="tel" placeholder="+1 (555) 000-0000" />
      </div>
      <div className="space-y-2">
        <Label htmlFor="form-message">Message</Label>
        <Input id="form-message" placeholder="Your message..." />
      </div>
      <Button className="w-full">Submit</Button>
    </div>
  ),
}
