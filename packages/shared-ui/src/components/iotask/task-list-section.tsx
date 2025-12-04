import * as React from "react";

import { cn } from "../../utils";

interface TaskListSectionProps {
  title: string;
  count?: number;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

function TaskListSection({
  title,
  count,
  action,
  children,
  className,
}: TaskListSectionProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card",
        className
      )}
    >
      <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
        <div className="flex items-center gap-2">
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            {title}
          </h2>
          {count !== undefined && (
            <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-[var(--neutral-100)] px-1.5 text-xs font-medium text-[var(--text-secondary)]">
              {count}
            </span>
          )}
        </div>
        {action && <div className="text-xs">{action}</div>}
      </div>
      <div className="space-y-2 p-4">{children}</div>
    </div>
  );
}

export { TaskListSection };
export type { TaskListSectionProps };
