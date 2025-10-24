import type { Meta, StoryObj } from '@storybook/react';
import { Alert, AlertTitle, AlertDescription } from './alert';
import { AlertTriangle, CheckCircle, Info, XCircle } from 'lucide-react';

const meta = {
  title: 'UI/Alert',
  component: Alert,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    variant: {
      control: 'select',
      options: ['default', 'destructive'],
    },
  },
} satisfies Meta<typeof Alert>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    variant: 'default',
  },
  render: (args) => (
    <Alert {...args}>
      <Info />
      <AlertTitle>Information</AlertTitle>
      <AlertDescription>
        This is a default alert with some information for the user.
      </AlertDescription>
    </Alert>
  ),
};

export const Destructive: Story = {
  args: {
    variant: 'destructive',
  },
  render: (args) => (
    <Alert {...args}>
      <XCircle />
      <AlertTitle>Error</AlertTitle>
      <AlertDescription>
        Something went wrong. Please try again or contact support.
      </AlertDescription>
    </Alert>
  ),
};

export const Success: Story = {
  render: () => (
    <Alert>
      <CheckCircle className="text-green-600" />
      <AlertTitle>Success</AlertTitle>
      <AlertDescription>
        Your changes have been saved successfully.
      </AlertDescription>
    </Alert>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Success alert using the default variant with a green icon.',
      },
    },
  },
};

export const Warning: Story = {
  render: () => (
    <Alert>
      <AlertTriangle className="text-yellow-600" />
      <AlertTitle>Warning</AlertTitle>
      <AlertDescription>
        This action cannot be undone. Please proceed with caution.
      </AlertDescription>
    </Alert>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Warning alert using the default variant with a yellow icon.',
      },
    },
  },
};

export const WithoutIcon: Story = {
  render: () => (
    <Alert>
      <AlertTitle>No Icon Alert</AlertTitle>
      <AlertDescription>
        This alert doesn't have an icon, so the content spans the full width.
      </AlertDescription>
    </Alert>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Alert without an icon - content automatically spans full width.',
      },
    },
  },
};

export const LongContent: Story = {
  render: () => (
    <Alert>
      <Info />
      <AlertTitle>Detailed Information</AlertTitle>
      <AlertDescription>
        <p>This alert contains multiple paragraphs of content to demonstrate how longer text is handled.</p>
        <p>The alert component automatically adjusts its height to accommodate the content, and the text maintains proper line spacing and readability.</p>
        <p>You can include multiple paragraphs, lists, or other content within the AlertDescription component.</p>
      </AlertDescription>
    </Alert>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Alert with longer content including multiple paragraphs.',
      },
    },
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="space-y-4">
      <Alert>
        <Info />
        <AlertTitle>Information</AlertTitle>
        <AlertDescription>
          This is a default informational alert.
        </AlertDescription>
      </Alert>
      
      <Alert>
        <CheckCircle className="text-green-600" />
        <AlertTitle>Success</AlertTitle>
        <AlertDescription>
          Operation completed successfully.
        </AlertDescription>
      </Alert>
      
      <Alert>
        <AlertTriangle className="text-yellow-600" />
        <AlertTitle>Warning</AlertTitle>
        <AlertDescription>
          Please review before proceeding.
        </AlertDescription>
      </Alert>
      
      <Alert variant="destructive">
        <XCircle />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>
          An error occurred during processing.
        </AlertDescription>
      </Alert>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'All alert variants displayed together for comparison.',
      },
    },
  },
};
