import type { Meta, StoryObj } from '@storybook/react';
import { Button } from './button';

/**
 * The Button component is a versatile UI element that supports multiple variants, sizes, and states.
 * Built on top of Radix UI's Slot component with class-variance-authority for consistent styling.
 * 
 * ## Features
 * - 6 visual variants (default, destructive, outline, secondary, ghost, link)
 * - 4 size options (default, sm, lg, icon)
 * - Full accessibility support with keyboard navigation
 * - Disabled state support
 * - Custom click handlers and form integration
 * - Consistent with design system tokens
 */
const meta = {
  title: 'UI/Button',
  component: Button,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Button component is the primary interactive element in our design system. It provides consistent styling and behavior across the application.

### Usage Guidelines
- Use \`default\` variant for primary actions
- Use \`destructive\` for dangerous actions (delete, remove)
- Use \`outline\` for secondary actions
- Use \`ghost\` for subtle actions in toolbars
- Use \`link\` for navigation that looks like text
- Use \`icon\` size for buttons containing only icons

### Accessibility
- Automatically includes proper ARIA attributes
- Supports keyboard navigation (Enter/Space)
- Maintains focus management
- Screen reader compatible
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
      description: 'Visual style variant of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' },
      },
    },
    size: {
      control: 'select',
      options: ['default', 'sm', 'lg', 'icon'],
      description: 'Size of the button',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'default' },
      },
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the button is disabled',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' },
      },
    },
    onClick: {
      action: 'clicked',
      description: 'Function called when button is clicked',
      table: {
        type: { summary: '() => void' },
      },
    },
    children: {
      control: 'text',
      description: 'Content to display inside the button',
      table: {
        type: { summary: 'ReactNode' },
      },
    },
  },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: 'Button',
    variant: 'default',
  },
};

export const Destructive: Story = {
  args: {
    children: 'Delete',
    variant: 'destructive',
  },
};

export const Outline: Story = {
  args: {
    children: 'Outline',
    variant: 'outline',
  },
};

export const Secondary: Story = {
  args: {
    children: 'Secondary',
    variant: 'secondary',
  },
};

export const Ghost: Story = {
  args: {
    children: 'Ghost',
    variant: 'ghost',
  },
};

export const Link: Story = {
  args: {
    children: 'Link',
    variant: 'link',
  },
};

export const Small: Story = {
  args: {
    children: 'Small Button',
    size: 'sm',
  },
};

export const Large: Story = {
  args: {
    children: 'Large Button',
    size: 'lg',
  },
};

export const Icon: Story = {
  args: {
    children: '🔍',
    size: 'icon',
  },
};

export const Disabled: Story = {
  args: {
    children: 'Disabled',
    disabled: true,
  },
};

export const WithClick: Story = {
  args: {
    children: 'Click Me',
    onClick: () => alert('Button clicked!'),
  },
};

export const LongText: Story = {
  args: {
    children: 'This is a very long button text that might wrap or truncate depending on the container width',
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with very long text content to test text wrapping and layout behavior.',
      },
    },
  },
};

export const SingleCharacter: Story = {
  args: {
    children: 'A',
    size: 'sm',
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with minimal content to test minimum size constraints.',
      },
    },
  },
};

export const EmptyButton: Story = {
  args: {
    children: '',
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with no content - should maintain minimum height and padding.',
      },
    },
  },
};

export const WithEmoji: Story = {
  args: {
    children: '🚀 Launch',
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with emoji content to test unicode character support.',
      },
    },
  },
};

export const MultilineText: Story = {
  args: {
    children: 'Line 1\nLine 2\nLine 3',
  },
  parameters: {
    docs: {
      description: {
        story: 'Button with multiline text (newlines) to test text handling.',
      },
    },
  },
};

export const Loading: Story = {
  render: () => (
    <Button disabled>
      <span className="mr-2">⏳</span>
      Loading...
    </Button>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Button in loading state with spinner icon.',
      },
    },
  },
};

export const WithIcon: Story = {
  render: () => (
    <Button>
      <span className="mr-2">📁</span>
      Open File
    </Button>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Button with icon and text content.',
      },
    },
  },
};
