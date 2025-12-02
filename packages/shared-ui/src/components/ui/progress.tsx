import * as React from "react"
import * as ProgressPrimitive from "@radix-ui/react-progress"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "../../utils"

const progressVariants = cva(
  "relative h-2 w-full overflow-hidden rounded-full",
  {
    variants: {
      variant: {
        default: "bg-primary-100",
        success: "bg-success-100",
        warning: "bg-warning-100",
        error: "bg-error-100",
        pink: "bg-pink-100",
        cyan: "bg-cyan-100",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

const indicatorVariants = cva(
  "h-full w-full flex-1 transition-all rounded-full",
  {
    variants: {
      variant: {
        default: "bg-primary-500",
        success: "bg-success-500",
        warning: "bg-warning-500",
        error: "bg-error-500",
        pink: "bg-pink-500",
        cyan: "bg-cyan-500",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

interface ProgressProps extends React.ComponentPropsWithoutRef<typeof ProgressPrimitive.Root>,
  VariantProps<typeof progressVariants> {
  className?: string;
  value?: number;
  showLabel?: boolean;
}

function Progress({
  className,
  value,
  variant,
  showLabel = false,
  ...props
}: ProgressProps) {
  return (
    <div className="flex items-center gap-3 w-full">
      <ProgressPrimitive.Root
        data-slot="progress"
        className={cn(progressVariants({ variant }), className)}
        {...props}>
        <ProgressPrimitive.Indicator
          data-slot="progress-indicator"
          className={cn(indicatorVariants({ variant }))}
          style={{ transform: `translateX(-${100 - (value || 0)}%)` }} />
      </ProgressPrimitive.Root>
      {showLabel && (
        <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300 min-w-[3ch] text-right">
          {value || 0}%
        </span>
      )}
    </div>
  );
}

export { Progress, progressVariants }
export type { ProgressProps }
