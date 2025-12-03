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
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-[var(--shadow-card)]",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-[var(--text-secondary)]">
          {label}
        </span>
        {badge && (
          <span className="rounded-full bg-[var(--brand-50)] px-2 py-0.5 text-[10px] text-[var(--brand-700)]">
            {badge}
          </span>
        )}
      </div>
      <div className="mt-2 flex items-baseline gap-2">
        <span className="text-2xl font-semibold text-[var(--text-primary)]">
          {value}
        </span>
        {trend && (
          <span className="text-xs text-[var(--success-600)]">
            {trend}
          </span>
        )}
      </div>
    </div>
  );
}

export { StatCard };
export type { StatCardProps };
