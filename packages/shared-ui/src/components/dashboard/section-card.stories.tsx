import type { Meta, StoryObj } from "@storybook/react";
import {
  BarChart3,
  PieChart,
  Activity,
  TrendingUp,
  Users,
  Calendar,
  FileText,
  Beaker,
} from "lucide-react";

import { SectionCard } from "./section-card";

const meta = {
  title: "Dashboard/SectionCard",
  component: SectionCard,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  argTypes: {
    icon: {
      control: false,
      description: "Optional icon to display next to the title",
    },
    action: {
      control: false,
      description: "Optional action element (e.g., button, link) in the header",
    },
  },
} satisfies Meta<typeof SectionCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "Overview",
    subtitle: "Summary of key metrics",
    children: (
      <div className="text-sm text-[var(--text-secondary)]">
        Content goes here
      </div>
    ),
  },
};

export const WithIcon: Story = {
  args: {
    title: "Analytics",
    subtitle: "Performance metrics over time",
    icon: <BarChart3 className="w-5 h-5" />,
    children: (
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm">Page Views</span>
          <span className="text-sm font-medium">12,345</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Unique Visitors</span>
          <span className="text-sm font-medium">8,901</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-sm">Bounce Rate</span>
          <span className="text-sm font-medium">32.5%</span>
        </div>
      </div>
    ),
  },
};

export const WithAction: Story = {
  args: {
    title: "Recent Activity",
    subtitle: "Latest updates from your team",
    icon: <Activity className="w-5 h-5" />,
    action: (
      <button className="text-[var(--primary-500)] hover:text-[var(--primary-600)] font-medium">
        View All
      </button>
    ),
    children: (
      <div className="space-y-3">
        <div className="flex items-center gap-3 p-2 rounded-lg bg-[var(--surface-secondary)]">
          <div className="w-8 h-8 rounded-full bg-[var(--primary-100)] flex items-center justify-center">
            <Users className="w-4 h-4 text-[var(--primary-500)]" />
          </div>
          <div>
            <p className="text-sm font-medium">New team member joined</p>
            <p className="text-xs text-[var(--text-secondary)]">2 hours ago</p>
          </div>
        </div>
        <div className="flex items-center gap-3 p-2 rounded-lg bg-[var(--surface-secondary)]">
          <div className="w-8 h-8 rounded-full bg-[var(--success-100)] flex items-center justify-center">
            <FileText className="w-4 h-4 text-[var(--success-500)]" />
          </div>
          <div>
            <p className="text-sm font-medium">Report generated</p>
            <p className="text-xs text-[var(--text-secondary)]">5 hours ago</p>
          </div>
        </div>
      </div>
    ),
  },
};

export const ChartSection: Story = {
  args: {
    title: "Distribution",
    subtitle: "Breakdown by category",
    icon: <PieChart className="w-5 h-5" />,
    children: (
      <div className="space-y-4">
        {[
          { label: "Category A", value: 45, color: "bg-[var(--primary-500)]" },
          { label: "Category B", value: 30, color: "bg-[var(--success-500)]" },
          { label: "Category C", value: 15, color: "bg-[var(--warning-500)]" },
          { label: "Category D", value: 10, color: "bg-[var(--error-500)]" },
        ].map((item) => (
          <div key={item.label} className="space-y-1">
            <div className="flex items-center justify-between text-sm">
              <span>{item.label}</span>
              <span className="font-medium">{item.value}%</span>
            </div>
            <div className="h-2 bg-[var(--surface-secondary)] rounded-full overflow-hidden">
              <div
                className={`h-full ${item.color} rounded-full`}
                style={{ width: `${item.value}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    ),
  },
};

export const ExperimentComparison: Story = {
  args: {
    title: "Experiment Comparison",
    subtitle: "Control vs Treatment performance metrics",
    icon: <Beaker className="w-5 h-5" />,
    children: (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4">
          <div className="p-3 rounded-lg bg-[var(--surface-secondary)]">
            <p className="text-xs text-[var(--text-secondary)] mb-1">Control</p>
            <p className="text-2xl font-semibold">72.3%</p>
            <p className="text-xs text-[var(--text-secondary)]">Success Rate</p>
          </div>
          <div className="p-3 rounded-lg bg-[var(--surface-secondary)]">
            <p className="text-xs text-[var(--text-secondary)] mb-1">Treatment</p>
            <p className="text-2xl font-semibold text-[var(--success-500)]">85.7%</p>
            <p className="text-xs text-[var(--text-secondary)]">Success Rate</p>
          </div>
        </div>
        <div className="flex items-center gap-2 text-sm">
          <TrendingUp className="w-4 h-4 text-[var(--success-500)]" />
          <span className="text-[var(--success-500)] font-medium">+13.4%</span>
          <span className="text-[var(--text-secondary)]">improvement</span>
        </div>
      </div>
    ),
  },
};

export const ScheduleSection: Story = {
  args: {
    title: "Upcoming Events",
    subtitle: "Your schedule for this week",
    icon: <Calendar className="w-5 h-5" />,
    action: (
      <button className="px-2 py-1 text-xs bg-[var(--primary-500)] text-white rounded-md">
        Add Event
      </button>
    ),
    children: (
      <div className="space-y-3">
        {[
          { time: "09:00 AM", title: "Team Standup", type: "Meeting" },
          { time: "11:30 AM", title: "Design Review", type: "Review" },
          { time: "02:00 PM", title: "Sprint Planning", type: "Planning" },
        ].map((event, index) => (
          <div
            key={index}
            className="flex items-center justify-between p-2 border-l-2 border-[var(--primary-500)] pl-3"
          >
            <div>
              <p className="text-sm font-medium">{event.title}</p>
              <p className="text-xs text-[var(--text-secondary)]">{event.time}</p>
            </div>
            <span className="text-xs px-2 py-1 bg-[var(--surface-secondary)] rounded">
              {event.type}
            </span>
          </div>
        ))}
      </div>
    ),
  },
};

export const WithoutSubtitle: Story = {
  args: {
    title: "Quick Stats",
    icon: <TrendingUp className="w-5 h-5" />,
    children: (
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-2xl font-semibold">1,234</p>
          <p className="text-xs text-[var(--text-secondary)]">Total</p>
        </div>
        <div>
          <p className="text-2xl font-semibold text-[var(--success-500)]">89%</p>
          <p className="text-xs text-[var(--text-secondary)]">Success</p>
        </div>
        <div>
          <p className="text-2xl font-semibold text-[var(--error-500)]">11%</p>
          <p className="text-xs text-[var(--text-secondary)]">Failed</p>
        </div>
      </div>
    ),
  },
};

export const DashboardExample: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <SectionCard
        title="Top Failure Types"
        subtitle="Distribution of error types in failed workflows"
        icon={<PieChart className="w-5 h-5" />}
      >
        <div className="space-y-3">
          {[
            { type: "TIMEOUT", count: 45, percentage: 35 },
            { type: "API_ERROR", count: 32, percentage: 25 },
            { type: "VALIDATION", count: 26, percentage: 20 },
            { type: "AUTH_FAILED", count: 25, percentage: 20 },
          ].map((item) => (
            <div key={item.type} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <span className="px-2 py-0.5 bg-[var(--surface-secondary)] rounded text-xs font-medium">
                  {item.type}
                </span>
                <span>{item.count}</span>
              </div>
              <div className="h-2 bg-[var(--surface-secondary)] rounded-full overflow-hidden">
                <div
                  className="h-full bg-[var(--primary-500)] rounded-full"
                  style={{ width: `${item.percentage}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      </SectionCard>

      <SectionCard
        title="Fixer Retry Distribution"
        subtitle="Number of fixer iterations per workflow"
        icon={<BarChart3 className="w-5 h-5" />}
      >
        <div className="space-y-3">
          {[1, 2, 3, 4, 5].map((iteration) => {
            const count = Math.floor(Math.random() * 50) + 10;
            const percentage = (count / 60) * 100;
            return (
              <div key={iteration} className="space-y-1">
                <div className="flex items-center justify-between text-sm">
                  <span>Iteration {iteration}</span>
                  <span className="font-medium">{count}</span>
                </div>
                <div className="h-2 bg-[var(--surface-secondary)] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-[var(--success-500)] rounded-full"
                    style={{ width: `${percentage}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </SectionCard>
    </div>
  ),
};
