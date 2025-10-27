import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"
import { useAccessibleTabs, useScreenReaderAnnouncement } from "@/hooks/use-accessibility"

/**
 * AppleTabBar - iOS-style bottom tab navigation
 * 
 * Features:
 * - iOS-style tab bar with icons and labels
 * - Smooth spring animations
 * - Haptic feedback simulation
 * - Active state indicator
 * - Badge support for notifications
 * - Accessible with ARIA attributes
 * 
 * @example
 * <AppleTabBar value="home" onValueChange={setValue}>
 *   <AppleTabBarItem value="home" icon={<HomeIcon />} label="Home" />
 *   <AppleTabBarItem value="search" icon={<SearchIcon />} label="Search" badge={3} />
 * </AppleTabBar>
 */

interface AppleTabBarContextValue {
  value: string
  onValueChange: (value: string) => void
}

const AppleTabBarContext = React.createContext<AppleTabBarContextValue | null>(null)

interface AppleTabBarProps extends React.HTMLAttributes<HTMLElement> {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
}

function AppleTabBar({
  value,
  onValueChange,
  className,
  children,
  ...props
}: AppleTabBarProps) {
  return (
    <AppleTabBarContext.Provider value={{ value, onValueChange }}>
      <nav
        aria-label="Main navigation"
        className={cn(
          "fixed bottom-0 left-0 right-0 z-50",
          "bg-background/80 backdrop-blur-xl",
          "border-t border-border/50",
          "safe-area-inset-bottom",
          className
        )}
        {...props}
      >
        <div role="tablist" className="flex items-center justify-around px-2 py-1">
          {children}
        </div>
      </nav>
    </AppleTabBarContext.Provider>
  )
}

interface AppleTabBarItemProps extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'value'> {
  value: string
  icon: React.ReactNode
  label: string
  badge?: number
  disabled?: boolean
}

function AppleTabBarItem({
  value,
  icon,
  label,
  badge,
  disabled = false,
  className,
  onClick,
  ...props
}: AppleTabBarItemProps) {
  const context = React.useContext(AppleTabBarContext)
  if (!context) {
    throw new Error('AppleTabBarItem must be used within AppleTabBar')
  }
  const { value: selectedValue, onValueChange } = context
  const isActive = value === selectedValue
  const itemRef = React.useRef<HTMLButtonElement>(null)
  const { announce } = useScreenReaderAnnouncement()

  const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return
    
    if (itemRef.current) {
      triggerHaptic(itemRef.current, 'light')
    }
    
    announce(`${label} tab selected`, 'polite')
    onValueChange?.(value)
    onClick?.(e)
  }, [disabled, value, onValueChange, onClick, label, announce])

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
      aria-selected={isActive}
      aria-label={label}
      tabIndex={isActive ? 0 : -1}
      disabled={disabled}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      className={cn(
        "relative flex flex-col items-center justify-center",
        "min-w-[64px] flex-1 max-w-[120px]",
        "py-2 px-3",
        "outline-none",
        "transition-colors duration-200",
        disabled && "opacity-50 cursor-not-allowed",
        className
      )}
      whileTap={disabled ? {} : { scale: 0.95 }}
      transition={springConfig}
      {...props}
    >
      {/* Icon Container */}
      <motion.div
        className={cn(
          "relative mb-1",
          "transition-colors duration-200",
          isActive ? "text-primary" : "text-muted-foreground"
        )}
        animate={{
          scale: isActive ? 1.1 : 1,
        }}
        transition={springConfig}
      >
        {icon}
        
        {/* Badge */}
        {badge !== undefined && badge > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            className={cn(
              "absolute -top-1 -right-1",
              "min-w-[16px] h-4 px-1",
              "flex items-center justify-center",
              "bg-destructive text-white",
              "rounded-full",
              "text-[10px] font-semibold leading-none"
            )}
          >
            {badge > 99 ? "99+" : badge}
          </motion.div>
        )}
      </motion.div>

      {/* Label */}
      <motion.span
        className={cn(
          "text-[10px] font-medium leading-tight",
          "transition-colors duration-200",
          isActive ? "text-primary" : "text-muted-foreground"
        )}
        animate={{
          opacity: isActive ? 1 : 0.7,
        }}
        transition={springConfig}
      >
        {label}
      </motion.span>

      {/* Active Indicator */}
      {isActive && (
        <motion.div
          layoutId="activeTab"
          className="absolute inset-0 -z-10 bg-accent/30 rounded-xl"
          initial={false}
          transition={springConfig}
        />
      )}
    </motion.button>
  )
}

AppleTabBar.displayName = "AppleTabBar"
AppleTabBarItem.displayName = "AppleTabBarItem"

export { AppleTabBar, AppleTabBarItem }
