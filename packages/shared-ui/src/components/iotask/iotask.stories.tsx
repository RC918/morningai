import type { Meta, StoryObj } from "@storybook/react";
import * as React from "react";

import { AvatarStack } from "./avatar-stack";
import { TaskRow } from "./task-row";
import { TaskListSection } from "./task-list-section";
import { ActivityListItem } from "./activity-list-item";
import { ActivityListPanel } from "./activity-list-panel";
import { CircleProgressCard } from "./circle-progress-card";
import { CalendarCard } from "./calendar-card";

const meta: Meta = {
  title: "iotask/Components",
  parameters: {
    layout: "padded",
  },
};

export default meta;

export const AvatarStackDefault: StoryObj<typeof AvatarStack> = {
  render: () => (
    <div className="space-y-4">
      <div>
        <p className="text-sm text-[var(--text-secondary)] mb-2">Small (3 avatars)</p>
        <AvatarStack
          size="sm"
          avatars={[
            { id: "1", name: "John Doe" },
            { id: "2", name: "Jane Smith" },
            { id: "3", name: "Bob Wilson" },
          ]}
        />
      </div>
      <div>
        <p className="text-sm text-[var(--text-secondary)] mb-2">Medium (5 avatars, max 4)</p>
        <AvatarStack
          size="md"
          max={4}
          avatars={[
            { id: "1", name: "John Doe" },
            { id: "2", name: "Jane Smith" },
            { id: "3", name: "Bob Wilson" },
            { id: "4", name: "Alice Brown" },
            { id: "5", name: "Charlie Davis" },
          ]}
        />
      </div>
      <div>
        <p className="text-sm text-[var(--text-secondary)] mb-2">Large (8 avatars, max 3)</p>
        <AvatarStack
          size="lg"
          max={3}
          avatars={[
            { id: "1", name: "John Doe" },
            { id: "2", name: "Jane Smith" },
            { id: "3", name: "Bob Wilson" },
            { id: "4", name: "Alice Brown" },
            { id: "5", name: "Charlie Davis" },
            { id: "6", name: "Eve Johnson" },
            { id: "7", name: "Frank Miller" },
            { id: "8", name: "Grace Lee" },
          ]}
        />
      </div>
    </div>
  ),
};

export const TaskRowStates: StoryObj<typeof TaskRow> = {
  render: () => (
    <div className="space-y-3 max-w-lg">
      <TaskRow
        id="1"
        title="Design new landing page"
        status="pending"
        priority="high"
        dueDate="Dec 15"
        assignee="John Doe"
      />
      <TaskRow
        id="2"
        title="Implement user authentication"
        status="in_progress"
        priority="medium"
        progress={65}
        assignee="Jane Smith"
      />
      <TaskRow
        id="3"
        title="Write unit tests for API"
        status="completed"
        priority="low"
        assignee="Bob Wilson"
      />
    </div>
  ),
};

export const TaskListSectionExample: StoryObj<typeof TaskListSection> = {
  render: () => (
    <TaskListSection
      title="Today's Tasks"
      count={3}
      action={
        <a href="#" className="text-[var(--primary-600)] hover:underline">
          View all
        </a>
      }
    >
      <TaskRow
        id="1"
        title="Review pull requests"
        status="pending"
        priority="high"
        dueDate="Today"
      />
      <TaskRow
        id="2"
        title="Update documentation"
        status="in_progress"
        progress={40}
      />
      <TaskRow
        id="3"
        title="Fix navigation bug"
        status="completed"
      />
    </TaskListSection>
  ),
};

export const ActivityListItemTypes: StoryObj<typeof ActivityListItem> = {
  render: () => (
    <div className="max-w-md divide-y divide-[var(--border)]">
      <ActivityListItem
        id="1"
        type="task"
        title="New task assigned"
        description="Design system audit has been assigned to you"
        timestamp="2m ago"
        user={{ name: "John Doe" }}
      />
      <ActivityListItem
        id="2"
        type="comment"
        title="New comment on PR #123"
        description="Looks good! Just a few minor suggestions..."
        timestamp="15m ago"
        user={{ name: "Jane Smith" }}
      />
      <ActivityListItem
        id="3"
        type="update"
        title="Project status updated"
        description="Sprint 5 is now 80% complete"
        timestamp="1h ago"
      />
      <ActivityListItem
        id="4"
        type="milestone"
        title="Milestone reached"
        description="Q4 goals have been achieved"
        timestamp="2h ago"
      />
      <ActivityListItem
        id="5"
        type="alert"
        title="Build failed"
        description="CI pipeline failed on main branch"
        timestamp="3h ago"
      />
    </div>
  ),
};

export const ActivityListPanelExample: StoryObj<typeof ActivityListPanel> = {
  render: () => (
    <ActivityListPanel
      title="Recent Activity"
      action={
        <a href="#" className="text-[var(--primary-600)] hover:underline">
          See all
        </a>
      }
    >
      <ActivityListItem
        id="1"
        type="task"
        title="New task assigned"
        description="Design system audit"
        timestamp="2m ago"
        user={{ name: "John Doe" }}
      />
      <ActivityListItem
        id="2"
        type="comment"
        title="New comment"
        description="Great work on the PR!"
        timestamp="15m ago"
        user={{ name: "Jane Smith" }}
      />
      <ActivityListItem
        id="3"
        type="update"
        title="Status updated"
        timestamp="1h ago"
      />
    </ActivityListPanel>
  ),
};

export const ActivityListPanelEmpty: StoryObj<typeof ActivityListPanel> = {
  render: () => (
    <ActivityListPanel
      title="Recent Activity"
      emptyMessage="No activity yet"
    >
      {null}
    </ActivityListPanel>
  ),
};

export const CircleProgressCardSizes: StoryObj<typeof CircleProgressCard> = {
  render: () => (
    <div className="flex gap-4 flex-wrap">
      <CircleProgressCard
        title="Small"
        value={75}
        size="sm"
        color="primary"
        subtitle="Tasks completed"
      />
      <CircleProgressCard
        title="Medium"
        value={60}
        size="md"
        color="success"
        subtitle="Sprint progress"
      />
      <CircleProgressCard
        title="Large"
        value={45}
        size="lg"
        color="accent"
        subtitle="Overall completion"
      />
    </div>
  ),
};

export const CircleProgressCardColors: StoryObj<typeof CircleProgressCard> = {
  render: () => (
    <div className="flex gap-4 flex-wrap">
      <CircleProgressCard title="Primary" value={80} color="primary" />
      <CircleProgressCard title="Success" value={65} color="success" />
      <CircleProgressCard title="Warning" value={50} color="warning" />
      <CircleProgressCard title="Error" value={35} color="error" />
      <CircleProgressCard title="Accent" value={90} color="accent" />
    </div>
  ),
};

export const CalendarCardDefault: StoryObj<typeof CalendarCard> = {
  render: () => (
    <div className="max-w-sm">
      <CalendarCard
        title="Calendar"
        date={new Date()}
        events={[
          { id: "1", title: "Team standup", time: "9:00 AM", color: "primary" },
          { id: "2", title: "Design review", time: "2:00 PM", color: "accent" },
          { id: "3", title: "Sprint planning", time: "4:00 PM", color: "success" },
        ]}
      />
    </div>
  ),
};

export const CalendarCardNoEvents: StoryObj<typeof CalendarCard> = {
  render: () => (
    <div className="max-w-sm">
      <CalendarCard
        title="Schedule"
        date={new Date()}
      />
    </div>
  ),
};

export const FullDashboardExample: StoryObj = {
  render: () => (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <div className="lg:col-span-2 space-y-6">
        <TaskListSection
          title="My Tasks"
          count={4}
          action={
            <a href="#" className="text-[var(--primary-600)] hover:underline">
              View all
            </a>
          }
        >
          <TaskRow
            id="1"
            title="Complete quarterly report"
            status="in_progress"
            priority="high"
            progress={75}
            dueDate="Dec 10"
            assignee="You"
          />
          <TaskRow
            id="2"
            title="Review team performance"
            status="pending"
            priority="medium"
            dueDate="Dec 12"
          />
          <TaskRow
            id="3"
            title="Update project roadmap"
            status="pending"
            priority="low"
            dueDate="Dec 15"
          />
          <TaskRow
            id="4"
            title="Send weekly newsletter"
            status="completed"
          />
        </TaskListSection>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <CircleProgressCard
            title="Sprint Progress"
            value={68}
            color="primary"
            subtitle="12 of 18 tasks done"
          />
          <CircleProgressCard
            title="Team Velocity"
            value={85}
            color="success"
            subtitle="Above target"
          />
          <CircleProgressCard
            title="Bug Resolution"
            value={42}
            color="warning"
            subtitle="5 bugs remaining"
          />
        </div>
      </div>

      <div className="space-y-6">
        <CalendarCard
          title="Upcoming"
          date={new Date()}
          events={[
            { id: "1", title: "Team standup", time: "9:00 AM", color: "primary" },
            { id: "2", title: "1:1 with manager", time: "11:00 AM", color: "accent" },
          ]}
        />

        <ActivityListPanel
          title="Recent Activity"
          action={
            <a href="#" className="text-[var(--primary-600)] hover:underline">
              See all
            </a>
          }
        >
          <ActivityListItem
            id="1"
            type="task"
            title="Task completed"
            description="Weekly newsletter sent"
            timestamp="5m ago"
          />
          <ActivityListItem
            id="2"
            type="comment"
            title="New feedback"
            description="Great progress on the report!"
            timestamp="1h ago"
            user={{ name: "Sarah Chen" }}
          />
          <ActivityListItem
            id="3"
            type="milestone"
            title="Milestone reached"
            description="Phase 1 complete"
            timestamp="2h ago"
          />
        </ActivityListPanel>

        <div>
          <p className="text-sm font-medium text-[var(--text-primary)] mb-2">Team Members</p>
          <AvatarStack
            size="md"
            max={5}
            avatars={[
              { id: "1", name: "John Doe" },
              { id: "2", name: "Jane Smith" },
              { id: "3", name: "Bob Wilson" },
              { id: "4", name: "Alice Brown" },
              { id: "5", name: "Charlie Davis" },
              { id: "6", name: "Eve Johnson" },
            ]}
          />
        </div>
      </div>
    </div>
  ),
};
