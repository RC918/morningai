import type { Meta, StoryObj } from "@storybook/react";
import { useState } from "react";
import {
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle,
  XCircle,
  Users,
} from "lucide-react";

import { StatusCard } from "./status-card";

const meta: Meta<typeof StatusCard> = {
  title: "Dashboard/StatusCard",
  component: StatusCard,
  parameters: {
    layout: "centered",
    docs: {
      description: {
        component:
          "Interactive status/filter card archetype for dashboard pages. Supports multiple color variants, active states, and accessibility features.",
      },
    },
  },
  tags: ["autodocs"],
  argTypes: {
    variant: {
      control: "select",
      options: ["default", "blue", "green", "yellow", "red"],
      description: "Color variant for the card",
    },
    isActive: {
      control: "boolean",
      description: "Whether the card is currently selected/active",
    },
    disabled: {
      control: "boolean",
      description: "Whether the card is disabled",
    },
    label: {
      control: "text",
      description: "Card label text",
    },
    value: {
      control: "text",
      description: "Numeric value to display",
    },
    tooltip: {
      control: "text",
      description: "Tooltip text for the card",
    },
  },
};

export default meta;
type Story = StoryObj<typeof StatusCard>;

export const Default: Story = {
  args: {
    label: "Total Sessions",
    value: "128",
    icon: <Activity />,
    variant: "default",
    isActive: false,
  },
};

export const Blue: Story = {
  args: {
    label: "Active",
    value: "42",
    icon: <Clock />,
    variant: "blue",
    isActive: false,
  },
};

export const Green: Story = {
  args: {
    label: "Completed",
    value: "86",
    icon: <CheckCircle />,
    variant: "green",
    isActive: false,
  },
};

export const Yellow: Story = {
  args: {
    label: "Pending",
    value: "15",
    icon: <AlertTriangle />,
    variant: "yellow",
    isActive: false,
  },
};

export const Red: Story = {
  args: {
    label: "Failed",
    value: "3",
    icon: <XCircle />,
    variant: "red",
    isActive: false,
  },
};

export const ActiveState: Story = {
  args: {
    label: "Active Sessions",
    value: "42",
    icon: <Clock />,
    variant: "blue",
    isActive: true,
  },
};

export const DisabledState: Story = {
  args: {
    label: "Disabled Card",
    value: "0",
    icon: <Activity />,
    variant: "default",
    disabled: true,
  },
};

export const WithTooltip: Story = {
  args: {
    label: "Total Users",
    value: "1,234",
    icon: <Users />,
    variant: "blue",
    tooltip: "Total number of registered users",
  },
};

export const AllVariants: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
      <StatusCard
        label="Default"
        value="100"
        icon={<Activity />}
        variant="default"
      />
      <StatusCard
        label="Blue"
        value="42"
        icon={<Clock />}
        variant="blue"
      />
      <StatusCard
        label="Green"
        value="86"
        icon={<CheckCircle />}
        variant="green"
      />
      <StatusCard
        label="Yellow"
        value="15"
        icon={<AlertTriangle />}
        variant="yellow"
      />
      <StatusCard
        label="Red"
        value="3"
        icon={<XCircle />}
        variant="red"
      />
    </div>
  ),
};

export const AllVariantsActive: Story = {
  render: () => (
    <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
      <StatusCard
        label="Default"
        value="100"
        icon={<Activity />}
        variant="default"
        isActive
      />
      <StatusCard
        label="Blue"
        value="42"
        icon={<Clock />}
        variant="blue"
        isActive
      />
      <StatusCard
        label="Green"
        value="86"
        icon={<CheckCircle />}
        variant="green"
        isActive
      />
      <StatusCard
        label="Yellow"
        value="15"
        icon={<AlertTriangle />}
        variant="yellow"
        isActive
      />
      <StatusCard
        label="Red"
        value="3"
        icon={<XCircle />}
        variant="red"
        isActive
      />
    </div>
  ),
};

export const InteractiveExample: Story = {
  render: function InteractiveStatusCards() {
    const [activeFilter, setActiveFilter] = useState<string | null>("all");

    const filters = [
      { id: "all", label: "All Sessions", value: 128, icon: <Activity />, variant: "default" as const },
      { id: "active", label: "Active", value: 42, icon: <Clock />, variant: "blue" as const },
      { id: "completed", label: "Completed", value: 86, icon: <CheckCircle />, variant: "green" as const },
      { id: "pending", label: "Pending", value: 15, icon: <AlertTriangle />, variant: "yellow" as const },
      { id: "failed", label: "Failed", value: 3, icon: <XCircle />, variant: "red" as const },
    ];

    return (
      <div className="space-y-4">
        <div className="grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-5">
          {filters.map((filter) => (
            <StatusCard
              key={filter.id}
              label={filter.label}
              value={filter.value}
              icon={filter.icon}
              variant={filter.variant}
              isActive={activeFilter === filter.id}
              onClick={() => setActiveFilter(filter.id)}
            />
          ))}
        </div>
        <p className="text-sm text-[var(--text-secondary)]">
          Selected filter: <strong>{activeFilter || "None"}</strong>
        </p>
      </div>
    );
  },
};

export const KeyboardNavigation: Story = {
  render: () => (
    <div className="space-y-4">
      <p className="text-sm text-[var(--text-secondary)]">
        Use Tab to navigate between cards. Focus ring should be visible on keyboard focus.
      </p>
      <div className="grid grid-cols-3 gap-4">
        <StatusCard
          label="First Card"
          value="1"
          icon={<Activity />}
          variant="blue"
        />
        <StatusCard
          label="Second Card"
          value="2"
          icon={<CheckCircle />}
          variant="green"
        />
        <StatusCard
          label="Third Card"
          value="3"
          icon={<AlertTriangle />}
          variant="yellow"
        />
      </div>
    </div>
  ),
};
