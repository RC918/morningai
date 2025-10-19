import { motion } from 'framer-motion'
import { cn } from '@/lib/utils'

const AppleCard = ({ 
  children, 
  className,
  hover = true,
  glass = false,
  gradient = false,
  ...props 
}) => {
  const baseClasses = cn(
    "rounded-3xl transition-all duration-300",
    glass 
      ? "bg-white/60 dark:bg-gray-800/60 backdrop-blur-xl border border-gray-200/50 dark:border-gray-700/50" 
      : "bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700",
    gradient && "bg-gradient-to-br from-white to-gray-50 dark:from-gray-800 dark:to-gray-900",
    className
  )

  if (hover) {
    return (
      <motion.div
        whileHover={{ 
          y: -4,
          scale: 1.01,
          transition: { duration: 0.2, ease: [0.4, 0, 0.2, 1] }
        }}
        className={cn(baseClasses, "hover:shadow-xl hover:border-blue-300 dark:hover:border-blue-600")}
        {...props}
      >
        {children}
      </motion.div>
    )
  }

  return (
    <div className={baseClasses} {...props}>
      {children}
    </div>
  )
}

const AppleCardHeader = ({ children, className, ...props }) => {
  return (
    <div className={cn("p-6 pb-4", className)} {...props}>
      {children}
    </div>
  )
}

const AppleCardTitle = ({ children, className, ...props }) => {
  return (
    <h3 
      className={cn(
        "text-2xl font-semibold tracking-tight text-gray-900 dark:text-white mb-2",
        className
      )} 
      {...props}
    >
      {children}
    </h3>
  )
}

const AppleCardDescription = ({ children, className, ...props }) => {
  return (
    <p 
      className={cn(
        "text-sm text-gray-600 dark:text-gray-400",
        className
      )} 
      {...props}
    >
      {children}
    </p>
  )
}

const AppleCardContent = ({ children, className, ...props }) => {
  return (
    <div className={cn("p-6 pt-0", className)} {...props}>
      {children}
    </div>
  )
}

const AppleCardFooter = ({ children, className, ...props }) => {
  return (
    <div 
      className={cn(
        "p-6 pt-4 border-t border-gray-200 dark:border-gray-700",
        className
      )} 
      {...props}
    >
      {children}
    </div>
  )
}

export {
  AppleCard,
  AppleCardHeader,
  AppleCardTitle,
  AppleCardDescription,
  AppleCardContent,
  AppleCardFooter
}
