import * as React from "react";

import { cn } from "../../utils";

type StatusType = "Healthy" | "Operational" | "Degraded" | "Down" | string;

const statusStyles: Record<string, string> = {
  Healthy: "bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400",
  Operational: "bg-success-50 text-success-600 dark:bg-success-900/30 dark:text-success-400",
  Degraded: "bg-warning-50 text-warning-600 dark:bg-warning-900/30 dark:text-warning-400",
  Down: "bg-danger-50 text-danger-600 dark:bg-danger-900/30 dark:text-danger-400",
};

const defaultStatusStyle = "bg-neutral-50 text-neutral-600 dark:bg-neutral-700/30 dark:text-neutral-400";

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
          className="flex items-center justify-between rounded-lg bg-neutral-50 px-3 py-2 dark:bg-neutral-700/50"
        >
          <div>
            <div className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
              {item.service}
            </div>
            <div className="text-[11px] text-neutral-500 dark:text-neutral-400">
              {item.latency}
            </div>
          </div>
          <span className={cn("rounded-full px-2 py-0.5 text-[11px] font-medium", getStatusStyle(item.status))}>
            {item.status}
          </span>
        </div>
      ))}
    </div>
  );
}

export { SystemStatusList };
export type { SystemStatusListProps, StatusItem };
