import * as React from "react";

import { cn } from "../../utils";

type StatCardVariant = "default" | "blue" | "green" | "yellow" | "red" | "purple";

const variantStyles: Record<StatCardVariant, string> = {
  default: "bg-[var(--neutral-100)] text-[var(--neutral-600)]",
  blue: "bg-[var(--primary-50)] text-[var(--primary-600)]",
  green: "bg-[var(--success-50)] text-[var(--success-600)]",
  yellow: "bg-[var(--warning-50)] text-[var(--warning-600)]",
  red: "bg-[var(--error-50)] text-[var(--error-600)]",
  purple: "bg-[var(--color-accent-50)] text-[var(--color-accent-600)]",
};

interface StatCardProps {
  label: string;
  value: string;
  /** @deprecated Use deltaLabel instead for semantic clarity */
  trend?: string;
  badge?: string;
  className?: string;
  /** Icon element to display on the right side */
  icon?: React.ReactNode;
  /** Delta/change label (e.g., "+5.10%", "-2 this month") */
  deltaLabel?: string;
  /** Whether the delta represents a positive/good change (green) or a negative/bad change (red). Defaults to true. */
  deltaPositive?: boolean;
  /** Color variant for the icon background */
  variant?: StatCardVariant;
}

function StatCard({
  label,
  value,
  trend,
  badge,
  className,
  icon,
  deltaLabel,
  deltaPositive = true,
  variant = "default",
}: StatCardProps) {
  const displayDelta = deltaLabel || trend;

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] p-4 shadow-card",
        className
      )}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
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
          {displayDelta && (
            <div
              className={cn(
                "mt-1 text-xs",
                deltaPositive
                  ? "text-[var(--success-600)]"
                  : "text-[var(--error-600)]"
              )}
            >
              {displayDelta}
            </div>
          )}
        </div>
        {icon && (
          <div
            className={cn(
              "flex items-center justify-center ml-3 shrink-0",
              "h-[var(--card-icon-kpi-containerSize,40px)] w-[var(--card-icon-kpi-containerSize,40px)]",
              "rounded-[var(--card-icon-kpi-shape,9999px)]",
              variantStyles[variant]
            )}
          >
            {React.isValidElement(icon)
              ? React.cloneElement(icon as React.ReactElement<{ className?: string }>, {
                  className: "w-[var(--card-icon-kpi-size,40px)] h-[var(--card-icon-kpi-size,40px)]",
                })
              : icon}
          </div>
        )}
      </div>
    </div>
  );
}

export { StatCard };
export type { StatCardProps };
