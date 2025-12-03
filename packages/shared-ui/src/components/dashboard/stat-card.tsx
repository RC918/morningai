import * as React from "react";

import { cn } from "../../utils";

interface StatCardProps {
  label: string;
  value: string;
  trend?: string;
  badge?: string;
  className?: string;
}

function StatCard({ label, value, trend, badge, className }: StatCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-neutral-200 bg-white p-4 shadow-sm dark:border-neutral-700 dark:bg-neutral-800",
        className
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs font-medium text-neutral-500 dark:text-neutral-400">
          {label}
        </span>
        {badge && (
          <span className="rounded-full bg-primary-50 px-2 py-0.5 text-[10px] text-primary-700 dark:bg-primary-900/30 dark:text-primary-300">
            {badge}
          </span>
        )}
      </div>
      <div className="text-2xl font-semibold text-neutral-900 dark:text-neutral-100">
        {value}
      </div>
      {trend && (
        <div className="mt-1 text-xs text-success-600 dark:text-success-400">
          {trend}
        </div>
      )}
    </div>
  );
}

export { StatCard };
export type { StatCardProps };
