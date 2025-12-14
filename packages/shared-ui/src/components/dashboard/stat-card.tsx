import * as React from "react";

import { cn } from "../../utils";

type StatCardVariant = "default" | "blue" | "green" | "yellow" | "red" | "purple";

const variantIconColors: Record<StatCardVariant, string> = {
  default: "text-[var(--neutral-600)]",
  blue: "text-[var(--primary-600)]",
  green: "text-[var(--success-600)]",
  yellow: "text-[var(--warning-600)]",
  red: "text-[var(--error-600)]",
  purple: "text-[var(--color-accent-600)]",
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
  /** Whether the delta represents a positive/good change (green), negative/bad change (red), or neutral info (secondary text). Defaults to true. */
  deltaPositive?: boolean | "neutral";
  /** Color variant for the icon */
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
                deltaPositive === "neutral"
                  ? "text-[var(--text-secondary)]"
                  : deltaPositive
                    ? "text-[var(--success-600)]"
                    : "text-[var(--error-600)]"
              )}
            >
              {displayDelta}
            </div>
          )}
        </div>
        {icon && (
          <div className="ml-3 shrink-0">
            {React.isValidElement(icon)
              ? React.cloneElement(icon as React.ReactElement<{ className?: string }>, {
                  className: cn("size-5", variantIconColors[variant]),
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
