import type { Meta, StoryObj } from '@storybook/react';
import { Checkbox } from './checkbox';
import { Label } from './label';

/**
 * The Checkbox component provides a binary selection interface built on Radix UI.
 * It allows users to toggle between checked and unchecked states.
 * 
 * ## Features
 * - Full keyboard navigation support (Space to toggle)
 * - Screen reader accessible with proper ARIA attributes
 * - Indeterminate state support
 * - Disabled state support
 * - Controlled and uncontrolled modes
 * - Custom styling with Tailwind CSS
 */
const meta = {
  title: 'UI/Checkbox',
  component: Checkbox,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Checkbox component allows users to select one or more options from a set. It's built on top of Radix UI's Checkbox primitive for maximum accessibility.

### Usage Guidelines
- Use for binary choices (yes/no, on/off)
- Use for selecting multiple items from a list
- Always pair with a descriptive label
- Use indeterminate state for "select all" functionality
- Group related checkboxes together

### Accessibility
- Full keyboard support (Space to toggle, Tab to navigate)
- Screen reader announces checked/unchecked state
- Proper ARIA attributes (aria-checked, aria-label)
- Focus indicators for keyboard navigation
- Supports disabled state
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    checked: {
      control: 'boolean',
      description: 'Whether the checkbox is checked',
      table: {
        type: { summary: 'boolean | "indeterminate"' },
        defaultValue: { summary: 'false' },
      },
    },
    disabled: {
      control: 'boolean',
      description: 'Whether the checkbox is disabled',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' },
      },
    },
    onCheckedChange: {
      action: 'checkedChanged',
      description: 'Function called when checked state changes',
      table: {
        type: { summary: '(checked: boolean) => void' },
      },
    },
  },
} satisfies Meta<typeof Checkbox>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
  ),
};

export const Checked: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox id="checked" defaultChecked />
      <Label htmlFor="checked">This checkbox is checked by default</Label>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with default checked state.',
      },
    },
  },
};

export const Disabled: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox id="disabled" disabled />
      <Label htmlFor="disabled">This checkbox is disabled</Label>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Checkbox in disabled state - user cannot interact with it.',
      },
    },
  },
};

export const DisabledChecked: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox id="disabled-checked" disabled defaultChecked />
      <Label htmlFor="disabled-checked">Disabled and checked</Label>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Checkbox that is both disabled and checked.',
      },
    },
  },
};

export const WithoutLabel: Story = {
  render: () => <Checkbox />,
  parameters: {
    docs: {
      description: {
        story: 'Checkbox without a label - not recommended for accessibility.',
      },
    },
  },
};

export const MultipleCheckboxes: Story = {
  render: () => (
    <div className="space-y-4">
      <div className="flex items-center space-x-2">
        <Checkbox id="option1" />
        <Label htmlFor="option1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option2" />
        <Label htmlFor="option2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="option3" />
        <Label htmlFor="option3">Option 3</Label>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Multiple checkboxes in a group for selecting multiple options.',
      },
    },
  },
};

export const LongLabel: Story = {
  render: () => (
    <div className="flex items-start space-x-2 max-w-md">
      <Checkbox id="long-label" className="mt-1" />
      <Label htmlFor="long-label" className="leading-relaxed">
        I agree to the terms and conditions, privacy policy, and all other legal documents that govern the use of this application and its services
      </Label>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with very long label text to test text wrapping.',
      },
    },
  },
};

export const WithDescription: Story = {
  render: () => (
    <div className="flex items-start space-x-2 max-w-md">
      <Checkbox id="with-description" className="mt-1" />
      <div className="grid gap-1.5 leading-none">
        <Label htmlFor="with-description">Marketing emails</Label>
        <p className="text-sm text-muted-foreground">
          Receive emails about new products, features, and more.
        </p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Checkbox with label and additional description text.',
      },
    },
  },
};

export const Interactive: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox 
        id="interactive" 
        onCheckedChange={(checked) => console.log('Checked:', checked)}
      />
      <Label htmlFor="interactive">Click me (check console)</Label>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Interactive checkbox that logs state changes to console.',
      },
    },
  },
};

export const FormExample: Story = {
  render: () => (
    <form className="space-y-4">
      <div className="space-y-2">
        <h3 className="text-sm font-medium">Select your interests:</h3>
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <Checkbox id="tech" />
            <Label htmlFor="tech">Technology</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="design" />
            <Label htmlFor="design">Design</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="business" />
            <Label htmlFor="business">Business</Label>
          </div>
          <div className="flex items-center space-x-2">
            <Checkbox id="marketing" />
            <Label htmlFor="marketing">Marketing</Label>
          </div>
        </div>
      </div>
    </form>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Example of checkboxes used in a form context.',
      },
    },
  },
};
