import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { Activity, AlertTriangle, CheckCircle, Clock, XCircle } from "lucide-react"

import { cn } from "../../utils"

const statusBadgeVariants = cva(
  "inline-flex items-center justify-center gap-1 rounded-md border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
  {
    variants: {
      status: {
        completed:
          "border-green-300 bg-green-100 text-green-800 dark:border-green-700 dark:bg-green-900/30 dark:text-green-400",
        running:
          "border-blue-300 bg-blue-100 text-blue-800 dark:border-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
        failed:
          "border-red-300 bg-red-100 text-red-800 dark:border-red-700 dark:bg-red-900/30 dark:text-red-400",
        queued:
          "border-gray-300 bg-gray-100 text-gray-800 dark:border-gray-700 dark:bg-gray-900/30 dark:text-gray-400",
        assigned:
          "border-yellow-300 bg-yellow-100 text-yellow-800 dark:border-yellow-700 dark:bg-yellow-900/30 dark:text-yellow-400",
        cancelled:
          "border-orange-300 bg-orange-100 text-orange-800 dark:border-orange-700 dark:bg-orange-900/30 dark:text-orange-400",
      },
    },
    defaultVariants: {
      status: "queued",
    },
  }
)

export interface StatusBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement>,
    VariantProps<typeof statusBadgeVariants> {
  /**
   * The status to display
   */
  status?: "completed" | "running" | "failed" | "queued" | "assigned" | "cancelled"
  /**
   * Whether to show an icon
   */
  showIcon?: boolean
  /**
   * Custom icon to display (overrides default status icon)
   */
  icon?: React.ReactNode
}

const getStatusIcon = (status: StatusBadgeProps["status"]) => {
  switch (status) {
    case "completed":
      return <CheckCircle className="w-3 h-3" />
    case "running":
      return <Activity className="w-3 h-3 motion-safe:animate-pulse motion-reduce:animate-none" />
    case "failed":
      return <XCircle className="w-3 h-3" />
    case "queued":
    case "assigned":
      return <Clock className="w-3 h-3" />
    case "cancelled":
      return <AlertTriangle className="w-3 h-3" />
    default:
      return <Activity className="w-3 h-3" />
  }
}

function StatusBadge({
  className,
  status = "queued",
  showIcon = true,
  icon,
  children,
  ...props
}: StatusBadgeProps) {
  return (
    <span
      className={cn(statusBadgeVariants({ status }), className)}
      {...props}
    >
      {showIcon && (icon || getStatusIcon(status))}
      {children}
    </span>
  )
}

export { StatusBadge, statusBadgeVariants }
