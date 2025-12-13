import type { Meta, StoryObj } from '@storybook/react'
import { Button } from './button'
import { Input } from './input'
import { Label } from './label'
import { Popover, PopoverContent, PopoverTrigger } from './popover'

const meta = {
  title: 'Components/Popover',
  component: Popover,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Popover>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Open Popover</Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="grid gap-4">
          <div className="space-y-2">
            <h4 className="font-medium leading-none">Dimensions</h4>
            <p className="text-sm text-muted-foreground">
              Set the dimensions for the layer.
            </p>
          </div>
          <div className="grid gap-2">
            <div className="grid grid-cols-3 items-center gap-4">
              <Label htmlFor="width">Width</Label>
              <Input id="width" defaultValue="100%" className="col-span-2 h-8" />
            </div>
            <div className="grid grid-cols-3 items-center gap-4">
              <Label htmlFor="maxWidth">Max. width</Label>
              <Input id="maxWidth" defaultValue="300px" className="col-span-2 h-8" />
            </div>
            <div className="grid grid-cols-3 items-center gap-4">
              <Label htmlFor="height">Height</Label>
              <Input id="height" defaultValue="25px" className="col-span-2 h-8" />
            </div>
            <div className="grid grid-cols-3 items-center gap-4">
              <Label htmlFor="maxHeight">Max. height</Label>
              <Input id="maxHeight" defaultValue="none" className="col-span-2 h-8" />
            </div>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  ),
}

export const Simple: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Info</Button>
      </PopoverTrigger>
      <PopoverContent>
        <p className="text-sm">
          This is a simple popover with some informational text.
        </p>
      </PopoverContent>
    </Popover>
  ),
}

export const AlignStart: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Align Start</Button>
      </PopoverTrigger>
      <PopoverContent align="start">
        <p className="text-sm">
          This popover is aligned to the start of the trigger.
        </p>
      </PopoverContent>
    </Popover>
  ),
}

export const AlignEnd: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">Align End</Button>
      </PopoverTrigger>
      <PopoverContent align="end">
        <p className="text-sm">
          This popover is aligned to the end of the trigger.
        </p>
      </PopoverContent>
    </Popover>
  ),
}

export const AllAlignments: Story = {
  render: () => (
    <div className="flex gap-4">
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline">Start</Button>
        </PopoverTrigger>
        <PopoverContent align="start" className="w-48">
          <p className="text-sm">Aligned to start</p>
        </PopoverContent>
      </Popover>
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline">Center</Button>
        </PopoverTrigger>
        <PopoverContent align="center" className="w-48">
          <p className="text-sm">Aligned to center</p>
        </PopoverContent>
      </Popover>
      <Popover>
        <PopoverTrigger asChild>
          <Button variant="outline">End</Button>
        </PopoverTrigger>
        <PopoverContent align="end" className="w-48">
          <p className="text-sm">Aligned to end</p>
        </PopoverContent>
      </Popover>
    </div>
  ),
}

export const WithForm: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button>Subscribe</Button>
      </PopoverTrigger>
      <PopoverContent className="w-80">
        <div className="grid gap-4">
          <div className="space-y-2">
            <h4 className="font-medium leading-none">Newsletter</h4>
            <p className="text-sm text-muted-foreground">
              Subscribe to our newsletter for updates.
            </p>
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" placeholder="Enter your email" />
          </div>
          <Button size="sm">Subscribe</Button>
        </div>
      </PopoverContent>
    </Popover>
  ),
}

export const UserProfile: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="ghost" className="size-10 rounded-full p-0">
          <span className="flex size-full items-center justify-center rounded-full bg-muted">
            JD
          </span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64" align="end">
        <div className="grid gap-4">
          <div className="flex items-center gap-4">
            <span className="flex size-12 items-center justify-center rounded-full bg-muted text-lg font-medium">
              JD
            </span>
            <div>
              <p className="font-medium">John Doe</p>
              <p className="text-sm text-muted-foreground">john@example.com</p>
            </div>
          </div>
          <div className="grid gap-1">
            <Button variant="ghost" className="justify-start">Profile</Button>
            <Button variant="ghost" className="justify-start">Settings</Button>
            <Button variant="ghost" className="justify-start text-destructive">
              Sign out
            </Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  ),
}

export const ColorPicker: Story = {
  render: () => (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" className="w-[200px] justify-start">
          <div className="size-4 rounded bg-blue-500 mr-2" />
          Pick a color
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-64">
        <div className="grid gap-4">
          <h4 className="font-medium leading-none">Colors</h4>
          <div className="grid grid-cols-5 gap-2">
            {['red', 'orange', 'yellow', 'green', 'blue', 'purple', 'pink', 'gray', 'black', 'white'].map((color) => (
              <button
                key={color}
                className={`size-8 rounded-md border ${color === 'white' ? 'bg-white' : color === 'black' ? 'bg-black' : `bg-${color}-500`}`}
                style={{ backgroundColor: color }}
              />
            ))}
          </div>
        </div>
      </PopoverContent>
    </Popover>
  ),
}
