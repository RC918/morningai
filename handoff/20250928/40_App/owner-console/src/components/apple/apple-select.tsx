import * as React from "react"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  type SelectProps,
} from '@morningai/shared-ui'
import { cn } from "@/lib/utils"

/**
 * AppleSelect - Apple-styled select component
 * 
 * Wraps the shared-ui Select with Apple design system styling to match AppleInput and AppleButton.
 * Uses the same visual language: rounded-xl, consistent borders, focus rings, and semi-transparent backgrounds.
 * 
 * @example
 * ```tsx
 * <AppleSelect value={value} onValueChange={setValue}>
 *   <SelectItem value="option1">Option 1</SelectItem>
 *   <SelectItem value="option2">Option 2</SelectItem>
 * </AppleSelect>
 * ```
 */

interface AppleSelectProps extends SelectProps {
  className?: string
  triggerClassName?: string
  contentClassName?: string
}

export const AppleSelect = React.forwardRef<
  React.ElementRef<typeof Select>,
  AppleSelectProps
>(({ className, triggerClassName, contentClassName, children, ...props }, ref) => {
  return (
    <Select {...props}>
      <SelectTrigger
        className={cn(
          // Base styling matching AppleInput
          "rounded-xl border border-gray-300 bg-white/80 backdrop-blur-sm text-base transition-all outline-none",
          // Focus state matching AppleInput
          "focus:border-blue-600 focus:ring-[3px] focus:ring-blue-600/20",
          // Hover state
          "hover:bg-gray-50",
          // Dark mode
          "dark:bg-neutral-900/60 dark:border-neutral-700 dark:hover:bg-neutral-800/60",
          // Sizing matching AppleInput default size
          "h-11 px-4 py-3",
          // Disabled state
          "disabled:cursor-not-allowed disabled:opacity-50",
          // Typography
          "md:text-sm",
          triggerClassName
        )}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent
        className={cn(
          // Apple-styled dropdown
          "rounded-xl shadow-lg bg-white/95 backdrop-blur-md border border-gray-200",
          // Dark mode
          "dark:bg-neutral-900/95 dark:border-neutral-700",
          contentClassName
        )}
      >
        {children}
      </SelectContent>
    </Select>
  )
})

AppleSelect.displayName = "AppleSelect"

export { SelectItem } from '@morningai/shared-ui'
