import type { Meta, StoryObj } from "@storybook/react";
import { StatCard } from "./stat-card";
import { SectionCard } from "./section-card";
import { TimelineList } from "./timeline-list";
import { SystemStatusList } from "./system-status-list";
import { ProgressTrack } from "./progress-track";

const statCardMeta = {
  title: "Dashboard/StatCard",
  component: StatCard,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
  argTypes: {
    label: {
      control: "text",
      description: "Label text displayed above the value",
    },
    value: {
      control: "text",
      description: "Main value to display",
    },
    trend: {
      control: "text",
      description: "Optional trend indicator (deprecated, use deltaLabel)",
    },
    badge: {
      control: "text",
      description: "Optional badge text",
    },
    deltaLabel: {
      control: "text",
      description: "Delta/change label (e.g., +5.10%, -2 this month)",
    },
    deltaPositive: {
      control: "boolean",
      description: "Whether the delta is positive (green) or negative (red)",
    },
    variant: {
      control: "select",
      options: ["default", "blue", "green", "yellow", "red", "purple"],
      description: "Color variant for the icon background",
    },
  },
} satisfies Meta<typeof StatCard>;

export default statCardMeta;
type StatCardStory = StoryObj<typeof statCardMeta>;

export const StatCardDefault: StatCardStory = {
  args: {
    label: "Total Tenants",
    value: "12",
  },
};

export const StatCardWithTrend: StatCardStory = {
  args: {
    label: "Total Tenants",
    value: "12",
    trend: "+2 this month",
  },
};

export const StatCardWithBadge: StatCardStory = {
  args: {
    label: "Active Agents",
    value: "45",
    badge: "Cross-tenant",
  },
};

export const StatCardWithTrendAndBadge: StatCardStory = {
  args: {
    label: "Monthly Revenue",
    value: "$12,345",
    trend: "+15%",
    badge: "New",
  },
};

export const StatCardWithIcon: StatCardStory = {
  args: {
    label: "Tasks Overview",
    value: "345",
    deltaLabel: "+5.10%",
    deltaPositive: true,
    variant: "blue",
    icon: <span className="text-lg">📊</span>,
  },
};

export const StatCardWithNegativeDelta: StatCardStory = {
  args: {
    label: "Error Rate",
    value: "2.3%",
    deltaLabel: "+0.5% from last week",
    deltaPositive: false,
    variant: "red",
    icon: <span className="text-lg">⚠️</span>,
  },
};

export const StatCardVariants: StoryObj = {
  render: () => (
    <div className="grid gap-4 md:grid-cols-3 w-[700px]">
      <StatCard
        label="Revenue"
        value="$12,345"
        deltaLabel="+12%"
        deltaPositive={true}
        variant="green"
        icon={<span className="text-lg">💰</span>}
      />
      <StatCard
        label="Users"
        value="1,234"
        deltaLabel="+5.10%"
        deltaPositive={true}
        variant="blue"
        icon={<span className="text-lg">👥</span>}
      />
      <StatCard
        label="Errors"
        value="23"
        deltaLabel="+3%"
        deltaPositive={false}
        variant="yellow"
        icon={<span className="text-lg">⚡</span>}
      />
    </div>
  ),
};

export const StatCardGrid: StoryObj = {
  render: () => (
    <div className="grid gap-4 md:grid-cols-4 w-[900px]">
      <StatCard label="Total Tenants" value="12" trend="+2 this month" />
      <StatCard label="Active Agents" value="45" badge="Cross-tenant" />
      <StatCard label="Monthly Cost" value="$1,234" />
      <StatCard label="System Health" value="98.5%" />
    </div>
  ),
};

const sectionCardMeta = {
  title: "Dashboard/SectionCard",
  component: SectionCard,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof SectionCard>;

export const SectionCardDefault: StoryObj<typeof SectionCard> = {
  render: () => (
    <div className="w-[400px]">
      <SectionCard title="Recent Activity" subtitle="Latest platform events">
        <p className="text-sm text-neutral-600">Content goes here...</p>
      </SectionCard>
    </div>
  ),
};

export const SectionCardWithAction: StoryObj<typeof SectionCard> = {
  render: () => (
    <div className="w-[400px]">
      <SectionCard
        title="Platform Progress"
        subtitle="Track core development tasks"
        action={
          <button className="text-primary-600 hover:text-primary-700">
            View All
          </button>
        }
      >
        <p className="text-sm text-neutral-600">Content with action button...</p>
      </SectionCard>
    </div>
  ),
};

const timelineListMeta = {
  title: "Dashboard/TimelineList",
  component: TimelineList,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof TimelineList>;

const sampleTimelineItems = [
  { id: "1", title: "New Tenant Registered", desc: "Acme Corp", time: "5 min ago" },
  { id: "2", title: "Agent Updated", desc: "FAQ-Agent v1.3", time: "30 min ago" },
  { id: "3", title: "Policy Changed", desc: "Data retention updated", time: "1 hour ago" },
  { id: "4", title: "User Invited", desc: "john@acme.com", time: "2 hours ago" },
];

export const TimelineListDefault: StoryObj<typeof TimelineList> = {
  render: () => (
    <div className="w-[400px]">
      <TimelineList items={sampleTimelineItems} />
    </div>
  ),
};

export const TimelineListInCard: StoryObj<typeof TimelineList> = {
  render: () => (
    <div className="w-[400px]">
      <SectionCard title="Recent Activity" subtitle="Latest platform events">
        <TimelineList items={sampleTimelineItems} />
      </SectionCard>
    </div>
  ),
};

const systemStatusListMeta = {
  title: "Dashboard/SystemStatusList",
  component: SystemStatusList,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof SystemStatusList>;

const sampleStatusItems = [
  { service: "API Backend", status: "Healthy", latency: "220ms" },
  { service: "Database", status: "Healthy", latency: "18ms" },
  { service: "Redis", status: "Healthy", latency: "4ms" },
  { service: "Worker Queue", status: "Healthy", latency: "12ms" },
];

const mixedStatusItems = [
  { service: "API Backend", status: "Healthy", latency: "220ms" },
  { service: "Database", status: "Degraded", latency: "850ms" },
  { service: "Redis", status: "Operational", latency: "4ms" },
  { service: "Worker Queue", status: "Down", latency: "N/A" },
];

export const SystemStatusListDefault: StoryObj<typeof SystemStatusList> = {
  render: () => (
    <div className="w-[400px]">
      <SystemStatusList items={sampleStatusItems} />
    </div>
  ),
};

export const SystemStatusListMixedStatus: StoryObj<typeof SystemStatusList> = {
  render: () => (
    <div className="w-[400px]">
      <SystemStatusList items={mixedStatusItems} />
    </div>
  ),
};

export const SystemStatusListInCard: StoryObj<typeof SystemStatusList> = {
  render: () => (
    <div className="w-[400px]">
      <SectionCard title="System Status" subtitle="Service health overview">
        <SystemStatusList items={sampleStatusItems} />
      </SectionCard>
    </div>
  ),
};

const progressTrackMeta = {
  title: "Dashboard/ProgressTrack",
  component: ProgressTrack,
  parameters: {
    layout: "centered",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof ProgressTrack>;

const sampleProgressItems = [
  { label: "Agent Deployment", value: 85, hint: "Core workflow integrated with Orchestrator" },
  { label: "Data Integration", value: 60, hint: "RLS Phase 3 complete, reports in progress" },
  { label: "Security Audit", value: 45, hint: "2FA/TOTP live, RLS testing ongoing" },
  { label: "Performance Optimization", value: 30, hint: "LangGraph canary, Redis Checkpointer tuning" },
];

export const ProgressTrackDefault: StoryObj<typeof ProgressTrack> = {
  render: () => (
    <div className="w-[400px]">
      <ProgressTrack items={sampleProgressItems} />
    </div>
  ),
};

export const ProgressTrackWithoutHints: StoryObj<typeof ProgressTrack> = {
  render: () => (
    <div className="w-[400px]">
      <ProgressTrack
        items={[
          { label: "Project Alpha", value: 75 },
          { label: "Project Beta", value: 50 },
          { label: "Project Gamma", value: 25 },
        ]}
      />
    </div>
  ),
};

export const ProgressTrackInCard: StoryObj<typeof ProgressTrack> = {
  render: () => (
    <div className="w-[400px]">
      <SectionCard title="Platform Progress" subtitle="Track core development tasks">
        <ProgressTrack items={sampleProgressItems} />
      </SectionCard>
    </div>
  ),
};

export const DashboardLayout: StoryObj = {
  render: () => (
    <div className="space-y-6 p-6 bg-neutral-50 min-h-screen w-[1000px]">
      <div className="grid gap-4 md:grid-cols-4">
        <StatCard label="Total Tenants" value="12" trend="+2 this month" />
        <StatCard label="Active Agents" value="45" badge="Cross-tenant" />
        <StatCard label="Monthly Cost" value="$1,234" />
        <StatCard label="System Health" value="98.5%" />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <SectionCard title="Platform Progress" subtitle="Track core development tasks">
          <ProgressTrack items={sampleProgressItems} />
        </SectionCard>

        <SectionCard title="Recent Activity" subtitle="Latest platform events">
          <TimelineList items={sampleTimelineItems} />
        </SectionCard>

        <SectionCard title="System Status" subtitle="Service health overview">
          <SystemStatusList items={sampleStatusItems} />
        </SectionCard>
      </div>
    </div>
  ),
};
