import type { Meta, StoryObj } from "@storybook/react";

import { Label } from "./label";
import { Input } from "./input";
import { Checkbox } from "./checkbox";

const meta = {
  title: "UI/Label",
  component: Label,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof Label>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    children: "Email address",
  },
};

export const WithInput: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="email">Email</Label>
      <Input type="email" id="email" placeholder="Enter your email" />
    </div>
  ),
};

export const WithCheckbox: Story = {
  render: () => (
    <div className="flex items-center space-x-2">
      <Checkbox id="terms" />
      <Label htmlFor="terms">Accept terms and conditions</Label>
    </div>
  ),
};

export const Required: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="name">
        Name <span className="text-destructive">*</span>
      </Label>
      <Input type="text" id="name" placeholder="Enter your name" required />
    </div>
  ),
};

export const WithDescription: Story = {
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="username">Username</Label>
      <Input type="text" id="username" placeholder="Enter username" />
      <p className="text-xs text-muted-foreground">
        This will be your public display name.
      </p>
    </div>
  ),
};

export const Disabled: Story = {
  render: () => (
    <div className="group grid w-full max-w-sm items-center gap-1.5" data-disabled="true">
      <Label htmlFor="disabled-input">Disabled Field</Label>
      <Input type="text" id="disabled-input" placeholder="Cannot edit" disabled />
    </div>
  ),
};

export const FormExample: Story = {
  render: () => (
    <form className="space-y-4 max-w-sm">
      <div className="grid gap-1.5">
        <Label htmlFor="form-email">
          Email <span className="text-destructive">*</span>
        </Label>
        <Input type="email" id="form-email" placeholder="you@example.com" />
      </div>
      <div className="grid gap-1.5">
        <Label htmlFor="form-password">
          Password <span className="text-destructive">*</span>
        </Label>
        <Input type="password" id="form-password" placeholder="Enter password" />
        <p className="text-xs text-muted-foreground">
          Must be at least 8 characters.
        </p>
      </div>
      <div className="flex items-center space-x-2">
        <Checkbox id="form-remember" />
        <Label htmlFor="form-remember">Remember me</Label>
      </div>
    </form>
  ),
};

export const WithI18n: Story = {
  name: "With i18n (Chinese)",
  render: () => (
    <div className="grid w-full max-w-sm items-center gap-1.5">
      <Label htmlFor="zh-email">
        電子郵件 <span className="text-destructive">*</span>
      </Label>
      <Input type="email" id="zh-email" placeholder="請輸入電子郵件" />
      <p className="text-xs text-muted-foreground">
        我們不會分享您的電子郵件地址。
      </p>
    </div>
  ),
};
