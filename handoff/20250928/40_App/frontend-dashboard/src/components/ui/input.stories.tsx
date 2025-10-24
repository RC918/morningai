import type { Meta, StoryObj } from '@storybook/react';
import { Input } from './input';
import { Label } from './label';

/**
 * The Input component is a versatile form element for text entry.
 * It supports multiple input types and states for various use cases.
 * 
 * ## Features
 * - Multiple input types (text, email, password, number, etc.)
 * - Disabled state support
 * - Placeholder text
 * - Default values
 * - Error states
 * - Full accessibility support
 */
const meta = {
  title: 'UI/Input',
  component: Input,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Input component provides a consistent interface for text entry across the application. It supports various input types and states.

### Usage Guidelines
- Always pair with a Label for accessibility
- Use appropriate input type for the data (email, password, number, etc.)
- Provide clear placeholder text
- Show validation errors below the input
- Use helper text for additional context
- Disable when input is not available

### Accessibility
- Proper label associations with htmlFor/id
- Placeholder text for guidance
- Error messages announced to screen readers
- Keyboard navigation support
- Focus indicators
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    type: {
      control: 'select',
      options: ['text', 'email', 'password', 'number', 'tel', 'url', 'search'],
      description: 'The type of input field',
      table: {
        type: { summary: 'string' },
        defaultValue: { summary: 'text' },
      },
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the input is disabled',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' },
      },
    },
    placeholder: {
      control: 'text',
      description: 'Placeholder text shown when input is empty',
      table: {
        type: { summary: 'string' },
      },
    },
  },
} satisfies Meta<typeof Input>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    placeholder: 'Enter text...',
  },
};

export const WithLabel: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Email" />
    </div>
  ),
};

export const WithValue: Story = {
  args: {
    defaultValue: 'Hello World',
  },
};

export const Disabled: Story = {
  args: {
    placeholder: 'Disabled input',
    disabled: true,
  },
};

export const Password: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="password">Password</Label>
      <Input type="password" id="password" placeholder="Enter password" />
    </div>
  ),
};

export const Email: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-input">Email</Label>
      <Input type="email" id="email-input" placeholder="name@example.com" />
    </div>
  ),
};

export const Number: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="number">Number</Label>
      <Input type="number" id="number" placeholder="0" />
    </div>
  ),
};

export const Search: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="search">Search</Label>
      <Input type="search" id="search" placeholder="Search..." />
    </div>
  ),
};

export const WithHelperText: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-helper">Email</Label>
      <Input type="email" id="email-helper" placeholder="Email" />
      <p className="text-sm text-muted-foreground">
        We'll never share your email with anyone else.
      </p>
    </div>
  ),
};

export const WithError: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email-error">Email</Label>
      <Input 
        type="email" 
        id="email-error" 
        placeholder="Email" 
        className="border-red-500"
      />
      <p className="text-sm text-red-500">
        Please enter a valid email address.
      </p>
    </div>
  ),
};

export const File: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="picture">Picture</Label>
      <Input id="picture" type="file" />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'File input for uploading files.',
      },
    },
  },
};

export const LongPlaceholder: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="long-placeholder">Input</Label>
      <Input 
        id="long-placeholder" 
        placeholder="This is a very long placeholder text that might get truncated depending on the input width" 
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input with very long placeholder text to test truncation.',
      },
    },
  },
};

export const LongValue: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="long-value">Input</Label>
      <Input 
        id="long-value" 
        defaultValue="This is a very long input value that extends beyond the visible area and requires horizontal scrolling to see the full content" 
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input with very long value to test overflow behavior.',
      },
    },
  },
};

export const MinWidth: Story = {
  render: () => (
    <div className="grid w-32 items-center gap-1.5">
      <Label htmlFor="min-width">Narrow</Label>
      <Input id="min-width" placeholder="Text" />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input with minimal width constraint.',
      },
    },
  },
};

export const FullWidth: Story = {
  render: () => (
    <div className="grid w-full max-w-4xl items-center gap-1.5">
      <Label htmlFor="full-width">Full Width Input</Label>
      <Input id="full-width" placeholder="This input spans the full width" />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input that spans full width of container.',
      },
    },
  },
};

export const ReadOnly: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="readonly">Read Only</Label>
      <Input 
        id="readonly" 
        defaultValue="This value cannot be changed" 
        readOnly 
      />
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Read-only input that displays but cannot be edited.',
      },
    },
  },
};

export const WithMaxLength: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="maxlength">Username (max 10 characters)</Label>
      <Input 
        id="maxlength" 
        placeholder="Username" 
        maxLength={10}
      />
      <p className="text-sm text-muted-foreground">
        Maximum 10 characters allowed.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input with maximum length constraint.',
      },
    },
  },
};

export const WithPattern: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="pattern">Phone Number</Label>
      <Input 
        id="pattern" 
        type="tel"
        placeholder="(123) 456-7890" 
        pattern="[0-9]{3}-[0-9]{3}-[0-9]{4}"
      />
      <p className="text-sm text-muted-foreground">
        Format: 123-456-7890
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Input with pattern validation for phone numbers.',
      },
    },
  },
};

export const Required: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="required">
        Email <span className="text-red-500">*</span>
      </Label>
      <Input 
        id="required" 
        type="email"
        placeholder="Email" 
        required
      />
      <p className="text-sm text-muted-foreground">
        This field is required.
      </p>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Required input field with visual indicator.',
      },
    },
  },
};
