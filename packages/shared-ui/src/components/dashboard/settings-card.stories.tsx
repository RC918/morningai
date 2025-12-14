import type { Meta, StoryObj } from "@storybook/react";
import { Settings, Shield, Bell, Lock, User, Globe, Key } from "lucide-react";

import { SettingsCard } from "./settings-card";

const meta = {
  title: "Dashboard/SettingsCard",
  component: SettingsCard,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "blue", "green", "yellow", "red", "purple"],
      description: "Color variant for the icon",
    },
    noPadding: {
      control: "boolean",
      description: "Remove default padding from content area",
    },
  },
} satisfies Meta<typeof SettingsCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "General Settings",
    description: "Configure your general preferences",
    icon: <Settings />,
  },
};

export const WithContent: Story = {
  args: {
    title: "Notification Settings",
    description: "Manage how you receive notifications",
    icon: <Bell />,
    variant: "blue",
    children: (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p id="email-notifications-label" className="text-sm font-medium">Email Notifications</p>
            <p className="text-xs text-gray-500">Receive updates via email</p>
          </div>
          <input type="checkbox" defaultChecked className="h-4 w-4" aria-labelledby="email-notifications-label" />
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p id="push-notifications-label" className="text-sm font-medium">Push Notifications</p>
            <p className="text-xs text-gray-500">Receive push notifications</p>
          </div>
          <input type="checkbox" className="h-4 w-4" aria-labelledby="push-notifications-label" />
        </div>
      </div>
    ),
  },
};

export const SecuritySettings: Story = {
  args: {
    title: "Security",
    description: "Manage your security settings and two-factor authentication",
    icon: <Shield />,
    variant: "green",
    children: (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Two-Factor Authentication</p>
            <p className="text-xs text-gray-500">Add an extra layer of security</p>
          </div>
          <button className="px-3 py-1 text-sm bg-green-500 text-white rounded-md">
            Enable
          </button>
        </div>
        <div className="flex items-center justify-between">
          <div>
            <p id="session-timeout-label" className="text-sm font-medium">Session Timeout</p>
            <p className="text-xs text-gray-500">Auto-logout after inactivity</p>
          </div>
          <select className="px-2 py-1 text-sm border rounded-md" aria-labelledby="session-timeout-label">
            <option>30 minutes</option>
            <option>1 hour</option>
            <option>4 hours</option>
          </select>
        </div>
      </div>
    ),
  },
};

export const PrivacySettings: Story = {
  args: {
    title: "Privacy",
    description: "Control your privacy and data sharing preferences",
    icon: <Lock />,
    variant: "yellow",
    children: (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <p id="profile-visibility-label" className="text-sm font-medium">Profile Visibility</p>
            <p className="text-xs text-gray-500">Who can see your profile</p>
          </div>
          <select className="px-2 py-1 text-sm border rounded-md" aria-labelledby="profile-visibility-label">
            <option>Public</option>
            <option>Private</option>
            <option>Team Only</option>
          </select>
        </div>
      </div>
    ),
  },
};

export const WithoutDescription: Story = {
  args: {
    title: "Quick Settings",
    icon: <Settings />,
    children: (
      <div className="flex items-center justify-between">
        <span id="dark-mode-label" className="text-sm">Dark Mode</span>
        <input type="checkbox" className="h-4 w-4" aria-labelledby="dark-mode-label" />
      </div>
    ),
  },
};

export const WithoutIcon: Story = {
  args: {
    title: "Account Settings",
    description: "Manage your account information",
    children: (
      <div className="space-y-3">
        <div>
          <label htmlFor="display-name" className="text-sm font-medium">Display Name</label>
          <input
            id="display-name"
            type="text"
            defaultValue="John Doe"
            className="mt-1 w-full px-3 py-2 border rounded-md text-sm"
          />
        </div>
        <button className="px-4 py-2 text-sm bg-blue-500 text-white rounded-md">
          Save Changes
        </button>
      </div>
    ),
  },
};

export const NoPadding: Story = {
  args: {
    title: "Custom Layout",
    description: "Card with no content padding for custom layouts",
    icon: <Globe />,
    noPadding: true,
    children: (
      <div className="border-t">
        <div className="px-5 py-3 hover:bg-gray-50 cursor-pointer border-b">
          <p className="text-sm font-medium">Language</p>
          <p className="text-xs text-gray-500">English (US)</p>
        </div>
        <div className="px-5 py-3 hover:bg-gray-50 cursor-pointer border-b">
          <p className="text-sm font-medium">Timezone</p>
          <p className="text-xs text-gray-500">UTC+8 (Taipei)</p>
        </div>
        <div className="px-5 py-3 hover:bg-gray-50 cursor-pointer">
          <p className="text-sm font-medium">Date Format</p>
          <p className="text-xs text-gray-500">YYYY-MM-DD</p>
        </div>
      </div>
    ),
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <SettingsCard
        title="Default"
        description="Default variant"
        icon={<Settings />}
        variant="default"
      />
      <SettingsCard
        title="Blue"
        description="Blue variant"
        icon={<Globe />}
        variant="blue"
      />
      <SettingsCard
        title="Green"
        description="Green variant"
        icon={<Shield />}
        variant="green"
      />
      <SettingsCard
        title="Yellow"
        description="Yellow variant"
        icon={<Bell />}
        variant="yellow"
      />
      <SettingsCard
        title="Red"
        description="Red variant"
        icon={<Lock />}
        variant="red"
      />
      <SettingsCard
        title="Purple"
        description="Purple variant"
        icon={<Key />}
        variant="purple"
      />
    </div>
  ),
};

export const SettingsPageExample: Story = {
  render: () => (
    <div className="space-y-6 max-w-2xl">
      <SettingsCard
        title="Profile"
        description="Manage your public profile information"
        icon={<User />}
        variant="blue"
      >
        <div className="space-y-3">
          <div>
            <label htmlFor="profile-username" className="text-sm font-medium">Username</label>
            <input
              id="profile-username"
              type="text"
              defaultValue="johndoe"
              className="mt-1 w-full px-3 py-2 border rounded-md text-sm"
            />
          </div>
          <div>
            <label htmlFor="profile-email" className="text-sm font-medium">Email</label>
            <input
              id="profile-email"
              type="email"
              defaultValue="john@example.com"
              className="mt-1 w-full px-3 py-2 border rounded-md text-sm"
            />
          </div>
        </div>
      </SettingsCard>

      <SettingsCard
        title="Security"
        description="Keep your account secure"
        icon={<Shield />}
        variant="green"
      >
        <div className="flex items-center justify-between">
          <div>
            <p className="text-sm font-medium">Two-Factor Authentication</p>
            <p className="text-xs text-gray-500">Enabled on Dec 1, 2025</p>
          </div>
          <button className="px-3 py-1 text-sm border rounded-md">
            Manage
          </button>
        </div>
      </SettingsCard>

      <SettingsCard
        title="Notifications"
        description="Choose what updates you receive"
        icon={<Bell />}
        variant="yellow"
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span id="page-email-notifications-label" className="text-sm">Email notifications</span>
            <input type="checkbox" defaultChecked className="h-4 w-4" aria-labelledby="page-email-notifications-label" />
          </div>
          <div className="flex items-center justify-between">
            <span id="page-push-notifications-label" className="text-sm">Push notifications</span>
            <input type="checkbox" className="h-4 w-4" aria-labelledby="page-push-notifications-label" />
          </div>
        </div>
      </SettingsCard>
    </div>
  ),
};
