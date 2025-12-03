import * as React from "react";

import { cn } from "../../utils";

interface SectionCardProps {
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

function SectionCard({
  title,
  subtitle,
  action,
  children,
  className,
}: SectionCardProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card",
        className
      )}
    >
      <div className="flex items-center justify-between border-b border-[var(--border)] px-5 py-4">
        <div>
          <h2 className="text-sm font-semibold text-[var(--text-primary)]">
            {title}
          </h2>
          {subtitle && (
            <p className="mt-0.5 text-xs text-[var(--text-secondary)]">
              {subtitle}
            </p>
          )}
        </div>
        {action && <div className="text-xs">{action}</div>}
      </div>
      <div className="px-5 py-4">{children}</div>
    </div>
  );
}

export { SectionCard };
export type { SectionCardProps };
