import type { Meta, StoryObj } from '@storybook/react'
import { Users, Activity, Settings, ChevronRight } from 'lucide-react'
import { SectionTemplate } from './section-template'
import { PageScaffold } from './page-scaffold'
import { Button } from './button'

const meta = {
  title: 'Layout/SectionTemplate',
  component: SectionTemplate,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Section title - rendered as h2 for plain variant',
    },
    description: {
      control: 'text',
      description: 'Optional description below the title',
    },
    variant: {
      control: 'select',
      options: ['plain', 'card'],
      description: 'Section variant: plain (default) or card',
    },
    actions: {
      description: 'Optional action buttons/elements aligned to the right',
    },
  },
} satisfies Meta<typeof SectionTemplate>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    title: 'Active Tenants',
    description: 'Manage your active tenant accounts',
    children: (
      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
          <div>
            <p className="font-medium text-[var(--text-primary)]">Acme Corp</p>
            <p className="text-sm text-[var(--text-secondary)]">12 active agents</p>
          </div>
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">Active</span>
        </div>
        <div className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
          <div>
            <p className="font-medium text-[var(--text-primary)]">TechStart Inc</p>
            <p className="text-sm text-[var(--text-secondary)]">5 active agents</p>
          </div>
          <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">Active</span>
        </div>
      </div>
    ),
  },
}

export const WithActions: Story = {
  args: {
    title: 'Recent Activity',
    description: 'Latest events from your platform',
    actions: (
      <Button variant="ghost" size="sm">
        View All
        <ChevronRight className="w-4 h-4 ml-1" />
      </Button>
    ),
    children: (
      <div className="space-y-3">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
            <Users className="w-4 h-4 text-primary-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--text-primary)]">New tenant registered</p>
            <p className="text-xs text-[var(--text-secondary)]">Acme Corp joined 5 minutes ago</p>
          </div>
        </div>
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-success-100 flex items-center justify-center">
            <Activity className="w-4 h-4 text-success-600" />
          </div>
          <div>
            <p className="text-sm font-medium text-[var(--text-primary)]">Agent deployed</p>
            <p className="text-xs text-[var(--text-secondary)]">Customer Support Bot is now active</p>
          </div>
        </div>
      </div>
    ),
  },
}

export const CardVariant: Story = {
  args: {
    variant: 'card',
    title: 'System Status',
    description: 'Current system health metrics',
    actions: (
      <Button variant="ghost" size="sm">
        <Activity className="w-4 h-4 mr-1" />
        Refresh
      </Button>
    ),
    children: (
      <div className="space-y-2">
        <div className="flex justify-between">
          <span className="text-sm text-[var(--text-secondary)]">API Backend</span>
          <span className="text-sm font-medium text-success-600">Healthy</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-[var(--text-secondary)]">Database</span>
          <span className="text-sm font-medium text-success-600">Healthy</span>
        </div>
        <div className="flex justify-between">
          <span className="text-sm text-[var(--text-secondary)]">Redis Cache</span>
          <span className="text-sm font-medium text-success-600">Healthy</span>
        </div>
      </div>
    ),
  },
}

export const PlainVariant: Story = {
  args: {
    variant: 'plain',
    title: 'Configuration',
    description: 'Manage your system settings',
    actions: (
      <Button variant="outline" size="sm">
        <Settings className="w-4 h-4 mr-1" />
        Edit
      </Button>
    ),
    children: (
      <div className="space-y-4">
        <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
          <h3 className="text-sm font-medium text-[var(--text-primary)]">API Settings</h3>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Configure API rate limits and authentication</p>
        </div>
        <div className="p-4 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
          <h3 className="text-sm font-medium text-[var(--text-primary)]">Notification Settings</h3>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">Manage email and webhook notifications</p>
        </div>
      </div>
    ),
  },
}

export const InsidePageScaffold: Story = {
  render: () => (
    <PageScaffold
      title="Tenant Management"
      subtitle="Manage your organization tenants and their configurations"
      titleIcon={<Users className="w-6 h-6" />}
      actions={
        <Button size="sm">
          Add Tenant
        </Button>
      }
    >
      <SectionTemplate
        title="Active Tenants"
        description="Currently active tenant accounts"
        actions={
          <Button variant="ghost" size="sm">
            View All
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        }
      >
        <div className="space-y-3">
          <div className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div>
              <p className="font-medium text-[var(--text-primary)]">Acme Corp</p>
              <p className="text-sm text-[var(--text-secondary)]">12 active agents</p>
            </div>
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">Active</span>
          </div>
          <div className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div>
              <p className="font-medium text-[var(--text-primary)]">TechStart Inc</p>
              <p className="text-sm text-[var(--text-secondary)]">5 active agents</p>
            </div>
            <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">Active</span>
          </div>
        </div>
      </SectionTemplate>

      <SectionTemplate
        variant="card"
        title="Pending Approvals"
        description="Tenants awaiting approval"
        actions={
          <Button variant="ghost" size="sm">
            Review All
          </Button>
        }
      >
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">NewCo Ltd</p>
              <p className="text-xs text-[var(--text-secondary)]">Applied 2 hours ago</p>
            </div>
            <div className="flex gap-2">
              <Button variant="outline" size="sm">Reject</Button>
              <Button size="sm">Approve</Button>
            </div>
          </div>
        </div>
      </SectionTemplate>
    </PageScaffold>
  ),
}

export const MultipleSections: Story = {
  render: () => (
    <PageScaffold
      title="Dashboard"
      subtitle="Overview of your platform metrics and activity"
    >
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <SectionTemplate
          variant="card"
          title="Quick Stats"
          description="Key metrics at a glance"
        >
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Total Tenants</span>
              <span className="text-sm font-semibold text-[var(--text-primary)]">12</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Active Agents</span>
              <span className="text-sm font-semibold text-[var(--text-primary)]">45</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Monthly Cost</span>
              <span className="text-sm font-semibold text-[var(--text-primary)]">$1,234.56</span>
            </div>
          </div>
        </SectionTemplate>

        <SectionTemplate
          variant="card"
          title="System Health"
          description="Current system status"
        >
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-secondary)]">API</span>
              <span className="text-sm font-medium text-success-600">Operational</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Database</span>
              <span className="text-sm font-medium text-success-600">Operational</span>
            </div>
            <div className="flex justify-between">
              <span className="text-sm text-[var(--text-secondary)]">Workers</span>
              <span className="text-sm font-medium text-success-600">Operational</span>
            </div>
          </div>
        </SectionTemplate>
      </div>

      <SectionTemplate
        title="Recent Activity"
        description="Latest events from your platform"
        actions={
          <Button variant="ghost" size="sm">
            View All
            <ChevronRight className="w-4 h-4 ml-1" />
          </Button>
        }
      >
        <div className="space-y-3">
          <div className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div className="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
              <Users className="w-4 h-4 text-primary-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">New tenant registered</p>
              <p className="text-xs text-[var(--text-secondary)]">Acme Corp joined 5 minutes ago</p>
            </div>
          </div>
          <div className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
            <div className="w-8 h-8 rounded-full bg-success-100 flex items-center justify-center">
              <Activity className="w-4 h-4 text-success-600" />
            </div>
            <div>
              <p className="text-sm font-medium text-[var(--text-primary)]">Agent deployed</p>
              <p className="text-xs text-[var(--text-secondary)]">Customer Support Bot is now active</p>
            </div>
          </div>
        </div>
      </SectionTemplate>
    </PageScaffold>
  ),
}
