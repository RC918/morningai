import * as React from "react"
import {
  Select,
  SelectContent,
  SelectItem as BaseSelectItem,
  SelectTrigger,
  SelectValue,
  type SelectProps,
  type SelectItemProps as BaseSelectItemProps,
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
          "rounded-xl border border-gray-200 bg-white/80 backdrop-blur-sm text-base transition-all outline-none",
          // Text color - always dark text for readability on light background
          "text-neutral-900",
          // Focus state matching AppleInput
          "focus:border-blue-600 focus:ring-[3px] focus:ring-blue-600/20",
          // Hover state
          "hover:bg-gray-50 hover:text-neutral-900",
          // Dark mode - keep pill light with dark text for Apple style
          "dark:bg-white dark:hover:bg-neutral-100 dark:border-neutral-200 dark:text-neutral-900",
          // Sizing matching AppleInput default size
          "h-11 px-4 py-3",
          // Disabled state
          "disabled:cursor-not-allowed disabled:opacity-50",
          // Typography matching AppleButton and AppleInput
          "text-callout md:text-callout",
          triggerClassName
        )}
      >
        <SelectValue />
      </SelectTrigger>
      <SelectContent
        className={cn(
          // Apple-styled dropdown - keep light in both modes for consistency with trigger
          "rounded-xl shadow-lg bg-white/95 backdrop-blur-md border border-gray-200",
          // Text color - always dark for readability on light background
          "text-neutral-900",
          // Dark mode - keep dropdown light like the trigger pill
          "dark:bg-white/95 dark:border-neutral-200 dark:text-neutral-900",
          // Ensure proper spacing for items
          "py-2",
          contentClassName
        )}
      >
        {children}
      </SelectContent>
    </Select>
  )
})

AppleSelect.displayName = "AppleSelect"

/**
 * AppleSelectItem - Apple-styled select item component
 * 
 * Ensures proper text color and spacing in both light and dark modes.
 * Always uses dark text on light background for consistency with Apple design.
 */
export function AppleSelectItem({
  className,
  children,
  ...props
}: BaseSelectItemProps) {
  return (
    <BaseSelectItem
      className={cn(
        // Override default focus colors to maintain dark text on light background
        "text-neutral-900 dark:text-neutral-900",
        "focus:bg-neutral-100 focus:text-neutral-900",
        "dark:focus:bg-neutral-100 dark:focus:text-neutral-900",
        // Proper spacing to prevent text overlap with checkmark (shared-ui uses absolute right-2 for checkmark)
        // Keep vertical padding but ensure right padding accommodates the checkmark
        "py-2.5 pl-3 pr-8",
        // Ensure proper line height
        "leading-normal",
        className
      )}
      {...props}
    >
      {children}
    </BaseSelectItem>
  )
}

AppleSelectItem.displayName = "AppleSelectItem"

// Export both for convenience
export { AppleSelectItem as SelectItem }
