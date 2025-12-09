import type { Meta, StoryObj } from '@storybook/react'
import { Tooltip, TooltipTrigger, TooltipContent } from './tooltip'
import { Button } from './button'

const meta = {
  title: 'Components/Tooltip',
  component: TooltipContent,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    side: {
      control: 'select',
      options: ['top', 'right', 'bottom', 'left'],
      description: 'The preferred side of the trigger to render against',
    },
    sideOffset: {
      control: 'number',
      description: 'The distance in pixels from the trigger',
    },
    className: {
      control: 'text',
      description: 'Custom className for the tooltip content',
    },
    arrowClassName: {
      control: 'text',
      description: 'Custom className for the tooltip arrow. Defaults to "bg-primary fill-primary" when not provided.',
    },
  },
} satisfies Meta<typeof TooltipContent>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: (args) => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover me</Button>
      </TooltipTrigger>
      <TooltipContent {...args}>
        Default tooltip with primary arrow
      </TooltipContent>
    </Tooltip>
  ),
  args: {
    side: 'top',
    sideOffset: 4,
  },
}

export const NeutralStyle: Story = {
  render: (args) => (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="outline">Hover me</Button>
      </TooltipTrigger>
      <TooltipContent {...args}>
        Neutral tooltip with white arrow
      </TooltipContent>
    </Tooltip>
  ),
  args: {
    side: 'top',
    sideOffset: 4,
    className: 'bg-white text-neutral-900 rounded-md shadow-sm border border-neutral-200 px-2 py-1 text-xs',
    arrowClassName: 'bg-white fill-white',
  },
}

export const DarkModeResponsive: Story = {
  render: (args) => (
    <div className="flex gap-8">
      <div className="p-8 bg-white rounded-lg">
        <p className="text-sm text-neutral-500 mb-4">Light Mode</p>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Hover me</Button>
          </TooltipTrigger>
          <TooltipContent {...args}>
            Responsive tooltip
          </TooltipContent>
        </Tooltip>
      </div>
      <div className="dark p-8 bg-neutral-900 rounded-lg">
        <p className="text-sm text-neutral-400 mb-4">Dark Mode</p>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Hover me</Button>
          </TooltipTrigger>
          <TooltipContent {...args}>
            Responsive tooltip
          </TooltipContent>
        </Tooltip>
      </div>
    </div>
  ),
  args: {
    side: 'bottom',
    sideOffset: 4,
    className: 'bg-white text-neutral-900 dark:bg-neutral-800 dark:text-neutral-50 rounded-md shadow-sm border border-neutral-200 dark:border-neutral-700 px-2 py-1 text-xs',
    arrowClassName: 'bg-white fill-white dark:bg-neutral-800 dark:fill-neutral-800',
  },
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates responsive tooltip styling that adapts to light and dark modes using Tailwind dark: prefix classes.',
      },
    },
  },
}

export const AllSides: Story = {
  render: () => (
    <div className="flex flex-col items-center gap-16 py-16">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Top</Button>
        </TooltipTrigger>
        <TooltipContent side="top" sideOffset={4}>
          Tooltip on top
        </TooltipContent>
      </Tooltip>
      
      <div className="flex gap-32">
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Left</Button>
          </TooltipTrigger>
          <TooltipContent side="left" sideOffset={4}>
            Tooltip on left
          </TooltipContent>
        </Tooltip>
        
        <Tooltip>
          <TooltipTrigger asChild>
            <Button variant="outline">Right</Button>
          </TooltipTrigger>
          <TooltipContent side="right" sideOffset={4}>
            Tooltip on right
          </TooltipContent>
        </Tooltip>
      </div>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Bottom</Button>
        </TooltipTrigger>
        <TooltipContent side="bottom" sideOffset={4}>
          Tooltip on bottom
        </TooltipContent>
      </Tooltip>
    </div>
  ),
}

export const CustomArrowColors: Story = {
  render: () => (
    <div className="flex gap-8">
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Primary (default)</Button>
        </TooltipTrigger>
        <TooltipContent side="bottom" sideOffset={4}>
          Default primary arrow
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">White</Button>
        </TooltipTrigger>
        <TooltipContent 
          side="bottom" 
          sideOffset={4}
          className="bg-white text-neutral-900 border border-neutral-200"
          arrowClassName="bg-white fill-white"
        >
          White arrow
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Success</Button>
        </TooltipTrigger>
        <TooltipContent 
          side="bottom" 
          sideOffset={4}
          className="bg-green-500 text-white"
          arrowClassName="bg-green-500 fill-green-500"
        >
          Success arrow
        </TooltipContent>
      </Tooltip>
      
      <Tooltip>
        <TooltipTrigger asChild>
          <Button variant="outline">Warning</Button>
        </TooltipTrigger>
        <TooltipContent 
          side="bottom" 
          sideOffset={4}
          className="bg-amber-500 text-white"
          arrowClassName="bg-amber-500 fill-amber-500"
        >
          Warning arrow
        </TooltipContent>
      </Tooltip>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Demonstrates how the arrowClassName prop can be used to match the arrow color with different tooltip background colors.',
      },
    },
  },
}
