import * as React from "react";

import { cn } from "../../utils";

type ActivityType = "task" | "comment" | "update" | "milestone" | "alert";

interface ActivityListItemProps {
  id: string;
  type: ActivityType;
  title: string;
  description?: string;
  timestamp: string;
  icon?: React.ReactNode;
  user?: {
    name: string;
    avatar?: string;
  };
  className?: string;
}

const typeStyles: Record<ActivityType, string> = {
  task: "bg-[var(--primary-50)] text-[var(--primary-600)]",
  comment: "bg-[var(--neutral-100)] text-[var(--neutral-600)]",
  update: "bg-[var(--success-50)] text-[var(--success-600)]",
  milestone: "bg-[var(--color-accent-50)] text-[var(--color-accent-600)]",
  alert: "bg-[var(--warning-50)] text-[var(--warning-600)]",
};

const defaultIcons: Record<ActivityType, React.ReactNode> = {
  task: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
    </svg>
  ),
  comment: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
    </svg>
  ),
  update: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
    </svg>
  ),
  milestone: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M3 21v-4m0 0V5a2 2 0 012-2h6.5l1 1H21l-3 6 3 6h-8.5l-1-1H5a2 2 0 00-2 2zm9-13.5V9" />
    </svg>
  ),
  alert: (
    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  ),
};

function ActivityListItem({
  type,
  title,
  description,
  timestamp,
  icon,
  user,
  className,
}: ActivityListItemProps) {
  return (
    <div className={cn("flex gap-3 py-3", className)}>
      <div
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-full",
          typeStyles[type]
        )}
      >
        {icon || defaultIcons[type]}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-medium text-[var(--text-primary)] truncate">
              {title}
            </p>
            {description && (
              <p className="mt-0.5 text-xs text-[var(--text-secondary)] line-clamp-2">
                {description}
              </p>
            )}
          </div>
          <span className="shrink-0 text-xs text-[var(--text-secondary)]">
            {timestamp}
          </span>
        </div>
        {user && (
          <div className="mt-2 flex items-center gap-1.5">
            {user.avatar ? (
              <img
                src={user.avatar}
                alt={user.name}
                className="h-4 w-4 rounded-full object-cover"
              />
            ) : (
              <div className="flex h-4 w-4 items-center justify-center rounded-full bg-[var(--primary-100)] text-[8px] font-medium text-[var(--primary-700)]">
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .join("")
                  .toUpperCase()
                  .slice(0, 2)}
              </div>
            )}
            <span className="text-xs text-[var(--text-secondary)]">
              {user.name}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

export { ActivityListItem };
export type { ActivityListItemProps, ActivityType };
