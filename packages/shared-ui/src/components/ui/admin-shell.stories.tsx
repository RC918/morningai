import type { Meta, StoryObj } from '@storybook/react'
import { Home, Users, Bot, Activity, Shield, Settings } from 'lucide-react'
import { AdminShell } from './admin-shell'
import { AdminSidebar } from './admin-sidebar'
import { AdminTopbar } from './admin-topbar'
import { ActivityListPanel } from '../iotask/activity-list-panel'

const defaultNavItems = [
  { label: "Dashboard", href: "/dashboard", icon: Home, active: true },
  { label: "Agents", href: "/agents", icon: Bot },
  { label: "Tenants", href: "/tenants", icon: Users },
  { label: "Monitoring", href: "/monitoring", icon: Activity },
  { label: "Governance", href: "/governance", icon: Shield },
  { label: "Settings", href: "/settings", icon: Settings },
]

const defaultUser = {
  name: "Platform Owner",
  role: "owner",
}

const userWithAvatar = {
  name: "Platform Owner",
  role: "owner",
  avatar: "/assets/avatar-placeholder.png",
}

const meta = {
  title: 'Admin/AdminShell',
  component: AdminShell,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
  argTypes: {
    navItems: {
      description: 'Navigation items for the sidebar',
    },
    user: {
      description: 'User information displayed in sidebar and topbar',
    },
    appName: {
      control: 'text',
      description: 'Application name displayed in sidebar header',
    },
    appSubtitle: {
      control: 'text',
      description: 'Subtitle displayed below app name',
    },
    topbarTitle: {
      control: 'text',
      description: 'Title displayed in the topbar',
    },
    searchPlaceholder: {
      control: 'text',
      description: 'Placeholder text for search input',
    },
  },
} satisfies Meta<typeof AdminShell>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    navItems: defaultNavItems,
    user: defaultUser,
    children: (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-4">
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">Total Tenants</div>
            <div className="mt-2 text-2xl font-semibold">12</div>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">Active Agents</div>
            <div className="mt-2 text-2xl font-semibold">45</div>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">Monthly Cost</div>
            <div className="mt-2 text-2xl font-semibold">$1,234</div>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">System Health</div>
            <div className="mt-2 text-2xl font-semibold">98.5%</div>
          </div>
        </div>
      </div>
    ),
  },
}

export const WithAvatar: Story = {
  args: {
    navItems: defaultNavItems,
    user: userWithAvatar,
    children: (
      <div className="p-4">
        <h1 className="text-2xl font-semibold">Dashboard with Avatar</h1>
        <p className="text-neutral-500 mt-2">User has a custom avatar image.</p>
      </div>
    ),
  },
}

export const CustomBranding: Story = {
  args: {
    navItems: defaultNavItems,
    user: defaultUser,
    appName: "Acme Corp",
    appSubtitle: "Admin Portal",
    topbarTitle: "Welcome to Acme",
    searchPlaceholder: "Search users, orders...",
    children: (
      <div className="p-4">
        <h1 className="text-2xl font-semibold">Custom Branding</h1>
        <p className="text-neutral-500 mt-2">This shell uses custom app name and subtitle.</p>
      </div>
    ),
  },
}

export const AgentsActive: Story = {
  args: {
    navItems: [
      { label: "Dashboard", href: "/dashboard", icon: Home },
      { label: "Agents", href: "/agents", icon: Bot, active: true },
      { label: "Tenants", href: "/tenants", icon: Users },
      { label: "Monitoring", href: "/monitoring", icon: Activity },
      { label: "Governance", href: "/governance", icon: Shield },
    ],
    user: defaultUser,
    topbarTitle: "Agent Management",
    children: (
      <div className="p-4">
        <h1 className="text-2xl font-semibold">Agents</h1>
        <p className="text-neutral-500 mt-2">Manage your AI agents here.</p>
      </div>
    ),
  },
}

const sampleActivities = [
  {
    id: "1",
    type: "task" as const,
    title: "New agent deployed",
    description: "Customer Support Bot v2.1 is now live",
    timestamp: "2 hours ago",
    user: { name: "System", avatar: undefined },
  },
  {
    id: "2",
    type: "comment" as const,
    title: "Feedback received",
    description: "User reported positive experience with AI assistant",
    timestamp: "4 hours ago",
    user: { name: "John Doe", avatar: undefined },
  },
  {
    id: "3",
    type: "update" as const,
    title: "Configuration updated",
    description: "Response timeout increased to 30s",
    timestamp: "Yesterday",
    user: { name: "Jane Smith", avatar: undefined },
  },
  {
    id: "4",
    type: "milestone" as const,
    title: "10,000 conversations",
    description: "Platform reached 10K total conversations",
    timestamp: "2 days ago",
    user: { name: "System", avatar: undefined },
  },
]

export const ThreeColumnLayout: Story = {
  args: {
    navItems: defaultNavItems,
    user: defaultUser,
    topbarTitle: "Dashboard",
    children: (
      <div className="space-y-6">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">Total Tenants</div>
            <div className="mt-2 text-2xl font-semibold">12</div>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">Active Agents</div>
            <div className="mt-2 text-2xl font-semibold">45</div>
          </div>
          <div className="rounded-xl border border-neutral-200 bg-white p-5 shadow-sm dark:border-neutral-700 dark:bg-neutral-800">
            <div className="text-xs text-neutral-500">System Health</div>
            <div className="mt-2 text-2xl font-semibold">98.5%</div>
          </div>
        </div>
      </div>
    ),
    rightPanel: (
      <ActivityListPanel
        title="Recent Activity"
        activities={sampleActivities}
        seeAllHref="/governance"
      />
    ),
  },
}

const sidebarMeta = {
  title: 'Admin/AdminSidebar',
  component: AdminSidebar,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof AdminSidebar>

export const SidebarDefault: StoryObj<typeof AdminSidebar> = {
  render: () => (
    <div className="h-[600px] border rounded-lg overflow-hidden">
      <AdminSidebar navItems={defaultNavItems} user={defaultUser} />
    </div>
  ),
}

export const SidebarWithAvatar: StoryObj<typeof AdminSidebar> = {
  render: () => (
    <div className="h-[600px] border rounded-lg overflow-hidden">
      <AdminSidebar navItems={defaultNavItems} user={userWithAvatar} />
    </div>
  ),
}

const topbarMeta = {
  title: 'Admin/AdminTopbar',
  component: AdminTopbar,
  parameters: {
    layout: 'fullscreen',
  },
  tags: ['autodocs'],
} satisfies Meta<typeof AdminTopbar>

export const TopbarDefault: StoryObj<typeof AdminTopbar> = {
  render: () => (
    <AdminTopbar user={defaultUser} />
  ),
}

export const TopbarWithAvatar: StoryObj<typeof AdminTopbar> = {
  render: () => (
    <AdminTopbar user={userWithAvatar} />
  ),
}

export const TopbarCustomTitle: StoryObj<typeof AdminTopbar> = {
  render: () => (
    <AdminTopbar 
      user={defaultUser} 
      title="Agent Management" 
      searchPlaceholder="Search agents..."
    />
  ),
}
