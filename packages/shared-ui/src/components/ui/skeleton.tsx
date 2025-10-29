import * as React from "react"

import { cn } from "../../utils"

interface SkeletonProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

function Skeleton({
  className,
  ...props
}: SkeletonProps) {
  return (
    <div
      data-slot="skeleton"
      className={cn("bg-primary/10 animate-pulse rounded-md", className)}
      {...props} />
  );
}

export { Skeleton }
export type { SkeletonProps }
