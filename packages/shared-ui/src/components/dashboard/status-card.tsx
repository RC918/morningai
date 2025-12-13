import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../../utils";

/**
 * StatusCard - Interactive status/filter card archetype for dashboard pages
 *
 * Design Specification:
 * - Fixed dimensions: min-w-[140px] h-24 (96px) for consistent visual alignment
 * - Internal padding: px-4 py-3 (16px horizontal, 12px vertical)
 * - Icon container: 28x28px (h-7 w-7) with rounded-lg, positioned top-right
 * - Typography: label text-xs font-medium (top-left), value text-2xl font-semibold (bottom-left)
 * - Active state: light tinted background + subtle shadow + 2px left highlight (internal)
 * - Focus state: 2px ring with accessibility color, only on keyboard focus
 */

const statusCardVariants = cva(
  // Base styles
  [
    "relative min-w-[140px] h-24 w-full",
    "text-left rounded-xl border px-4 py-3",
    "flex flex-col justify-between",
    "transition-all duration-150",
    "border-[var(--border)] bg-[var(--surface)] shadow-sm",
    "focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--a11y-focus-outline-color,var(--accessibility-focus-outline-color,#0284c7))] focus-visible:ring-offset-2",
  ],
  {
    variants: {
      variant: {
        default: "",
        blue: "",
        green: "",
        yellow: "",
        red: "",
      },
      isActive: {
        true: "shadow-md",
        false: "hover:shadow-md hover:border-[var(--neutral-300)]",
      },
      disabled: {
        true: "opacity-50 cursor-not-allowed",
        false: "cursor-pointer",
      },
    },
    compoundVariants: [
      // Active state backgrounds and borders
      {
        variant: "default",
        isActive: true,
        className: "bg-neutral-50 border-neutral-300",
      },
      {
        variant: "blue",
        isActive: true,
        className: "bg-primary-50 border-primary-500",
      },
      {
        variant: "green",
        isActive: true,
        className: "bg-success-50 border-success-500",
      },
      {
        variant: "yellow",
        isActive: true,
        className: "bg-warning-50 border-warning-500",
      },
      {
        variant: "red",
        isActive: true,
        className: "bg-error-50 border-error-500",
      },
    ],
    defaultVariants: {
      variant: "default",
      isActive: false,
      disabled: false,
    },
  }
);

const iconContainerVariants = cva(
  "flex h-7 w-7 items-center justify-center rounded-lg shrink-0",
  {
    variants: {
      variant: {
        default: "bg-[var(--neutral-100)] text-[var(--neutral-600)]",
        blue: "bg-[var(--primary-50)] text-[var(--primary-600)]",
        green: "bg-[var(--success-50)] text-[var(--success-600)]",
        yellow: "bg-[var(--warning-50)] text-[var(--warning-600)]",
        red: "bg-[var(--error-50)] text-[var(--error-600)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

const valueVariants = cva(
  "text-2xl font-semibold transition-colors duration-150",
  {
    variants: {
      variant: {
        default: "",
        blue: "",
        green: "",
        yellow: "",
        red: "",
      },
      isActive: {
        true: "",
        false: "text-[var(--text-primary)]",
      },
    },
    compoundVariants: [
      {
        variant: "default",
        isActive: true,
        className: "text-[var(--neutral-700)]",
      },
      {
        variant: "blue",
        isActive: true,
        className: "text-[var(--primary-600)]",
      },
      {
        variant: "green",
        isActive: true,
        className: "text-[var(--success-600)]",
      },
      {
        variant: "yellow",
        isActive: true,
        className: "text-[var(--warning-600)]",
      },
      {
        variant: "red",
        isActive: true,
        className: "text-[var(--error-600)]",
      },
      {
        isActive: false,
        className: "text-[var(--text-primary)]",
      },
    ],
    defaultVariants: {
      variant: "default",
      isActive: false,
    },
  }
);

const highlightBarVariants = cva(
  "pointer-events-none absolute inset-y-3 left-1.5 w-0.5 rounded-full",
  {
    variants: {
      variant: {
        default: "bg-[var(--neutral-400)]",
        blue: "bg-[var(--primary-600)]",
        green: "bg-[var(--success-600)]",
        yellow: "bg-[var(--warning-600)]",
        red: "bg-[var(--error-600)]",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
);

type StatusCardVariant = "default" | "blue" | "green" | "yellow" | "red";

interface StatusCardProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, "disabled">,
    VariantProps<typeof statusCardVariants> {
  /** Card label text */
  label: string;
  /** Numeric value to display */
  value: string | number;
  /** Icon element to display */
  icon: React.ReactNode;
  /** Color variant for the card */
  variant?: StatusCardVariant;
  /** Whether this card is currently selected/active */
  isActive?: boolean;
  /** Whether the card is disabled */
  disabled?: boolean;
  /** Tooltip text for the card */
  tooltip?: string;
}

function StatusCard({
  label,
  value,
  icon,
  variant = "default",
  isActive = false,
  disabled = false,
  tooltip,
  className,
  onClick,
  ...props
}: StatusCardProps) {
  return (
    <button
      type="button"
      aria-pressed={isActive}
      aria-disabled={disabled}
      title={tooltip}
      onClick={disabled ? undefined : onClick}
      className={cn(
        statusCardVariants({ variant, isActive, disabled }),
        className
      )}
      {...props}
    >
      {/* Subtle left highlight for active state */}
      {isActive && (
        <div
          className={highlightBarVariants({ variant })}
          aria-hidden="true"
        />
      )}

      {/* Top row: Label + Icon */}
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-[var(--text-secondary)]">
          {label}
        </span>
        <div className={iconContainerVariants({ variant })}>
          {icon && React.isValidElement(icon)
            ? React.cloneElement(icon as React.ReactElement<{ className?: string; "aria-hidden"?: string }>, {
                className: "w-4 h-4",
                "aria-hidden": "true",
              })
            : icon}
        </div>
      </div>

      {/* Bottom row: Value */}
      <div className="flex items-baseline">
        <span className={valueVariants({ variant, isActive })}>
          {value}
        </span>
      </div>
    </button>
  );
}

export { StatusCard, statusCardVariants };
export type { StatusCardProps, StatusCardVariant };
