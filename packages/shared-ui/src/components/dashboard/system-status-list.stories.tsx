import type { Meta, StoryObj } from "@storybook/react";

import { SystemStatusList } from "./system-status-list";

const meta = {
  title: "Dashboard/SystemStatusList",
  component: SystemStatusList,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  args: {
    items: [],
  },
} satisfies Meta<typeof SystemStatusList>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    items: [
      { service: "API Gateway", status: "Healthy", latency: "45ms" },
      { service: "Database", status: "Operational", latency: "12ms" },
      { service: "Cache Server", status: "Healthy", latency: "3ms" },
    ],
  },
};

export const AllHealthy: Story = {
  args: {
    items: [
      { service: "Web Server", status: "Healthy", latency: "23ms" },
      { service: "API Server", status: "Healthy", latency: "45ms" },
      { service: "Database", status: "Healthy", latency: "12ms" },
      { service: "Redis Cache", status: "Healthy", latency: "2ms" },
    ],
  },
};

export const WithDegradedService: Story = {
  args: {
    items: [
      { service: "API Gateway", status: "Healthy", latency: "45ms" },
      { service: "Database", status: "Degraded", latency: "250ms" },
      { service: "Cache Server", status: "Healthy", latency: "3ms" },
    ],
  },
};

export const WithDownService: Story = {
  args: {
    items: [
      { service: "API Gateway", status: "Healthy", latency: "45ms" },
      { service: "Database", status: "Down", latency: "N/A" },
      { service: "Cache Server", status: "Degraded", latency: "150ms" },
    ],
  },
};

export const MixedStatuses: Story = {
  args: {
    items: [
      { service: "Frontend CDN", status: "Healthy", latency: "15ms" },
      { service: "API Gateway", status: "Operational", latency: "45ms" },
      { service: "Auth Service", status: "Healthy", latency: "32ms" },
      { service: "Database Primary", status: "Degraded", latency: "180ms" },
      { service: "Database Replica", status: "Down", latency: "N/A" },
      { service: "Message Queue", status: "Healthy", latency: "8ms" },
    ],
  },
};

export const SingleService: Story = {
  args: {
    items: [{ service: "Main Server", status: "Healthy", latency: "25ms" }],
  },
};

export const CustomStatus: Story = {
  args: {
    items: [
      { service: "Custom Service", status: "Maintenance", latency: "N/A" },
      { service: "Another Service", status: "Starting", latency: "..." },
    ],
  },
};

export const DashboardExample: Story = {
  render: () => (
    <div className="max-w-md rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card">
      <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
        System Status
      </h3>
      <SystemStatusList
        items={[
          { service: "API Gateway", status: "Healthy", latency: "45ms" },
          { service: "Database", status: "Operational", latency: "12ms" },
          { service: "Cache Server", status: "Healthy", latency: "3ms" },
          { service: "Message Queue", status: "Healthy", latency: "8ms" },
        ]}
      />
    </div>
  ),
};

export const WithI18n: Story = {
  name: "With i18n (Chinese)",
  args: {
    items: [
      { service: "API 閘道", status: "Healthy", latency: "45ms" },
      { service: "資料庫", status: "Operational", latency: "12ms" },
      { service: "快取伺服器", status: "Healthy", latency: "3ms" },
    ],
  },
};
