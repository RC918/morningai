import type { Meta, StoryObj } from '@storybook/react';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from './select';

/**
 * The Select component provides a dropdown selection interface built on Radix UI.
 * It offers a consistent and accessible way to choose from a list of options.
 * 
 * ## Features
 * - Full keyboard navigation support
 * - Screen reader accessible
 * - Customizable placeholder text
 * - Disabled state support
 * - Controlled and uncontrolled modes
 * - Custom styling with Tailwind CSS
 */
const meta = {
  title: 'UI/Select',
  component: Select,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Select component is a dropdown menu that allows users to choose from a list of options. It's built on top of Radix UI's Select primitive for maximum accessibility.

### Usage Guidelines
- Use for lists of 5+ options where space is limited
- Provide clear, descriptive option labels
- Use placeholder text to indicate the expected selection
- Group related options when dealing with many choices
- Consider using radio buttons for 2-4 options instead

### Accessibility
- Full keyboard navigation (Arrow keys, Enter, Escape)
- Screen reader support with proper ARIA attributes
- Focus management and visual indicators
- Supports disabled state for individual options
        `,
      },
    },
  },
  tags: ['autodocs'],
  argTypes: {
    disabled: {
      control: 'boolean',
      description: 'Whether the select is disabled',
      table: {
        type: { summary: 'boolean' },
        defaultValue: { summary: 'false' },
      },
    },
    defaultValue: {
      control: 'text',
      description: 'Default selected value',
      table: {
        type: { summary: 'string' },
      },
    },
    onValueChange: {
      action: 'valueChanged',
      description: 'Function called when selection changes',
      table: {
        type: { summary: '(value: string) => void' },
      },
    },
  },
} satisfies Meta<typeof Select>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
        <SelectItem value="grape">Grape</SelectItem>
        <SelectItem value="pineapple">Pineapple</SelectItem>
      </SelectContent>
    </Select>
  ),
};

export const WithDefaultValue: Story = {
  render: () => (
    <Select defaultValue="banana">
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
        <SelectItem value="grape">Grape</SelectItem>
        <SelectItem value="pineapple">Pineapple</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select with a pre-selected default value.',
      },
    },
  },
};

export const Disabled: Story = {
  render: () => (
    <Select disabled>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select a fruit" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="apple">Apple</SelectItem>
        <SelectItem value="banana">Banana</SelectItem>
        <SelectItem value="orange">Orange</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select in disabled state - user cannot interact with it.',
      },
    },
  },
};

export const LongOptions: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[250px]">
        <SelectValue placeholder="Select a programming language" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="javascript">JavaScript - The versatile web language</SelectItem>
        <SelectItem value="typescript">TypeScript - JavaScript with static typing</SelectItem>
        <SelectItem value="python">Python - Simple and powerful programming</SelectItem>
        <SelectItem value="rust">Rust - Systems programming with memory safety</SelectItem>
        <SelectItem value="go">Go - Fast and simple backend development</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select with long option text to test text wrapping and layout.',
      },
    },
  },
};

export const ManyOptions: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a country" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="us">United States</SelectItem>
        <SelectItem value="ca">Canada</SelectItem>
        <SelectItem value="mx">Mexico</SelectItem>
        <SelectItem value="uk">United Kingdom</SelectItem>
        <SelectItem value="fr">France</SelectItem>
        <SelectItem value="de">Germany</SelectItem>
        <SelectItem value="it">Italy</SelectItem>
        <SelectItem value="es">Spain</SelectItem>
        <SelectItem value="jp">Japan</SelectItem>
        <SelectItem value="kr">South Korea</SelectItem>
        <SelectItem value="cn">China</SelectItem>
        <SelectItem value="in">India</SelectItem>
        <SelectItem value="au">Australia</SelectItem>
        <SelectItem value="br">Brazil</SelectItem>
        <SelectItem value="ar">Argentina</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select with many options to test scrolling behavior.',
      },
    },
  },
};

export const SmallWidth: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[100px]">
        <SelectValue placeholder="Size" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="xs">XS</SelectItem>
        <SelectItem value="s">S</SelectItem>
        <SelectItem value="m">M</SelectItem>
        <SelectItem value="l">L</SelectItem>
        <SelectItem value="xl">XL</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select with minimal width to test compact layouts.',
      },
    },
  },
};

export const WithEmptyOption: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select an option" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="">None</SelectItem>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select with an empty/none option for clearing selection.',
      },
    },
  },
};

export const WithIcons: Story = {
  render: () => (
    <Select>
      <SelectTrigger className="w-[200px]">
        <SelectValue placeholder="Select a status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="active">✅ Active</SelectItem>
        <SelectItem value="pending">⏳ Pending</SelectItem>
        <SelectItem value="inactive">❌ Inactive</SelectItem>
        <SelectItem value="archived">📦 Archived</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Select options with icons for better visual identification.',
      },
    },
  },
};

export const Interactive: Story = {
  render: () => (
    <Select onValueChange={(value) => console.log('Selected:', value)}>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Make a selection" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="option1">Option 1</SelectItem>
        <SelectItem value="option2">Option 2</SelectItem>
        <SelectItem value="option3">Option 3</SelectItem>
      </SelectContent>
    </Select>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Interactive select that logs selection changes to console.',
      },
    },
  },
};
