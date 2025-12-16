import type { Meta, StoryObj } from "@storybook/react";

import { ProgressTrack } from "./progress-track";

const meta = {
  title: "Dashboard/ProgressTrack",
  component: ProgressTrack,
  parameters: {
    layout: "padded",
  },
  tags: ["autodocs"],
  args: {
    items: [],
  },
} satisfies Meta<typeof ProgressTrack>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    items: [
      { label: "Task Completion", value: 75 },
      { label: "Code Coverage", value: 85 },
      { label: "Test Pass Rate", value: 92 },
    ],
  },
};

export const SingleItem: Story = {
  args: {
    items: [{ label: "Progress", value: 60 }],
  },
};

export const FullProgress: Story = {
  args: {
    items: [
      { label: "Completed Tasks", value: 100 },
      { label: "Reviewed Items", value: 100 },
    ],
  },
};

export const LowProgress: Story = {
  args: {
    items: [
      { label: "Sprint Progress", value: 15 },
      { label: "Bug Fixes", value: 25 },
      { label: "Feature Development", value: 10 },
    ],
  },
};

export const MixedProgress: Story = {
  args: {
    items: [
      { label: "Frontend", value: 90 },
      { label: "Backend", value: 65 },
      { label: "Testing", value: 45 },
      { label: "Documentation", value: 20 },
    ],
  },
};

export const WithHints: Story = {
  args: {
    items: [
      { label: "CPU Usage", value: 67, hint: "4 cores active" },
      { label: "Memory Usage", value: 45, hint: "8GB / 16GB" },
      { label: "Disk Usage", value: 82, hint: "164GB / 200GB" },
    ],
  },
};

export const DashboardExample: Story = {
  render: () => (
    <div className="max-w-md rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card">
      <h3 className="mb-4 text-sm font-semibold text-[var(--text-primary)]">
        Project Progress
      </h3>
      <ProgressTrack
        items={[
          { label: "Design", value: 100 },
          { label: "Development", value: 75 },
          { label: "Testing", value: 40 },
          { label: "Deployment", value: 0 },
        ]}
      />
    </div>
  ),
};

export const WithI18n: Story = {
  name: "With i18n (Chinese)",
  args: {
    items: [
      { label: "任務完成度", value: 75 },
      { label: "程式碼覆蓋率", value: 85 },
      { label: "測試通過率", value: 92 },
    ],
  },
};
