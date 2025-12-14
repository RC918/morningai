import type { Meta, StoryObj } from "@storybook/react";
import { Activity, Cpu, Clock, Users, Zap, TrendingUp } from "lucide-react";

import { MetricCard } from "./metric-card";

const meta = {
  title: "Dashboard/MetricCard",
  component: MetricCard,
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
    trend: {
      control: "select",
      options: [undefined, "up", "down", "stable"],
      description: "Trend direction indicator",
    },
    progress: {
      control: { type: "range", min: 0, max: 100 },
      description: "Progress value (0-100)",
    },
  },
} satisfies Meta<typeof MetricCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    title: "Response Time",
    value: 245,
    unit: "ms",
    icon: <Clock />,
    description: "Average response time",
  },
};

export const WithTrendUp: Story = {
  args: {
    title: "Success Rate",
    value: 99.5,
    unit: "%",
    icon: <Activity />,
    trend: "up",
    description: "Last 24 hours",
    variant: "green",
  },
};

export const WithTrendDown: Story = {
  args: {
    title: "Error Rate",
    value: 2.3,
    unit: "%",
    icon: <Zap />,
    trend: "down",
    description: "Decreased from yesterday",
    variant: "red",
  },
};

export const WithTrendStable: Story = {
  args: {
    title: "Active Users",
    value: 1250,
    icon: <Users />,
    trend: "stable",
    description: "No significant change",
    variant: "blue",
  },
};

export const WithProgress: Story = {
  args: {
    title: "CPU Usage",
    value: 67,
    unit: "%",
    icon: <Cpu />,
    progress: 67,
    description: "Current utilization",
    variant: "yellow",
  },
};

export const WithProgressAndTrend: Story = {
  args: {
    title: "Task Completion",
    value: 85,
    unit: "%",
    icon: <TrendingUp />,
    trend: "up",
    progress: 85,
    description: "Sprint progress",
    variant: "green",
  },
};

export const StringValue: Story = {
  args: {
    title: "Status",
    value: "Healthy",
    icon: <Activity />,
    description: "All systems operational",
    variant: "green",
  },
};

export const NoIcon: Story = {
  args: {
    title: "Total Requests",
    value: 12500,
    unit: "req/min",
    trend: "up",
    description: "Peak traffic",
  },
};

export const MinimalCard: Story = {
  args: {
    title: "Metric",
    value: 42,
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <MetricCard
        title="Default Variant"
        value={100}
        icon={<Activity />}
        variant="default"
      />
      <MetricCard
        title="Blue Variant"
        value={200}
        icon={<Activity />}
        variant="blue"
      />
      <MetricCard
        title="Green Variant"
        value={300}
        icon={<Activity />}
        variant="green"
      />
      <MetricCard
        title="Yellow Variant"
        value={400}
        icon={<Activity />}
        variant="yellow"
      />
      <MetricCard
        title="Red Variant"
        value={500}
        icon={<Activity />}
        variant="red"
      />
      <MetricCard
        title="Purple Variant"
        value={600}
        icon={<Activity />}
        variant="purple"
      />
    </div>
  ),
};

export const AllTrends: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <MetricCard
        title="Trending Up"
        value={95.5}
        unit="%"
        icon={<Activity />}
        trend="up"
        variant="green"
      />
      <MetricCard
        title="Trending Down"
        value={4.2}
        unit="%"
        icon={<Activity />}
        trend="down"
        variant="red"
      />
      <MetricCard
        title="Stable"
        value={50}
        unit="%"
        icon={<Activity />}
        trend="stable"
        variant="default"
      />
    </div>
  ),
};

export const DashboardExample: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <MetricCard
        title="Response Time"
        value={245}
        unit="ms"
        icon={<Clock />}
        trend="down"
        description="Improved by 12%"
        variant="green"
      />
      <MetricCard
        title="Success Rate"
        value={99.8}
        unit="%"
        icon={<Activity />}
        trend="up"
        progress={99.8}
        variant="green"
      />
      <MetricCard
        title="Active Users"
        value={1250}
        icon={<Users />}
        trend="stable"
        description="Online now"
        variant="blue"
      />
      <MetricCard
        title="CPU Usage"
        value={67}
        unit="%"
        icon={<Cpu />}
        progress={67}
        description="4 cores active"
        variant="yellow"
      />
    </div>
  ),
};
