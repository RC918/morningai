import * as React from "react";

import { cn } from "../../utils";

interface ActivityListPanelProps {
  title: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  emptyMessage?: string;
  className?: string;
}

function ActivityListPanel({
  title,
  action,
  children,
  emptyMessage = "No recent activity",
  className,
}: ActivityListPanelProps) {
  const hasChildren = React.Children.count(children) > 0;

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card",
        className
      )}
    >
      <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
        <h2 className="text-sm font-semibold text-[var(--text-primary)]">
          {title}
        </h2>
        {action && <div className="text-xs">{action}</div>}
      </div>
      <div className="divide-y divide-[var(--border)] px-5">
        {hasChildren ? (
          children
        ) : (
          <div className="py-8 text-center text-sm text-[var(--text-secondary)]">
            {emptyMessage}
          </div>
        )}
      </div>
    </div>
  );
}

export { ActivityListPanel };
export type { ActivityListPanelProps };
