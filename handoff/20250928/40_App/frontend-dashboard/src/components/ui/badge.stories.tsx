import type { Meta, StoryObj } from '@storybook/react';
import { Badge } from './badge';

/**
 * The Badge component is a small label for displaying status, counts, or categories.
 * It provides visual emphasis for important information in a compact format.
 * 
 * ## Features
 * - 4 visual variants (default, secondary, destructive, outline)
 * - Compact size for inline use
 * - Support for icons and counts
 * - Customizable with Tailwind classes
 * - Can be made interactive with click handlers
 */
const meta = {
  title: 'UI/Badge',
  component: Badge,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Badge component is used to highlight status, counts, or categories in a compact visual format. It's perfect for displaying metadata or drawing attention to specific information.

### Usage Guidelines
- Use for status indicators (active, pending, error)
- Display counts or notifications
- Tag items with categories
- Keep text short and concise
- Choose appropriate variant for the context
- Use sparingly to maintain visual hierarchy

### Accessibility
- Semantic HTML structure
- Screen reader compatible
- Sufficient color contrast
- Can be made focusable if interactive
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'secondary', 'destructive', 'outline'],
      description: 'Visual style variant of the badge',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' },
      },
    },
    children: {
      control: 'text',
      description: 'Content to display in the badge',
      table: {
        type: { summary: 'ReactNode' },
      },
    },
  },
} satisfies Meta<typeof Badge>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Badge',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
};

export const Destructive: Story = {
  args: {
    children: 'Destructive',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const WithIcon: Story = {
  render: () => (
    <Badge>
      <span className="mr-1">✓</span>
      Success
    </Badge>
  ),
};

export const StatusBadges: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge variant="default">Active</Badge>
      <Badge variant="secondary">Pending</Badge>
      <Badge variant="destructive">Error</Badge>
      <Badge variant="outline">Draft</Badge>
    </div>
  ),
};

export const Sizes: Story = {
  render: () => (
    <div className="flex items-center gap-2">
      <Badge className="text-xs">Small</Badge>
      <Badge>Medium</Badge>
      <Badge className="text-base px-3 py-1">Large</Badge>
    </div>
  ),
};

export const WithCount: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge>New 3</Badge>
      <Badge variant="destructive">Errors 12</Badge>
      <Badge variant="secondary">Pending 5</Badge>
    </div>
  ),
};

export const Clickable: Story = {
  render: () => (
    <Badge 
      className="cursor-pointer hover:opacity-80"
      onClick={() => alert('Badge clicked!')}
    >
      Click me
    </Badge>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Interactive badge with click handler.',
      },
    },
  },
};

export const LongText: Story = {
  args: {
    children: 'This is a very long badge text that might wrap',
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with long text to test wrapping behavior.',
      },
    },
  },
};

export const SingleCharacter: Story = {
  args: {
    children: '1',
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with minimal single character content.',
      },
    },
  },
};

export const WithEmoji: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge>🔥 Hot</Badge>
      <Badge variant="secondary">⭐ Featured</Badge>
      <Badge variant="destructive">❌ Error</Badge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Badges with emoji icons for visual emphasis.',
      },
    },
  },
};

export const Numbers: Story = {
  render: () => (
    <div className="flex gap-2">
      <Badge>1</Badge>
      <Badge variant="secondary">99+</Badge>
      <Badge variant="destructive">-5</Badge>
      <Badge variant="outline">0</Badge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Badges displaying numeric values.',
      },
    },
  },
};

export const Empty: Story = {
  args: {
    children: '',
  },
  parameters: {
    docs: {
      description: {
        story: 'Badge with no content - should maintain minimum size.',
      },
    },
  },
};

export const MultipleBadges: Story = {
  render: () => (
    <div className="flex flex-wrap gap-2 max-w-md">
      <Badge>React</Badge>
      <Badge variant="secondary">TypeScript</Badge>
      <Badge variant="outline">Tailwind</Badge>
      <Badge>Vite</Badge>
      <Badge variant="secondary">Storybook</Badge>
      <Badge variant="outline">ESLint</Badge>
      <Badge>Prettier</Badge>
      <Badge variant="secondary">pnpm</Badge>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple badges used as tags with wrapping.',
      },
    },
  },
};

export const InText: Story = {
  render: () => (
    <p className="max-w-md">
      This is a paragraph with an inline <Badge>badge</Badge> component. It should flow naturally with the surrounding text and maintain proper spacing.
    </p>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Badge used inline within text content.',
      },
    },
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-sm font-medium mb-2">Default</h3>
        <div className="flex gap-2">
          <Badge>Active</Badge>
          <Badge>New</Badge>
          <Badge>Featured</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Secondary</h3>
        <div className="flex gap-2">
          <Badge variant="secondary">Pending</Badge>
          <Badge variant="secondary">Draft</Badge>
          <Badge variant="secondary">Review</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Destructive</h3>
        <div className="flex gap-2">
          <Badge variant="destructive">Error</Badge>
          <Badge variant="destructive">Failed</Badge>
          <Badge variant="destructive">Blocked</Badge>
        </div>
      </div>
      <div>
        <h3 className="text-sm font-medium mb-2">Outline</h3>
        <div className="flex gap-2">
          <Badge variant="outline">Info</Badge>
          <Badge variant="outline">Note</Badge>
          <Badge variant="outline">Optional</Badge>
        </div>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Comprehensive showcase of all badge variants with examples.',
      },
    },
  },
};
