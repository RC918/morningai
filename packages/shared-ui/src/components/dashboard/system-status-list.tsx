import * as React from "react";

import { cn } from "../../utils";

interface StatusItem {
  service: string;
  status: string;
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
          <span className="rounded-full bg-success-50 px-2 py-0.5 text-[11px] font-medium text-success-600 dark:bg-success-900/30 dark:text-success-400">
            {item.status}
          </span>
        </div>
      ))}
    </div>
  );
}

export { SystemStatusList };
export type { SystemStatusListProps, StatusItem };
