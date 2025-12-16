import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';
import Sidebar from './Sidebar';

// Extended story args type that includes Storybook-only routing parameter
interface SidebarStoryArgs {
  user?: {
    name?: string;
    email?: string;
    role?: string;
    avatar?: string;
  };
  collapsed?: boolean;
  isMobileDrawer?: boolean;
  /** Storybook-only: initial route for MemoryRouter (not a Sidebar prop) */
  initialPath?: string;
}

const meta: Meta<SidebarStoryArgs> = {
  title: 'OwnerConsole/Layout/Sidebar',
  component: Sidebar,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story, context) => (
      <MemoryRouter initialEntries={[(context.args as SidebarStoryArgs).initialPath || '/dashboard']}>
        <div style={{ height: '100vh', display: 'flex' }}>
          <Story />
        </div>
      </MemoryRouter>
    ),
  ],
  argTypes: {
    user: {
      control: 'object',
      description: 'User object with name, role, and avatar',
    },
  },
};

export default meta;
type Story = StoryObj<SidebarStoryArgs>;

const defaultUser = {
  name: 'Ryan Chen',
  role: 'Platform Owner',
  avatar: undefined,
};

export const Default: Story = {
  args: {
    user: defaultUser,
    initialPath: '/dashboard',
  },
};

export const GovernanceActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/governance',
  },
};

export const AIPoliciesActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/ai-policies',
  },
};

export const TenantsActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/tenants',
  },
};

export const MonitoringActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/monitoring',
  },
};

export const UXMetricsActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/ux-metrics',
  },
};

export const FailureExperimentsActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/failure-experiments',
  },
};

export const SettingsActive: Story = {
  args: {
    user: defaultUser,
    initialPath: '/settings',
  },
};

export const WithDifferentUser: Story = {
  args: {
    user: {
      name: 'Admin User',
      role: 'System Administrator',
      avatar: undefined,
    },
    initialPath: '/dashboard',
  },
};

export const MinimalUser: Story = {
  args: {
    user: {
      name: 'A',
      role: 'Guest',
    },
    initialPath: '/dashboard',
  },
};

export const NoUser: Story = {
  args: {
    user: undefined,
    initialPath: '/dashboard',
  },
};
