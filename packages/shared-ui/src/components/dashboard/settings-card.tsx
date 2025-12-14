import * as React from "react";

import { cn } from "../../utils";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card";

type SettingsCardVariant = "default" | "blue" | "green" | "yellow" | "red" | "purple";

const variantIconColors: Record<SettingsCardVariant, string> = {
  default: "text-[var(--neutral-600)]",
  blue: "text-[var(--primary-600)]",
  green: "text-[var(--success-600)]",
  yellow: "text-[var(--warning-600)]",
  red: "text-[var(--error-600)]",
  purple: "text-[var(--color-accent-600)]",
};

interface SettingsCardProps {
  /** Card title */
  title: string;
  /** Card description */
  description?: string;
  /** Icon element to display next to the title */
  icon?: React.ReactNode;
  /** Color variant for the icon */
  variant?: SettingsCardVariant;
  /** Card content */
  children?: React.ReactNode;
  /** Additional CSS classes */
  className?: string;
  /** Whether the card content has no padding (for custom layouts) */
  noPadding?: boolean;
}

function SettingsCard({
  title,
  description,
  icon,
  variant = "default",
  children,
  className,
  noPadding = false,
}: SettingsCardProps) {
  return (
    <Card
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] shadow-card",
        className
      )}
    >
      <CardHeader className="px-5 py-4">
        <CardTitle className="flex items-center gap-2 text-base font-semibold text-[var(--text-primary)]">
          {icon && (
            <span className="shrink-0">
              {React.isValidElement(icon)
                ? React.cloneElement(icon as React.ReactElement<{ className?: string }>, {
                    className: cn("size-5", variantIconColors[variant]),
                  })
                : icon}
            </span>
          )}
          {title}
        </CardTitle>
        {description && (
          <CardDescription className="text-sm text-[var(--text-secondary)]">
            {description}
          </CardDescription>
        )}
      </CardHeader>
      {children && (
        <CardContent className={cn(noPadding ? "p-0" : "space-y-4 p-5 pt-0")}>
          {children}
        </CardContent>
      )}
    </Card>
  );
}

export { SettingsCard };
export type { SettingsCardProps, SettingsCardVariant };
