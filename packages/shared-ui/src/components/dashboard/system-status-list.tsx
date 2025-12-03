import * as React from "react";

import { cn } from "../../utils";

type StatusType = "Healthy" | "Operational" | "Degraded" | "Down" | string;

const statusStyles: Record<string, string> = {
  Healthy: "bg-[var(--success-50)] text-[var(--success-600)]",
  Operational: "bg-[var(--success-50)] text-[var(--success-600)]",
  Degraded: "bg-warning-50 text-warning-600",
  Down: "bg-danger-50 text-danger-600",
};

const defaultStatusStyle = "bg-[var(--surface-muted)] text-[var(--text-secondary)]";

function getStatusStyle(status: StatusType): string {
  return statusStyles[status] || defaultStatusStyle;
}

interface StatusItem {
  service: string;
  status: StatusType;
  latency: string;
}

interface SystemStatusListProps {
  items: StatusItem[];
  className?: string;
}

function SystemStatusList({ items, className }: SystemStatusListProps) {
  return (
    <div className={cn("space-y-3", className)}>
      {items.map((item) => (
        <div
          key={item.service}
          className="flex items-center justify-between rounded-lg bg-[var(--surface-muted)] px-3 py-2"
        >
          <div>
            <div className="text-xs font-medium text-[var(--text-primary)]">
              {item.service}
            </div>
            <div className="text-[10px] text-[var(--text-secondary)]">
              {item.latency}
            </div>
          </div>
          <span className={cn("rounded-full px-2 py-0.5 text-[10px] font-medium", getStatusStyle(item.status))}>
            {item.status}
          </span>
        </div>
      ))}
    </div>
  );
}

export { SystemStatusList };
export type { SystemStatusListProps, StatusItem };
