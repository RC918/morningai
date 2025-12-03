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
    <div className={cn("space-y-4", className)}>
      {items.map((item) => (
        <div key={item.label} className="space-y-1">
          <div className="flex items-center justify-between">
            <div className="flex flex-col">
              <span className="text-xs font-medium text-neutral-900 dark:text-neutral-100">
                {item.label}
              </span>
              {item.hint && (
                <span className="text-[11px] text-neutral-500 dark:text-neutral-400">
                  {item.hint}
                </span>
              )}
            </div>
            <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
              {item.value}%
            </span>
          </div>
          <div className="h-1.5 w-full overflow-hidden rounded-full bg-neutral-100 dark:bg-neutral-700">
            <div
              className="h-full rounded-full bg-primary-500 transition-all"
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
