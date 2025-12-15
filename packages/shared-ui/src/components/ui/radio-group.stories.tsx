import type { Meta, StoryObj } from "@storybook/react";

import { RadioGroup, RadioGroupItem } from "./radio-group";
import { Label } from "./label";

const meta = {
  title: "UI/RadioGroup",
  component: RadioGroup,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof RadioGroup>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <RadioGroup defaultValue="option-1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="option-1" />
        <Label htmlFor="option-1">Option 1</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="option-2" />
        <Label htmlFor="option-2">Option 2</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-3" id="option-3" />
        <Label htmlFor="option-3">Option 3</Label>
      </div>
    </RadioGroup>
  ),
};

export const Horizontal: Story = {
  render: () => (
    <RadioGroup defaultValue="small" className="flex gap-4">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="small" id="small" />
        <Label htmlFor="small">Small</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="medium" id="medium" />
        <Label htmlFor="medium">Medium</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="large" id="large" />
        <Label htmlFor="large">Large</Label>
      </div>
    </RadioGroup>
  ),
};

export const WithDisabledOption: Story = {
  render: () => (
    <RadioGroup defaultValue="option-1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="r1" />
        <Label htmlFor="r1">Available</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="r2" disabled />
        <Label htmlFor="r2" className="opacity-50">Disabled</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-3" id="r3" />
        <Label htmlFor="r3">Available</Label>
      </div>
    </RadioGroup>
  ),
};

export const FormExample: Story = {
  render: () => (
    <div className="max-w-md space-y-4">
      <div>
        <h3 className="mb-3 text-sm font-medium">Select your plan</h3>
        <RadioGroup defaultValue="pro">
          <div className="flex items-center space-x-2 rounded-lg border p-3">
            <RadioGroupItem value="free" id="free" />
            <div className="flex-1">
              <Label htmlFor="free" className="font-medium">Free</Label>
              <p className="text-xs text-muted-foreground">Basic features for personal use</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 rounded-lg border p-3 border-primary">
            <RadioGroupItem value="pro" id="pro" />
            <div className="flex-1">
              <Label htmlFor="pro" className="font-medium">Pro</Label>
              <p className="text-xs text-muted-foreground">Advanced features for professionals</p>
            </div>
          </div>
          <div className="flex items-center space-x-2 rounded-lg border p-3">
            <RadioGroupItem value="enterprise" id="enterprise" />
            <div className="flex-1">
              <Label htmlFor="enterprise" className="font-medium">Enterprise</Label>
              <p className="text-xs text-muted-foreground">Custom solutions for large teams</p>
            </div>
          </div>
        </RadioGroup>
      </div>
    </div>
  ),
};

export const WithI18n: Story = {
  name: "With i18n (Chinese)",
  render: () => (
    <RadioGroup defaultValue="option-1">
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-1" id="zh-1" />
        <Label htmlFor="zh-1">選項一</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-2" id="zh-2" />
        <Label htmlFor="zh-2">選項二</Label>
      </div>
      <div className="flex items-center space-x-2">
        <RadioGroupItem value="option-3" id="zh-3" />
        <Label htmlFor="zh-3">選項三</Label>
      </div>
    </RadioGroup>
  ),
};
