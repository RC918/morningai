import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva } from "class-variance-authority"
import { motion } from "framer-motion"

import { cn } from "@/lib/utils"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"

const appleButtonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-[3px] focus-visible:ring-offset-0",
  {
    variants: {
      variant: {
        primary:
          "bg-primary text-primary-foreground shadow-sm hover:shadow-md focus-visible:ring-primary/30 active:shadow-sm",
        secondary:
          "bg-secondary text-secondary-foreground shadow-sm hover:shadow-md focus-visible:ring-secondary/30 active:shadow-sm",
        destructive:
          "bg-destructive text-white shadow-sm hover:shadow-md focus-visible:ring-destructive/30 active:shadow-sm",
        outline:
          "border border-input bg-background/80 backdrop-blur-sm shadow-xs hover:bg-accent hover:text-accent-foreground focus-visible:ring-primary/20 active:bg-accent/80",
        ghost:
          "hover:bg-accent/80 hover:text-accent-foreground focus-visible:ring-primary/20 active:bg-accent",
        link:
          "text-primary underline-offset-4 hover:underline focus-visible:ring-primary/20",
        filled:
          "bg-accent text-accent-foreground shadow-xs hover:shadow-sm focus-visible:ring-accent/30 active:shadow-xs",
        tinted:
          "bg-primary/10 text-primary hover:bg-primary/20 focus-visible:ring-primary/30 active:bg-primary/15",
      },
      size: {
        sm: "h-8 rounded-lg gap-1.5 px-3 text-sm has-[>svg]:px-2.5",
        default: "h-10 rounded-xl gap-2 px-4 text-sm has-[>svg]:px-3",
        lg: "h-12 rounded-xl gap-2 px-6 text-base has-[>svg]:px-4",
        icon: "size-10 rounded-xl",
        "icon-sm": "size-8 rounded-lg",
        "icon-lg": "size-12 rounded-xl",
      },
      haptic: {
        none: "",
        light: "",
        medium: "",
        heavy: "",
      },
    },
    defaultVariants: {
      variant: "primary",
      size: "default",
      haptic: "medium",
    },
  }
)

function AppleButton({
  className,
  variant,
  size,
  haptic = "medium",
  asChild = false,
  disabled = false,
  children,
  onClick,
  ...props
}) {
  const buttonRef = React.useRef(null)
  const Comp = asChild ? Slot : motion.button

  const handleClick = React.useCallback((e) => {
    if (disabled) return
    
    if (haptic !== "none" && buttonRef.current) {
      triggerHaptic(buttonRef.current, haptic)
    }
    
    onClick?.(e)
  }, [disabled, haptic, onClick])

  const springConfig = getSpringConfig('snappy')

  return (
    <Comp
      ref={buttonRef}
      data-slot="button"
      className={cn(appleButtonVariants({ variant, size, className }))}
      disabled={disabled}
      onClick={handleClick}
      whileHover={disabled ? {} : { scale: 1.02 }}
      whileTap={disabled ? {} : { scale: 0.98 }}
      transition={springConfig}
      {...props}
    >
      {children}
    </Comp>
  )
}

AppleButton.displayName = "AppleButton"

export { AppleButton, appleButtonVariants }
