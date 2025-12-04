import * as React from "react";

import { cn, getInitials } from "../../utils";

type TaskStatus = "pending" | "in_progress" | "completed";
type TaskPriority = "low" | "medium" | "high";

interface TaskRowProps {
  id: string;
  title: string;
  status: TaskStatus;
  priority?: TaskPriority;
  progress?: number;
  dueDate?: string;
  assignee?: string;
  onStatusChange?: (id: string, status: TaskStatus) => void;
  className?: string;
}

const statusStyles: Record<TaskStatus, string> = {
  pending: "border-[var(--neutral-300)] bg-[var(--surface)]",
  in_progress: "border-[var(--primary-500)] bg-[var(--primary-50)]",
  completed: "border-[var(--success-500)] bg-[var(--success-50)]",
};

const priorityStyles: Record<TaskPriority, string> = {
  low: "bg-[var(--neutral-100)] text-[var(--neutral-600)]",
  medium: "bg-[var(--warning-50)] text-[var(--warning-700)]",
  high: "bg-[var(--error-50)] text-[var(--error-700)]",
};

function TaskRow({
  id,
  title,
  status,
  priority,
  progress,
  dueDate,
  assignee,
  onStatusChange,
  className,
}: TaskRowProps) {
  const handleCheckboxChange = () => {
    if (onStatusChange) {
      const newStatus = status === "completed" ? "pending" : "completed";
      onStatusChange(id, newStatus);
    }
  };

  return (
    <div
      className={cn(
        "flex items-center gap-3 rounded-lg border p-3 transition-colors hover:bg-[var(--neutral-50)]",
        statusStyles[status],
        className
      )}
    >
      <button
        type="button"
        role="checkbox"
        aria-checked={status === "completed"}
        aria-label={status === "completed" ? `Mark "${title}" as incomplete` : `Mark "${title}" as complete`}
        onClick={handleCheckboxChange}
        className={cn(
          "flex h-5 w-5 shrink-0 items-center justify-center rounded border-2 transition-colors",
          status === "completed"
            ? "border-[var(--success-500)] bg-[var(--success-500)] text-white"
            : "border-[var(--neutral-300)] bg-[var(--surface)]"
        )}
      >
        {status === "completed" && (
          <svg
            className="h-3 w-3"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={3}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M5 13l4 4L19 7"
            />
          </svg>
        )}
      </button>

      <div className="flex-1 min-w-0">
        <div
          className={cn(
            "text-sm font-medium truncate",
            status === "completed"
              ? "text-[var(--text-secondary)] line-through"
              : "text-[var(--text-primary)]"
          )}
        >
          {title}
        </div>
        {progress !== undefined && status !== "completed" && (
          <div className="mt-1.5 h-1.5 w-full rounded-full bg-[var(--neutral-200)]">
            <div
              className="h-full rounded-full bg-[var(--primary-500)] transition-all"
              style={{ width: `${Math.min(100, Math.max(0, progress))}%` }}
            />
          </div>
        )}
      </div>

      <div className="flex items-center gap-2 shrink-0">
        {priority && (
          <span
            className={cn(
              "px-2 py-0.5 text-[10px] font-medium rounded-full uppercase",
              priorityStyles[priority]
            )}
          >
            {priority}
          </span>
        )}
        {dueDate && (
          <span className="text-xs text-[var(--text-secondary)]">{dueDate}</span>
        )}
        {assignee && (
          <div
            className="flex h-6 w-6 items-center justify-center rounded-full bg-[var(--primary-100)] text-[10px] font-medium text-[var(--primary-700)]"
            title={assignee}
          >
            {getInitials(assignee)}
          </div>
        )}
      </div>
    </div>
  );
}

export { TaskRow };
export type { TaskRowProps, TaskStatus, TaskPriority };
