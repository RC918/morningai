import * as React from "react"
import { motion } from "framer-motion"
import { cn } from "@/lib/utils"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"

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

const AppleTabBarContext = React.createContext({
  value: "",
  onValueChange: () => {},
})

function AppleTabBar({
  value,
  onValueChange,
  className,
  children,
  ...props
}) {
  return (
    <AppleTabBarContext.Provider value={{ value, onValueChange }}>
      <nav
        role="tablist"
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
        <div className="flex items-center justify-around px-2 py-1">
          {children}
        </div>
      </nav>
    </AppleTabBarContext.Provider>
  )
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
}) {
  const { value: selectedValue, onValueChange } = React.useContext(AppleTabBarContext)
  const isActive = value === selectedValue
  const itemRef = React.useRef(null)

  const handleClick = React.useCallback((e) => {
    if (disabled) return
    
    if (itemRef.current) {
      triggerHaptic(itemRef.current, 'light')
    }
    
    onValueChange?.(value)
    onClick?.(e)
  }, [disabled, value, onValueChange, onClick])

  const springConfig = getSpringConfig('snappy')

  return (
    <motion.button
      ref={itemRef}
      role="tab"
      aria-selected={isActive}
      aria-label={label}
      disabled={disabled}
      onClick={handleClick}
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
