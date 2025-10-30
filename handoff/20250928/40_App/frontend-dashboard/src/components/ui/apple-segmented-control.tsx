import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"
import { useScreenReaderAnnouncement } from "@/hooks/use-accessibility"

/**
 * AppleSegmentedControl - iOS-style segmented picker
 * 
 * Features:
 * - iOS-style segmented control for switching between views
 * - Smooth sliding animation for active segment
 * - Spring physics for natural feel
 * - Haptic feedback simulation
 * - Full keyboard navigation support
 * - Accessible with ARIA attributes
 * 
 * @example
 * <AppleSegmentedControl value="all" onValueChange={setValue}>
 *   <AppleSegmentedControlItem value="all">All</AppleSegmentedControlItem>
 *   <AppleSegmentedControlItem value="active">Active</AppleSegmentedControlItem>
 *   <AppleSegmentedControlItem value="completed">Completed</AppleSegmentedControlItem>
 * </AppleSegmentedControl>
 */

interface AppleSegmentedControlContextValue {
  value: string
  onValueChange: (value: string) => void
}

const AppleSegmentedControlContext = React.createContext<AppleSegmentedControlContextValue>({
  value: "",
  onValueChange: () => {},
})

type SegmentedControlSize = "sm" | "default" | "lg"

export interface AppleSegmentedControlProps extends React.HTMLAttributes<HTMLDivElement> {
  value: string
  onValueChange: (value: string) => void
  size?: SegmentedControlSize
}

function AppleSegmentedControl({
  value,
  onValueChange,
  className,
  children,
  size = "default",
  ...props
}: AppleSegmentedControlProps) {
  const segments = React.Children.toArray(children)
  
  return (
    <AppleSegmentedControlContext.Provider value={{ value, onValueChange }}>
      <div
        role="tablist"
        aria-label="Segmented control"
        className={cn(
          "inline-flex items-center",
          "bg-accent/30 backdrop-blur-sm",
          "rounded-xl p-0.5",
          "border border-border/50",
          size === "sm" && "h-8",
          size === "default" && "h-10",
          size === "lg" && "h-12",
          className
        )}
        {...props}
      >
        {segments}
      </div>
    </AppleSegmentedControlContext.Provider>
  )
}

export interface AppleSegmentedControlItemProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onAnimationStart' | 'onDragStart' | 'onDragEnd' | 'onDrag'> {
  value: string
}

function AppleSegmentedControlItem({
  value,
  disabled = false,
  className,
  children,
  onClick,
  ...props
}: AppleSegmentedControlItemProps) {
  const { value: selectedValue, onValueChange } = React.useContext(AppleSegmentedControlContext)
  const isActive = value === selectedValue
  const itemRef = React.useRef<HTMLButtonElement>(null)
  const { announce } = useScreenReaderAnnouncement()

  const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return
    
    if (itemRef.current) {
      triggerHaptic(itemRef.current, 'light')
    }
    
    announce(`${children} selected`, 'polite')
    onValueChange?.(value)
    onClick?.(e)
  }, [disabled, value, onValueChange, onClick, children, announce])

  const handleKeyDown = React.useCallback((e: React.KeyboardEvent<HTMLButtonElement>) => {
    if (disabled) return
    
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick(e as unknown as React.MouseEvent<HTMLButtonElement>)
    }
  }, [disabled, handleClick])

  const springConfig = getSpringConfig('snappy')

  return (
    <motion.button
      ref={itemRef}
      role="tab"
      type="button"
      aria-selected={isActive}
      disabled={disabled}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={cn(
        "relative z-10",
        "flex items-center justify-center",
        "px-4 py-1.5",
        "text-sm font-medium",
        "rounded-lg",
        "outline-none",
        "transition-colors duration-200",
        "focus-visible:ring-2 focus-visible:ring-primary/50 focus-visible:ring-offset-2",
        isActive ? "text-foreground" : "text-muted-foreground hover:text-foreground",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      whileTap={disabled ? {} : { scale: 0.97 }}
      transition={springConfig}
      {...props}
    >
      {/* Active Background */}
      {isActive && (
        <motion.div
          layoutId="activeSegment"
          className={cn(
            "absolute inset-0 -z-10",
            "bg-background",
            "rounded-lg",
            "shadow-sm"
          )}
          initial={false}
          transition={springConfig}
        />
      )}
      
      {children}
    </motion.button>
  )
}

AppleSegmentedControl.displayName = "AppleSegmentedControl"
AppleSegmentedControlItem.displayName = "AppleSegmentedControlItem"

export { AppleSegmentedControl, AppleSegmentedControlItem }
