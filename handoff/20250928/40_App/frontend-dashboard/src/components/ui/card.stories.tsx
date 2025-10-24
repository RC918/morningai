import type { Meta, StoryObj } from '@storybook/react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from './card';
import { Button } from './button';
import { Badge } from './badge';

/**
 * The Card component is a versatile container for grouping related content and actions.
 * It provides a consistent visual structure with optional header, content, and footer sections.
 * 
 * ## Features
 * - Flexible composition with sub-components
 * - Optional header with title and description
 * - Content area for any type of content
 * - Optional footer for actions
 * - Consistent spacing and borders
 * - Responsive design
 */
const meta = {
  title: 'UI/Card',
  component: Card,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Card component is a foundational layout element that groups related information and actions. It's composed of multiple sub-components for maximum flexibility.

### Sub-components
- **Card**: Main container with border and shadow
- **CardHeader**: Optional header section
- **CardTitle**: Title text with appropriate sizing
- **CardDescription**: Subtitle or description text
- **CardContent**: Main content area
- **CardFooter**: Optional footer for actions

### Usage Guidelines
- Use for grouping related content and actions
- Include a title to describe the card's purpose
- Use description for additional context
- Place primary actions in the footer
- Keep content focused and concise
- Consider card width based on content

### Accessibility
- Semantic HTML structure
- Proper heading hierarchy
- Focus management for interactive elements
- Screen reader compatible
        `,
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Card Title</CardTitle>
        <CardDescription>Card Description</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card Content</p>
      </CardContent>
      <CardFooter>
        <Button>Action</Button>
      </CardFooter>
    </Card>
  ),
};

export const WithoutFooter: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Notification</CardTitle>
        <CardDescription>You have 3 unread messages.</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Check your inbox for new updates.</p>
      </CardContent>
    </Card>
  ),
};

export const WithoutHeader: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardContent className="pt-6">
        <p>This card has no header, just content.</p>
      </CardContent>
    </Card>
  ),
};

export const WithList: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Your latest actions</CardDescription>
      </CardHeader>
      <CardContent>
        <ul className="space-y-2">
          <li>✓ Completed task A</li>
          <li>✓ Updated profile</li>
          <li>✓ Sent message</li>
        </ul>
      </CardContent>
    </Card>
  ),
};

export const WithMultipleButtons: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Confirm Action</CardTitle>
        <CardDescription>Are you sure you want to proceed?</CardDescription>
      </CardHeader>
      <CardContent>
        <p>This action cannot be undone.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Cancel</Button>
        <Button>Confirm</Button>
      </CardFooter>
    </Card>
  ),
};

export const Wide: Story = {
  render: () => (
    <Card className="w-[600px]">
      <CardHeader>
        <CardTitle>Wide Card</CardTitle>
        <CardDescription>This card is wider than the default</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can span across a wider area for more complex layouts.</p>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with wider width for more complex layouts.',
      },
    },
  },
};

export const LongTitle: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>This is a very long card title that might wrap to multiple lines depending on the card width</CardTitle>
        <CardDescription>Testing title wrapping behavior</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Card content goes here.</p>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with very long title to test text wrapping.',
      },
    },
  },
};

export const LongContent: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>Article Preview</CardTitle>
        <CardDescription>Latest blog post</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">
          Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.
        </p>
      </CardContent>
      <CardFooter>
        <Button>Read More</Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with long text content to test content overflow.',
      },
    },
  },
};

export const MinimalContent: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <CardTitle>A</CardTitle>
        <CardDescription>B</CardDescription>
      </CardHeader>
      <CardContent>
        <p>C</p>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with minimal single-character content.',
      },
    },
  },
};

export const WithBadges: Story = {
  render: () => (
    <Card className="w-[350px]">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle>Project Status</CardTitle>
          <Badge>Active</Badge>
        </div>
        <CardDescription>Current project information</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between">
            <span>Tasks completed:</span>
            <Badge variant="secondary">12/20</Badge>
          </div>
          <div className="flex justify-between">
            <span>Priority:</span>
            <Badge variant="destructive">High</Badge>
          </div>
        </div>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with Badge components for status indicators.',
      },
    },
  },
};

export const Narrow: Story = {
  render: () => (
    <Card className="w-[200px]">
      <CardHeader>
        <CardTitle>Narrow</CardTitle>
        <CardDescription>Small card</CardDescription>
      </CardHeader>
      <CardContent>
        <p className="text-sm">Compact layout</p>
      </CardContent>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card with narrow width to test minimum size constraints.',
      },
    },
  },
};

export const FullWidth: Story = {
  render: () => (
    <Card className="w-full max-w-4xl">
      <CardHeader>
        <CardTitle>Full Width Card</CardTitle>
        <CardDescription>This card spans the full width of its container</CardDescription>
      </CardHeader>
      <CardContent>
        <p>Content can be displayed across the full width, useful for dashboard layouts or detailed information displays.</p>
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button variant="outline">Secondary Action</Button>
        <Button>Primary Action</Button>
      </CardFooter>
    </Card>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Card that spans full width with maximum width constraint.',
      },
    },
  },
};

export const StackedCards: Story = {
  render: () => (
    <div className="space-y-4 w-[350px]">
      <Card>
        <CardHeader>
          <CardTitle>Card 1</CardTitle>
          <CardDescription>First card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for first card</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 2</CardTitle>
          <CardDescription>Second card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for second card</p>
        </CardContent>
      </Card>
      <Card>
        <CardHeader>
          <CardTitle>Card 3</CardTitle>
          <CardDescription>Third card in stack</CardDescription>
        </CardHeader>
        <CardContent>
          <p>Content for third card</p>
        </CardContent>
      </Card>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple cards stacked vertically with consistent spacing.',
      },
    },
  },
};
