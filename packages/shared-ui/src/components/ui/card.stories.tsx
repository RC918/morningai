import type { Meta, StoryObj } from '@storybook/react'
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter, CardAction } from './card'
import { Button } from './button'
import { Badge } from './badge'

const meta = {
  title: 'Components/Card',
  component: Card,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    interactive: {
      control: 'boolean',
      description: 'Whether the card has hover effects and cursor pointer',
    },
  },
} satisfies Meta<typeof Card>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card description goes here</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This is the main content of the card.</p>
      </CardContent>
    </Card>
  ),
}

export const WithFooter: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card with Footer</CardTitle>
        <CardDescription>This card includes a footer section</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content with additional information.</p>
      </CardContent>
      <CardFooter className="border-t">
        <Button variant="outline" size="sm">Cancel</Button>
        <Button size="sm" className="ml-auto">Save</Button>
      </CardFooter>
    </Card>
  ),
}

export const WithAction: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Card with Action</CardTitle>
        <CardDescription>This card has an action button in the header</CardDescription>
        <CardAction>
          <Button variant="ghost" size="sm">Edit</Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p>The action button is positioned in the top-right corner.</p>
      </CardContent>
    </Card>
  ),
}

export const Interactive: Story = {
  render: () => (
    <Card interactive>
      <CardHeader>
        <CardTitle>Interactive Card</CardTitle>
        <CardDescription>This card has hover effects</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Hover over this card to see the interactive effect.</p>
      </CardContent>
    </Card>
  ),
}

export const WithBadge: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Task Status</CardTitle>
        <CardDescription>Current progress on the project</CardDescription>
        <CardAction>
          <Badge variant="secondary">In Progress</Badge>
        </CardAction>
      </CardHeader>
      <CardContent>
        <p>This card demonstrates using a badge in the action slot.</p>
      </CardContent>
    </Card>
  ),
}

export const ContentOnly: Story = {
  render: () => (
    <Card>
      <CardContent>
        <p>A simple card with only content, no header or footer.</p>
      </CardContent>
    </Card>
  ),
}

export const ComplexLayout: Story = {
  render: () => (
    <Card>
      <CardHeader>
        <CardTitle>Project Dashboard</CardTitle>
        <CardDescription>Overview of your current projects</CardDescription>
        <CardAction>
          <Button variant="ghost" size="sm">View All</Button>
        </CardAction>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Active Projects</span>
            <Badge>12</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Completed</span>
            <Badge variant="secondary">45</Badge>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">Pending Review</span>
            <Badge variant="outline">8</Badge>
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t">
        <Button variant="outline" size="sm">Export</Button>
        <Button size="sm" className="ml-auto">New Project</Button>
      </CardFooter>
    </Card>
  ),
}

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Card>
        <CardHeader>
          <CardTitle>Default Card</CardTitle>
          <CardDescription>Standard card layout</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Basic card with header and content.</p>
        </CardContent>
      </Card>
      
      <Card interactive>
        <CardHeader>
          <CardTitle>Interactive Card</CardTitle>
          <CardDescription>With hover effects</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Hover to see the effect.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>With Action</CardTitle>
          <CardDescription>Action button in header</CardDescription>
          <CardAction>
            <Button variant="ghost" size="sm">Edit</Button>
          </CardAction>
        </CardHeader>
        <CardContent>
          <p>Card with action button.</p>
        </CardContent>
      </Card>
      
      <Card>
        <CardHeader>
          <CardTitle>With Footer</CardTitle>
          <CardDescription>Includes footer section</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Card with footer actions.</p>
        </CardContent>
        <CardFooter className="border-t">
          <Button variant="outline" size="sm">Cancel</Button>
          <Button size="sm" className="ml-auto">Save</Button>
        </CardFooter>
      </Card>
    </div>
  ),
}
