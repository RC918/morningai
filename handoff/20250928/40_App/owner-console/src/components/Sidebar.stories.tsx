import React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import { MemoryRouter } from 'react-router-dom';
import Sidebar from './Sidebar';

const meta: Meta<typeof Sidebar> = {
  title: 'OwnerConsole/Layout/Sidebar',
  component: Sidebar,
  parameters: {
    layout: 'fullscreen',
  },
  decorators: [
    (Story, context) => (
      <MemoryRouter initialEntries={[context.args.initialPath || '/dashboard']}>
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
    onLogout: {
      action: 'logout',
      description: 'Callback when logout button is clicked',
    },
  },
};

export default meta;
type Story = StoryObj<typeof Sidebar>;

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
