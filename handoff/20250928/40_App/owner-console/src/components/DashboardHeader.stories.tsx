import * as React from 'react';
import type { Meta, StoryObj } from '@storybook/react';
import DashboardHeader from './DashboardHeader';

const meta: Meta<typeof DashboardHeader> = {
  title: 'OwnerConsole/Layout/DashboardHeader',
import type { Meta, StoryObj } from '@storybook/react';
import DashboardHeader from './DashboardHeader';

const meta: Meta<typeof DashboardHeader> = {
  title: 'OwnerConsole/Layout/DashboardHeader',
  component: DashboardHeader,
  parameters: {
    layout: 'fullscreen',
  },
  argTypes: {
    title: {
      control: 'text',
      description: 'Header title text',
    },
    subtitle: {
      control: 'text',
      description: 'Optional subtitle text',
    },
    notificationCount: {
      control: { type: 'number', min: 0 },
      description: 'Number of unread notifications',
    },
    user: {
      control: 'object',
      description: 'User object with name, role, and avatar',
    },
  },
};

export default meta;
type Story = StoryObj<typeof DashboardHeader>;

const defaultUser = {
  name: 'Ryan Chen',
  role: 'Platform Owner',
  avatar: undefined,
};

export const Default: Story = {
  args: {
    user: defaultUser,
  },
};

export const WithCustomTitle: Story = {
  args: {
    user: defaultUser,
    title: 'System Monitoring',
    subtitle: 'Real-time system health and performance metrics',
  },
};

export const WithNotifications: Story = {
  args: {
    user: defaultUser,
    notificationCount: 5,
  },
};

export const WithManyNotifications: Story = {
  args: {
    user: defaultUser,
    notificationCount: 99,
  },
};

export const NoNotifications: Story = {
  args: {
    user: defaultUser,
    notificationCount: 0,
  },
};

export const WithAvatar: Story = {
  args: {
    user: {
      name: 'Ryan Chen',
      role: 'Platform Owner',
      avatar: '/assets/brand/icon-only/MorningAI_icon_1024.png',
    },
    notificationCount: 2,
  },
};

export const WithDifferentUser: Story = {
  args: {
    user: {
      name: 'Admin User',
      role: 'System Administrator',
      avatar: undefined,
    },
    notificationCount: 3,
  },
};

export const MinimalUser: Story = {
  args: {
    user: {
      name: 'A',
      role: 'Guest',
    },
  },
};

export const NoUser: Story = {
  args: {
    user: undefined,
  },
};

export const AllFeatures: Story = {
  args: {
    user: {
      name: 'Platform Owner',
      role: 'Super Admin',
      avatar: undefined,
    },
    title: 'Owner Dashboard',
    subtitle: 'Manage your AI agents and monitor system health',
    notificationCount: 12,
  },
};
