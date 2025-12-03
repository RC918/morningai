import * as React from "react";

import { cn } from "../../utils";

interface ProgressItem {
  label: string;
  value: number;
  hint?: string;
}

interface ProgressTrackProps {
  items: ProgressItem[];
  className?: string;
}

function ProgressTrack({ items, className }: ProgressTrackProps) {
  return (
    <div className={cn("space-y-5", className)}>
      {items.map((item) => (
        <div key={item.label} className="space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-[var(--text-primary)]">
                {item.label}
              </span>
              {item.hint && (
                <span className="text-[11px] text-[var(--text-secondary)]">
                  {item.hint}
                </span>
              )}
            </div>
            <span className="text-xs text-[var(--text-secondary)]">
              {item.value}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-[var(--surface-muted)]">
            <div
              className="h-full rounded-full bg-[var(--brand-500)] transition-all"
              style={{ width: `${item.value}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}

export { ProgressTrack };
export type { ProgressTrackProps, ProgressItem };
