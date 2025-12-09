import * as React from "react"
import * as TooltipPrimitive from "@radix-ui/react-tooltip"

import { cn } from "../../utils"

interface TooltipProviderProps extends React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Provider> {
  delayDuration?: number;
}

function TooltipProvider({
  delayDuration = 0,
  ...props
}: TooltipProviderProps) {
  return (<TooltipPrimitive.Provider data-slot="tooltip-provider" delayDuration={delayDuration} {...props} />);
}

interface TooltipProps extends React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Root> {}

function Tooltip({
  ...props
}: TooltipProps) {
  return (
    <TooltipProvider>
      <TooltipPrimitive.Root data-slot="tooltip" {...props} />
    </TooltipProvider>
  );
}

interface TooltipTriggerProps extends React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Trigger> {}

function TooltipTrigger({
  ...props
}: TooltipTriggerProps) {
  return <TooltipPrimitive.Trigger data-slot="tooltip-trigger" {...props} />;
}

interface TooltipContentProps extends React.ComponentPropsWithoutRef<typeof TooltipPrimitive.Content> {
  className?: string;
  sideOffset?: number;
  arrowClassName?: string;
}

function TooltipContent({
  className,
  sideOffset = 0,
  arrowClassName,
  children,
  ...props
}: TooltipContentProps) {
  return (
    <TooltipPrimitive.Portal>
      <TooltipPrimitive.Content
        data-slot="tooltip-content"
        sideOffset={sideOffset}
        className={cn(
          "bg-primary text-primary-foreground animate-in fade-in-0 zoom-in-95 data-[state=closed]:animate-out data-[state=closed]:fade-out-0 data-[state=closed]:zoom-out-95 data-[side=bottom]:slide-in-from-top-2 data-[side=left]:slide-in-from-right-2 data-[side=right]:slide-in-from-left-2 data-[side=top]:slide-in-from-bottom-2 z-50 w-fit origin-(--radix-tooltip-content-transform-origin) rounded-md px-3 py-1.5 text-xs text-balance",
          className
        )}
        {...props}>
        {children}
        <TooltipPrimitive.Arrow
          className={cn(
            "z-50 size-2.5 translate-y-[calc(-50%_-_2px)] rotate-45 rounded-[2px]",
            arrowClassName || "bg-primary fill-primary"
          )}
        />
      </TooltipPrimitive.Content>
    </TooltipPrimitive.Portal>
  );
}

export { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider }
export type { TooltipProps, TooltipTriggerProps, TooltipContentProps, TooltipProviderProps }
