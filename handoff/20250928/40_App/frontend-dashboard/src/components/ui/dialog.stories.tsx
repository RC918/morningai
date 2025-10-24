import type { Meta, StoryObj } from '@storybook/react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from './dialog';
import { Button } from './button';
import { Input } from './input';
import { Label } from './label';
import { Badge } from './badge';

/**
 * The Dialog component provides a modal overlay for displaying content that requires user attention.
 * Built on Radix UI's Dialog primitive with full accessibility support.
 * 
 * ## Features
 * - Modal overlay with backdrop
 * - Focus trap and keyboard navigation
 * - Escape key to close
 * - Customizable content and actions
 * - Responsive sizing
 * - Full accessibility support
 */
const meta = {
  title: 'UI/Dialog',
  component: Dialog,
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: `
The Dialog component creates a modal overlay that captures user focus and requires interaction before returning to the main content. It's perfect for forms, confirmations, and important messages.

### Sub-components
- **Dialog**: Main container component
- **DialogTrigger**: Button or element that opens the dialog
- **DialogContent**: Content container with backdrop
- **DialogHeader**: Header section for title and description
- **DialogTitle**: Dialog title (required for accessibility)
- **DialogDescription**: Optional description text
- **DialogFooter**: Footer section for actions

### Usage Guidelines
- Use for important actions that require user attention
- Always include a DialogTitle for accessibility
- Provide clear action buttons
- Use for forms, confirmations, or detailed information
- Keep content focused and concise
- Provide a way to close (X button or Cancel action)

### Accessibility
- Focus trap keeps keyboard navigation within dialog
- Escape key closes the dialog
- Proper ARIA attributes (role="dialog", aria-labelledby)
- Focus returns to trigger element on close
- Screen reader announcements
- Backdrop click to close
        `,
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta<typeof Dialog>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open Dialog</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Dialog Title</DialogTitle>
          <DialogDescription>
            This is a dialog description. You can put any content here.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content goes here.</p>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const WithForm: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Edit Profile</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit profile</DialogTitle>
          <DialogDescription>
            Make changes to your profile here. Click save when you're done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">
              Name
            </Label>
            <Input id="name" defaultValue="Pedro Duarte" className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="username" className="text-right">
              Username
            </Label>
            <Input id="username" defaultValue="@peduarte" className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit">Save changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const Confirmation: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete Account</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Are you absolutely sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete your
            account and remove your data from our servers.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Delete</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const WithoutDescription: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Simple Dialog</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p>This dialog has no description.</p>
        </div>
        <DialogFooter>
          <Button>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const LongContent: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>View Terms</Button>
      </DialogTrigger>
      <DialogContent className="max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Terms and Conditions</DialogTitle>
          <DialogDescription>
            Please read our terms and conditions carefully.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-4">
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
          <p>Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.</p>
          <p>Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.</p>
          <p>Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.</p>
          <p>Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.</p>
        </div>
        <DialogFooter>
          <Button>Accept</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
};

export const MultipleButtons: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Save Changes</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Unsaved Changes</DialogTitle>
          <DialogDescription>
            You have unsaved changes. What would you like to do?
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="sm:justify-between">
          <Button variant="outline">Cancel</Button>
          <div className="flex gap-2">
            <Button variant="secondary">Don't Save</Button>
            <Button>Save</Button>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog with multiple action buttons.',
      },
    },
  },
};

export const MinimalContent: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>A</DialogTitle>
        </DialogHeader>
        <div className="py-4">
          <p>B</p>
        </div>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog with minimal single-character content.',
      },
    },
  },
};

export const VeryLongTitle: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>
            This is a very long dialog title that might wrap to multiple lines depending on the dialog width and screen size
          </DialogTitle>
          <DialogDescription>
            Testing title wrapping behavior in dialogs.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Dialog content.</p>
        </div>
        <DialogFooter>
          <Button>OK</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog with very long title to test text wrapping.',
      },
    },
  },
};

export const WithBadges: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>View Status</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <div className="flex items-center gap-2">
            <DialogTitle>Project Status</DialogTitle>
            <Badge>Active</Badge>
          </div>
          <DialogDescription>
            Current status and metrics for your project.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 space-y-3">
          <div className="flex justify-between items-center">
            <span>Build Status:</span>
            <Badge>Success</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Tests:</span>
            <Badge variant="secondary">Passing</Badge>
          </div>
          <div className="flex justify-between items-center">
            <span>Deployment:</span>
            <Badge variant="destructive">Failed</Badge>
          </div>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog with Badge components for status display.',
      },
    },
  },
};

export const WideDialog: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Open Wide Dialog</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[800px]">
        <DialogHeader>
          <DialogTitle>Wide Dialog</DialogTitle>
          <DialogDescription>
            This dialog has a wider maximum width for displaying more content.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4">
          <p>Content can span across a wider area, useful for tables or detailed forms.</p>
        </div>
        <DialogFooter>
          <Button>Close</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog with wider maximum width for complex content.',
      },
    },
  },
};

export const LoadingState: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Process Data</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Processing...</DialogTitle>
          <DialogDescription>
            Please wait while we process your request.
          </DialogDescription>
        </DialogHeader>
        <div className="py-8 flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
        <DialogFooter>
          <Button disabled>Cancel</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog showing loading state with spinner.',
      },
    },
  },
};

export const NestedForm: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button>Create Account</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>Create New Account</DialogTitle>
          <DialogDescription>
            Fill in the form below to create a new account.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid gap-2">
            <Label htmlFor="fullname">Full Name</Label>
            <Input id="fullname" placeholder="John Doe" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="email-create">Email</Label>
            <Input id="email-create" type="email" placeholder="john@example.com" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="password-create">Password</Label>
            <Input id="password-create" type="password" placeholder="••••••••" />
          </div>
          <div className="grid gap-2">
            <Label htmlFor="confirm-password">Confirm Password</Label>
            <Input id="confirm-password" type="password" placeholder="••••••••" />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button type="submit">Create Account</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Dialog with complex multi-field form.',
      },
    },
  },
};

export const AlertDialog: Story = {
  render: () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete All</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle className="text-destructive">⚠️ Warning</DialogTitle>
          <DialogDescription>
            This action will permanently delete all your data. This cannot be undone.
          </DialogDescription>
        </DialogHeader>
        <div className="py-4 bg-destructive/10 rounded-md p-4">
          <p className="text-sm font-medium">Items to be deleted:</p>
          <ul className="text-sm mt-2 space-y-1">
            <li>• All projects (15)</li>
            <li>• All files (234)</li>
            <li>• All settings</li>
          </ul>
        </div>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Yes, Delete Everything</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Alert-style dialog for dangerous actions with warning styling.',
      },
    },
  },
};
