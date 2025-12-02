import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority";

import { cn } from "../../utils"

const badgeVariants = cva(
  "inline-flex items-center justify-center rounded-lg border px-2.5 py-1 text-xs font-medium w-fit whitespace-nowrap shrink-0 [&>svg]:size-3 gap-1 [&>svg]:pointer-events-none focus-visible:border-ring focus-visible:ring-ring/50 focus-visible:ring-[3px] aria-invalid:ring-destructive/20 dark:aria-invalid:ring-destructive/40 aria-invalid:border-destructive transition-[color,box-shadow] overflow-hidden font-['Public_Sans',sans-serif]",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary-500 text-white [a&]:hover:bg-primary-600",
        secondary:
          "border-transparent bg-neutral-100 text-neutral-700 [a&]:hover:bg-neutral-200 dark:bg-neutral-700 dark:text-neutral-200",
        destructive:
          "border-transparent bg-error-500 text-white [a&]:hover:bg-error-600 focus-visible:ring-destructive/20 dark:focus-visible:ring-destructive/40",
        outline:
          "border-neutral-300 text-neutral-700 bg-white [a&]:hover:bg-neutral-50 dark:border-neutral-600 dark:text-neutral-200 dark:bg-neutral-800",
        success:
          "border-transparent bg-success-500 text-white [a&]:hover:bg-success-600",
        warning:
          "border-transparent bg-warning-500 text-neutral-900 [a&]:hover:bg-warning-600",
        pink:
          "border-transparent bg-pink-500 text-white [a&]:hover:bg-pink-600",
        cyan:
          "border-transparent bg-cyan-500 text-white [a&]:hover:bg-cyan-600",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

interface BadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof badgeVariants> {
  asChild?: boolean;
}

function Badge({
  className,
  variant,
  asChild = false,
  ...props
}: BadgeProps) {
  const Comp = asChild ? Slot : "span"

  return (
    <Comp
      data-slot="badge"
      className={cn(badgeVariants({ variant }), className)}
      {...props} />
  );
}

export { Badge, badgeVariants }
export type { BadgeProps }
