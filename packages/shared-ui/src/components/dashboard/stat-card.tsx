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
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card",
        className
      )}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-xs text-[var(--text-secondary)] font-medium">
          {label}
        </span>
        {badge && (
          <span className="px-2 py-0.5 text-[10px] rounded-full bg-[var(--brand-50)] text-[var(--brand-700)]">
            {badge}
          </span>
        )}
      </div>
      <div className="text-2xl font-semibold text-[var(--text-primary)]">
        {value}
      </div>
      {trend && (
        <div className="mt-1 text-xs text-[var(--success-600)]">
          {trend}
        </div>
      )}
    </div>
  );
}

export { StatCard };
export type { StatCardProps };
