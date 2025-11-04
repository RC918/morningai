import type { Meta, StoryObj } from '@storybook/react'
import { useState } from 'react'
import { AppleSegmentedControl, AppleSegmentedControlItem } from './apple-segmented-control'
import { List, Grid, Calendar } from 'lucide-react'

const meta = {
  title: 'Apple Design System/AppleSegmentedControl',
  component: AppleSegmentedControl,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
# AppleSegmentedControl

iOS-style segmented control for switching between views or filtering content.

## Features

- **iOS Design**: Authentic iOS segmented control styling
- **Smooth Animation**: Sliding active indicator with spring physics
- **Haptic Feedback**: Visual haptic feedback simulation
- **Keyboard Navigation**: Full keyboard support (Arrow keys, Enter, Space)
- **Accessibility**: Complete ARIA support
- **Responsive**: Adapts to content width

## Design Principles

Based on Apple's Human Interface Guidelines:
- Clear visual feedback for active state
- Smooth, natural animations
- Minimal, focused design
- Accessible by default

## Usage

\`\`\`tsx
import { AppleSegmentedControl, AppleSegmentedControlItem } from '@/components/ui/apple-segmented-control'

function FilterView() {
  const [filter, setFilter] = useState('all')
  
  return (
    <AppleSegmentedControl value={filter} onValueChange={setFilter}>
      <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
      <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
      <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
    </AppleSegmentedControl>
  )
}
\`\`\`

## When to Use

- **View Switching**: Toggle between different views of the same data
- **Filtering**: Filter content by category or status
- **Settings**: Choose between mutually exclusive options
- **Layout Toggle**: Switch between list, grid, or other layouts

## Best Practices

- Use 2-5 segments (iOS guideline)
- Keep labels short and clear
- Use for mutually exclusive options
- Don't use for navigation between different screens
        `,
      },
    },
  },
  tags: ['autodocs'],
  args: {
    value: 'all',
    onValueChange: () => {}
  },
  argTypes: {
    value: {
      control: 'text',
      description: 'Currently selected segment value',
    },
    onValueChange: {
      action: 'valueChanged',
      description: 'Callback when segment selection changes',
    },
    size: {
      control: 'select',
      options: ['sm', 'default', 'lg'],
      description: 'Size variant of the segmented control',
    },
  },
} satisfies Meta<typeof AppleSegmentedControl>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('all')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue}>
          <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          Selected: <span className="font-semibold text-foreground">{value}</span>
        </p>
      </div>
    )
  },
}

export const TwoSegments: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('list')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue}>
          <AppleSegmentedControlItem value="list">
            <List className="w-4 h-4 mr-2" />
            List
          </AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="grid">
            <Grid className="w-4 h-4 mr-2" />
            Grid
          </AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          View mode: <span className="font-semibold text-foreground">{value}</span>
        </p>
      </div>
    )
  },
}

export const FourSegments: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('day')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue}>
          <AppleSegmentedControlItem value="day">Day</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="week">Week</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="month">Month</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="year">Year</AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          Time period: <span className="font-semibold text-foreground">{value}</span>
        </p>
      </div>
    )
  },
}

export const WithIcons: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('list')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue}>
          <AppleSegmentedControlItem value="list">
            <List className="w-4 h-4" />
          </AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="grid">
            <Grid className="w-4 h-4" />
          </AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="calendar">
            <Calendar className="w-4 h-4" />
          </AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          Layout: <span className="font-semibold text-foreground">{value}</span>
        </p>
      </div>
    )
  },
}

export const SmallSize: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('all')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue} size="sm">
          <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          Small size variant
        </p>
      </div>
    )
  },
}

export const LargeSize: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('all')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue} size="lg">
          <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          Large size variant
        </p>
      </div>
    )
  },
}

export const WithDisabledSegment: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('all')
    
    return (
      <div className="space-y-4">
        <AppleSegmentedControl value={value} onValueChange={setValue}>
          <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
          <AppleSegmentedControlItem value="completed" disabled>
            Completed
          </AppleSegmentedControlItem>
        </AppleSegmentedControl>
        
        <p className="text-sm text-muted-foreground text-center">
          "Completed" segment is disabled
        </p>
      </div>
    )
  },
}

export const InCard: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('overview')
    
    return (
      <div className="w-[400px] bg-card rounded-xl p-6 shadow-lg">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">Dashboard</h3>
          <AppleSegmentedControl value={value} onValueChange={setValue} size="sm">
            <AppleSegmentedControlItem value="overview">Overview</AppleSegmentedControlItem>
            <AppleSegmentedControlItem value="details">Details</AppleSegmentedControlItem>
          </AppleSegmentedControl>
        </div>
        
        <div className="space-y-3">
          <div className="h-20 bg-accent/30 rounded-lg" />
          <div className="h-20 bg-accent/30 rounded-lg" />
          <div className="h-20 bg-accent/30 rounded-lg" />
        </div>
      </div>
    )
  },
}

export const FilterExample: Story = {
  args: {},
  render: () => {
    const [status, setStatus] = useState('all')
    const [priority, setPriority] = useState('all')
    
    return (
      <div className="w-[500px] space-y-6">
        <div className="bg-card rounded-xl p-6 shadow-lg">
          <h3 className="text-lg font-semibold mb-4">Task Filters</h3>
          
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <AppleSegmentedControl value={status} onValueChange={setStatus}>
                <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
                <AppleSegmentedControlItem value="todo">To Do</AppleSegmentedControlItem>
                <AppleSegmentedControlItem value="progress">In Progress</AppleSegmentedControlItem>
                <AppleSegmentedControlItem value="done">Done</AppleSegmentedControlItem>
              </AppleSegmentedControl>
            </div>
            
            <div>
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <AppleSegmentedControl value={priority} onValueChange={setPriority}>
                <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
                <AppleSegmentedControlItem value="low">Low</AppleSegmentedControlItem>
                <AppleSegmentedControlItem value="medium">Medium</AppleSegmentedControlItem>
                <AppleSegmentedControlItem value="high">High</AppleSegmentedControlItem>
              </AppleSegmentedControl>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-accent/20 rounded-lg">
            <p className="text-sm text-muted-foreground">
              Showing tasks: <span className="font-semibold text-foreground">{status}</span> status, 
              <span className="font-semibold text-foreground"> {priority}</span> priority
            </p>
          </div>
        </div>
      </div>
    )
  },
}

export const DarkMode: Story = {
  args: {},
  render: () => {
    const [value, setValue] = useState('all')
    
    return (
      <div className="dark p-8 bg-background rounded-xl">
        <div className="space-y-4">
          <AppleSegmentedControl value={value} onValueChange={setValue}>
            <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
            <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
            <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
          </AppleSegmentedControl>
          
          <p className="text-sm text-muted-foreground text-center">
            Dark mode with proper contrast
          </p>
        </div>
      </div>
    )
  },
}
