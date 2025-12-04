import type { Meta, StoryObj } from '@storybook/react'
import { Shield, Users, Activity, AlertTriangle, TrendingUp, DollarSign } from 'lucide-react'
import { PageScaffold } from './page-scaffold'
import { StatCard } from '../dashboard/stat-card'
import { SectionCard } from '../dashboard/section-card'
import { Alert, AlertDescription } from './alert'
import { Button } from './button'

const meta = {
  title: 'Layout/PageScaffold',
  component: PageScaffold,
  parameters: {
    layout: 'padded',
  },
  tags: ['autodocs'],
  argTypes: {
    title: {
      control: 'text',
      description: 'Page title - rendered as h1',
    },
    subtitle: {
      control: 'text',
      description: 'Optional subtitle below the title',
    },
    titleIcon: {
      description: 'Optional icon displayed before the title',
    },
    actions: {
      description: 'Optional action buttons/elements aligned to the right',
    },
    banner: {
      description: 'Optional banner/alert content displayed below the header',
    },
    kpis: {
      description: 'Optional KPI row content (e.g., StatCard components)',
    },
  },
} satisfies Meta<typeof PageScaffold>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    title: 'Dashboard',
    subtitle: 'Overview of your platform metrics and activity',
    children: (
      <SectionCard title="Recent Activity" subtitle="Latest events from your platform">
        <div className="space-y-2">
          <p className="text-sm text-[var(--text-secondary)]">No recent activity to display.</p>
        </div>
      </SectionCard>
    ),
  },
}

export const WithTitleIcon: Story = {
  args: {
    title: 'Agent Governance',
    subtitle: 'Monitor and manage AI agent permissions and behavior',
    titleIcon: <Shield className="w-6 h-6" />,
    children: (
      <SectionCard title="Agents" subtitle="All registered agents">
        <div className="space-y-2">
          <p className="text-sm text-[var(--text-secondary)]">No agents registered yet.</p>
        </div>
      </SectionCard>
    ),
  },
}

export const WithActions: Story = {
  args: {
    title: 'Tenant Management',
    subtitle: 'Manage your organization tenants',
    titleIcon: <Users className="w-6 h-6" />,
    actions: (
      <>
        <Button variant="outline" size="sm">
          <Activity className="w-4 h-4 mr-2" />
          Refresh
        </Button>
        <Button size="sm">
          Add Tenant
        </Button>
      </>
    ),
    children: (
      <SectionCard title="Tenants" subtitle="All registered tenants">
        <div className="space-y-2">
          <p className="text-sm text-[var(--text-secondary)]">No tenants registered yet.</p>
        </div>
      </SectionCard>
    ),
  },
}

export const WithBanner: Story = {
  args: {
    title: 'System Monitoring',
    subtitle: 'Monitor system health and performance',
    actions: (
      <Button variant="outline" size="sm">
        <Activity className="w-4 h-4 mr-2" />
        Refresh
      </Button>
    ),
    banner: (
      <Alert className="bg-warning-50 border-warning-200">
        <AlertTriangle className="h-4 w-4 text-warning-600" />
        <AlertDescription className="text-warning-800">
          System maintenance scheduled for tonight at 2:00 AM UTC. Some services may be temporarily unavailable.
        </AlertDescription>
      </Alert>
    ),
    children: (
      <SectionCard title="System Status" subtitle="Current system health">
        <div className="space-y-2">
          <p className="text-sm text-[var(--text-secondary)]">All systems operational.</p>
        </div>
      </SectionCard>
    ),
  },
}

export const WithKPIs: Story = {
  args: {
    title: 'Agent Governance',
    subtitle: 'Monitor and manage AI agent permissions and behavior',
    titleIcon: <Shield className="w-6 h-6" />,
    actions: (
      <Button variant="outline" size="sm">
        <Activity className="w-4 h-4 mr-2" />
        Refresh
      </Button>
    ),
    kpis: (
      <>
        <StatCard
          label="Total Agents"
          value="5"
          icon={<Shield className="w-5 h-5" />}
        />
        <StatCard
          label="Avg Reputation"
          value="106"
          icon={<TrendingUp className="w-5 h-5" />}
          variant="green"
        />
        <StatCard
          label="Daily Cost"
          value="$12.50"
          icon={<DollarSign className="w-5 h-5" />}
          variant="yellow"
        />
        <StatCard
          label="Violations"
          value="0"
          icon={<AlertTriangle className="w-5 h-5" />}
          variant="green"
        />
      </>
    ),
    children: (
      <SectionCard title="Agents" subtitle="All registered agents">
        <div className="space-y-2">
          <p className="text-sm text-[var(--text-secondary)]">No agents registered yet.</p>
        </div>
      </SectionCard>
    ),
  },
}

export const FullExample: Story = {
  args: {
    title: 'Agent Governance',
    subtitle: 'Monitor and manage AI agent permissions and behavior',
    titleIcon: <Shield className="w-6 h-6" />,
    actions: (
      <Button variant="outline" size="sm">
        <Activity className="w-4 h-4 mr-2" />
        Refresh
      </Button>
    ),
    banner: (
      <Alert className="bg-error-50 border-error-200">
        <AlertTriangle className="h-4 w-4 text-error-600" />
        <AlertDescription className="text-error-800">
          2 agents have exceeded their budget limits. Please review and take action.
        </AlertDescription>
      </Alert>
    ),
    kpis: (
      <>
        <StatCard
          label="Total Agents"
          value="5"
          icon={<Shield className="w-5 h-5" />}
        />
        <StatCard
          label="Avg Reputation"
          value="106"
          icon={<TrendingUp className="w-5 h-5" />}
          variant="green"
        />
        <StatCard
          label="Daily Cost"
          value="$12.50"
          icon={<DollarSign className="w-5 h-5" />}
          variant="yellow"
        />
        <StatCard
          label="Violations"
          value="2"
          icon={<AlertTriangle className="w-5 h-5" />}
          variant="red"
        />
      </>
    ),
    children: (
      <div className="space-y-6">
        <SectionCard title="Active Agents" subtitle="Currently running agents">
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
              <div>
                <p className="font-medium text-[var(--text-primary)]">Customer Support Bot</p>
                <p className="text-sm text-[var(--text-secondary)]">ID: agent-001</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-success-100 text-success-800">Active</span>
            </div>
            <div className="flex items-center justify-between p-3 rounded-lg border border-[var(--border)] bg-[var(--surface)]">
              <div>
                <p className="font-medium text-[var(--text-primary)]">Data Analysis Agent</p>
                <p className="text-sm text-[var(--text-secondary)]">ID: agent-002</p>
              </div>
              <span className="px-2 py-1 text-xs font-medium rounded-full bg-warning-100 text-warning-800">Paused</span>
            </div>
          </div>
        </SectionCard>
        <SectionCard title="Recent Violations" subtitle="Policy violations in the last 24 hours">
          <div className="space-y-2">
            <div className="flex items-start gap-3 p-3 rounded-lg border border-error-200 bg-error-50">
              <AlertTriangle className="w-5 h-5 text-error-600 mt-0.5" />
              <div>
                <p className="font-medium text-error-900">Budget Exceeded</p>
                <p className="text-sm text-error-700">Agent agent-003 exceeded daily budget by $5.20</p>
              </div>
            </div>
          </div>
        </SectionCard>
      </div>
    ),
  },
}
