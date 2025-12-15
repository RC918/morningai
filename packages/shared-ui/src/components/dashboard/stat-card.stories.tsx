import type { Meta, StoryObj } from "@storybook/react";
import { Activity, Users, DollarSign, TrendingUp, Clock, Zap, Target, CheckCircle } from "lucide-react";

import { StatCard } from "./stat-card";

const meta = {
  title: "Dashboard/StatCard",
  component: StatCard,
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
    deltaPositive: {
      control: "select",
      options: [true, false, "neutral"],
      description: "Whether the delta represents a positive change (green), negative change (red), or neutral info (gray)",
    },
  },
} satisfies Meta<typeof StatCard>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    label: "Total Revenue",
    value: "$45,231",
    icon: <DollarSign />,
  },
};

export const WithDeltaPositive: Story = {
  args: {
    label: "Success Rate",
    value: "98.5%",
    icon: <Activity />,
    deltaLabel: "+5.10% from last month",
    deltaPositive: true,
    variant: "green",
  },
};

export const WithDeltaNegative: Story = {
  args: {
    label: "Error Rate",
    value: "2.3%",
    icon: <Zap />,
    deltaLabel: "+0.5% from last week",
    deltaPositive: false,
    variant: "red",
  },
};

export const WithDeltaNeutral: Story = {
  args: {
    label: "Active Users",
    value: "1,234",
    icon: <Users />,
    deltaLabel: "Target: 1,500",
    deltaPositive: "neutral",
    variant: "blue",
  },
};

export const WithBadge: Story = {
  args: {
    label: "Task Completion",
    value: "85%",
    icon: <Target />,
    badge: "On Target",
    deltaLabel: "+12% this sprint",
    deltaPositive: true,
    variant: "green",
  },
};

export const WithBadgeBelowTarget: Story = {
  args: {
    label: "Response Time",
    value: "450ms",
    icon: <Clock />,
    badge: "Below Target",
    deltaLabel: "Target: 200ms",
    deltaPositive: "neutral",
    variant: "yellow",
  },
};

export const MinimalCard: Story = {
  args: {
    label: "Total Count",
    value: "42",
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
      <StatCard
        label="Default Variant"
        value="100"
        icon={<Activity />}
        variant="default"
      />
      <StatCard
        label="Blue Variant"
        value="200"
        icon={<Activity />}
        variant="blue"
      />
      <StatCard
        label="Green Variant"
        value="300"
        icon={<Activity />}
        variant="green"
      />
      <StatCard
        label="Yellow Variant"
        value="400"
        icon={<Activity />}
        variant="yellow"
      />
      <StatCard
        label="Red Variant"
        value="500"
        icon={<Activity />}
        variant="red"
      />
      <StatCard
        label="Purple Variant"
        value="600"
        icon={<Activity />}
        variant="purple"
      />
    </div>
  ),
};

export const AllDeltaStates: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        label="Positive Delta"
        value="95.5%"
        icon={<TrendingUp />}
        deltaLabel="+12.5% increase"
        deltaPositive={true}
        variant="green"
      />
      <StatCard
        label="Negative Delta"
        value="4.2%"
        icon={<Zap />}
        deltaLabel="+1.2% increase"
        deltaPositive={false}
        variant="red"
      />
      <StatCard
        label="Neutral Delta"
        value="50%"
        icon={<Target />}
        deltaLabel="Target: 60%"
        deltaPositive="neutral"
        variant="default"
      />
    </div>
  ),
};

export const DashboardExample: Story = {
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      <StatCard
        label="Total Revenue"
        value="$45,231"
        icon={<DollarSign />}
        deltaLabel="+20.1% from last month"
        deltaPositive={true}
        variant="green"
      />
      <StatCard
        label="Active Users"
        value="2,350"
        icon={<Users />}
        deltaLabel="+180 this week"
        deltaPositive={true}
        variant="blue"
      />
      <StatCard
        label="Success Rate"
        value="98.5%"
        icon={<CheckCircle />}
        badge="On Target"
        deltaLabel="Target: 95%"
        deltaPositive="neutral"
        variant="green"
      />
      <StatCard
        label="Avg Response Time"
        value="245ms"
        icon={<Clock />}
        deltaLabel="-12ms from yesterday"
        deltaPositive={true}
        variant="default"
      />
    </div>
  ),
};

export const WithDeprecatedTrend: Story = {
  name: "With Deprecated Trend Prop",
  args: {
    label: "Legacy Usage",
    value: "100",
    icon: <Activity />,
    trend: "+5% (using deprecated trend prop)",
  },
};

export const WithI18n: Story = {
  name: "With i18n (Chinese)",
  render: () => (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <StatCard
        label="總收入"
        value="$45,231"
        icon={<DollarSign />}
        deltaLabel="+20.1% 較上月"
        deltaPositive={true}
        variant="green"
      />
      <StatCard
        label="活躍用戶"
        value="2,350"
        icon={<Users />}
        badge="達標"
        deltaLabel="目標: 2,000"
        deltaPositive="neutral"
        variant="blue"
      />
      <StatCard
        label="錯誤率"
        value="2.3%"
        icon={<Zap />}
        badge="低於目標"
        deltaLabel="+0.5% 較上週"
        deltaPositive={false}
        variant="red"
      />
    </div>
  ),
};
