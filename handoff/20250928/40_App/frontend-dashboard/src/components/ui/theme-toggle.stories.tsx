import type { Meta, StoryObj } from '@storybook/react';
import { ThemeToggle } from './theme-toggle';
import { ThemeProvider } from '../../contexts/ThemeContext';

const meta = {
  title: 'UI/Theme Toggle',
  component: ThemeToggle,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  decorators: [
    (Story) => (
      <ThemeProvider defaultTheme="light" storageKey="storybook-theme">
        <div className="p-8 bg-background text-foreground rounded-lg border">
          <Story />
        </div>
      </ThemeProvider>
    ),
  ],
} satisfies Meta<typeof ThemeToggle>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {},
  parameters: {
    docs: {
      description: {
        story: 'Default theme toggle button that switches between light and dark modes.',
      },
    },
  },
};

export const WithContext: Story = {
  render: () => (
    <div className="space-y-4">
      <div className="flex items-center gap-4">
        <ThemeToggle />
        <span className="text-sm text-muted-foreground">
          Click to toggle between light and dark mode
        </span>
      </div>
      <div className="p-4 bg-card rounded-lg border">
        <h3 className="font-semibold mb-2">Sample Content</h3>
        <p className="text-sm text-muted-foreground">
          This content will change appearance based on the selected theme.
        </p>
      </div>
    </div>
  ),
  parameters: {
    docs: {
      description: {
        story: 'Theme toggle with sample content showing how colors adapt to the theme.',
      },
    },
  },
};
