import type { Meta, StoryObj } from "@storybook/react";
import { Bold, Italic, Underline, AlignLeft, AlignCenter, AlignRight } from "lucide-react";

import { Toggle } from "./toggle";

const meta = {
  title: "UI/Toggle",
  component: Toggle,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "outline"],
      description: "Visual variant of the toggle",
    },
    size: {
      control: "select",
      options: ["default", "sm", "lg"],
      description: "Size of the toggle",
    },
  },
} satisfies Meta<typeof Toggle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const WithText: Story = {
  args: {
    children: "Toggle",
  },
};

export const Outline: Story = {
  args: {
    variant: "outline",
    children: <Italic className="h-4 w-4" />,
    "aria-label": "Toggle italic",
  },
};

export const Small: Story = {
  args: {
    size: "sm",
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const Large: Story = {
  args: {
    size: "lg",
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const Disabled: Story = {
  args: {
    disabled: true,
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const Pressed: Story = {
  args: {
    pressed: true,
    children: <Bold className="h-4 w-4" />,
    "aria-label": "Toggle bold",
  },
};

export const AllSizes: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Toggle size="sm" aria-label="Toggle small">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle size="default" aria-label="Toggle default">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle size="lg" aria-label="Toggle large">
        <Bold className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const AllVariants: Story = {
  render: () => (
    <div className="flex items-center gap-4">
      <Toggle variant="default" aria-label="Toggle default">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle variant="outline" aria-label="Toggle outline">
        <Bold className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const TextFormattingToolbar: Story = {
  render: () => (
    <div className="flex items-center gap-1 rounded-md border p-1">
      <Toggle aria-label="Toggle bold">
        <Bold className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Toggle italic">
        <Italic className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Toggle underline">
        <Underline className="h-4 w-4" />
      </Toggle>
      <div className="mx-1 h-4 w-px bg-border" />
      <Toggle aria-label="Align left">
        <AlignLeft className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Align center">
        <AlignCenter className="h-4 w-4" />
      </Toggle>
      <Toggle aria-label="Align right">
        <AlignRight className="h-4 w-4" />
      </Toggle>
    </div>
  ),
};

export const WithIconAndText: Story = {
  render: () => (
    <Toggle aria-label="Toggle with icon and text">
      <Bold className="h-4 w-4" />
      Bold
    </Toggle>
  ),
};
