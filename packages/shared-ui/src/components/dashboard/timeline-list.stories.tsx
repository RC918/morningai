import type { Meta, StoryObj } from "@storybook/react";

import { TimelineList } from "./timeline-list";

const meta = {
  title: "Dashboard/TimelineList",
  component: TimelineList,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
} satisfies Meta<typeof TimelineList>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    items: [
      {
        id: "1",
        title: "Deployment completed",
        desc: "Production environment updated",
        time: "2 min ago",
      },
      {
        id: "2",
        title: "Tests passed",
        desc: "All 156 tests passed",
        time: "5 min ago",
      },
      {
        id: "3",
        title: "Code review approved",
        desc: "PR #234 merged to main",
        time: "15 min ago",
      },
    ],
  },
};

export const SingleItem: Story = {
  args: {
    items: [
      {
        id: "1",
        title: "System started",
        desc: "All services initialized",
        time: "Just now",
      },
    ],
  },
};

export const ManyItems: Story = {
  args: {
    items: [
      { id: "1", title: "Alert resolved", desc: "CPU usage normalized", time: "1 min ago" },
      { id: "2", title: "New user registered", desc: "user@example.com", time: "3 min ago" },
      { id: "3", title: "Payment processed", desc: "Order #12345", time: "5 min ago" },
      { id: "4", title: "Report generated", desc: "Monthly analytics", time: "10 min ago" },
      { id: "5", title: "Backup completed", desc: "Database snapshot saved", time: "15 min ago" },
      { id: "6", title: "Cache cleared", desc: "Redis cache flushed", time: "20 min ago" },
    ],
  },
};

export const ActivityLog: Story = {
  args: {
    items: [
      { id: "1", title: "John updated settings", desc: "Changed notification preferences", time: "2 min ago" },
      { id: "2", title: "Sarah created a new agent", desc: "Agent: Customer Support Bot", time: "1 hour ago" },
      { id: "3", title: "System maintenance", desc: "Scheduled downtime completed", time: "3 hours ago" },
      { id: "4", title: "API rate limit reached", desc: "Throttling applied", time: "5 hours ago" },
    ],
  },
};

export const DashboardExample: Story = {
  render: () => (
    <div className="max-w-md rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card">
      <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
        Recent Activity
      </h3>
      <TimelineList
        items={[
          { id: "1", title: "Deployment completed", desc: "v2.1.0 released", time: "2 min ago" },
          { id: "2", title: "Tests passed", desc: "CI pipeline succeeded", time: "5 min ago" },
          { id: "3", title: "PR merged", desc: "#234 - Add new feature", time: "15 min ago" },
        ]}
      />
    </div>
  ),
};

export const WithI18n: Story = {
  name: "With i18n (Chinese)",
  args: {
    items: [
      { id: "1", title: "部署完成", desc: "生產環境已更新", time: "2 分鐘前" },
      { id: "2", title: "測試通過", desc: "所有 156 個測試通過", time: "5 分鐘前" },
      { id: "3", title: "程式碼審查通過", desc: "PR #234 已合併至 main", time: "15 分鐘前" },
    ],
  },
};
