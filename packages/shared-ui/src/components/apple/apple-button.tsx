import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { motion } from "framer-motion"

import { cn } from "../../utils"
import { getSpringConfig, triggerHaptic } from "../../lib/animations"

const appleButtonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-[3px] focus-visible:ring-offset-0",
  {
    variants: {
      variant: {
        primary:
          "bg-[var(--color-primary-600)] text-white shadow-[var(--shadow-sm)] hover:bg-[var(--color-primary-700)] hover:shadow-[var(--shadow-md)] focus-visible:ring-[var(--color-primary-600)]/30 active:shadow-[var(--shadow-sm)]",
        secondary:
          "bg-[var(--color-neutral-100)] text-[var(--color-neutral-900)] shadow-[var(--shadow-sm)] hover:bg-[var(--color-neutral-200)] hover:shadow-[var(--shadow-md)] focus-visible:ring-[var(--color-neutral-500)]/30 active:shadow-[var(--shadow-sm)]",
        destructive:
          "bg-[var(--color-error-600)] text-white shadow-[var(--shadow-sm)] hover:bg-[var(--color-error-700)] hover:shadow-[var(--shadow-md)] focus-visible:ring-[var(--color-error-600)]/30 active:shadow-[var(--shadow-sm)]",
        outline:
          "border border-[var(--color-neutral-300)] bg-white/80 backdrop-blur-sm shadow-[var(--shadow-sm)] hover:bg-[var(--color-neutral-50)] hover:text-[var(--color-neutral-900)] focus-visible:ring-[var(--color-primary-600)]/20 active:bg-[var(--color-neutral-100)]/80",
        ghost:
          "hover:bg-[var(--color-neutral-100)]/80 hover:text-[var(--color-neutral-900)] focus-visible:ring-[var(--color-primary-600)]/20 active:bg-[var(--color-neutral-100)]",
        link:
          "text-[var(--color-primary-600)] underline-offset-4 hover:underline focus-visible:ring-[var(--color-primary-600)]/20",
        filled:
          "bg-[var(--color-neutral-100)] text-[var(--color-neutral-900)] shadow-[var(--shadow-sm)] hover:shadow-[var(--shadow-sm)] focus-visible:ring-[var(--color-neutral-500)]/30 active:shadow-[var(--shadow-sm)]",
        tinted:
          "bg-[var(--color-primary-600)]/10 text-[var(--color-primary-600)] hover:bg-[var(--color-primary-600)]/20 focus-visible:ring-[var(--color-primary-600)]/30 active:bg-[var(--color-primary-600)]/15",
      },
      size: {
        sm: "h-8 rounded-[var(--radius-lg)] gap-1.5 px-3 text-sm has-[>svg]:px-2.5",
        default: "h-10 rounded-[var(--radius-xl)] gap-2 px-4 text-sm has-[>svg]:px-3",
        lg: "h-12 rounded-[var(--radius-xl)] gap-2 px-6 text-base has-[>svg]:px-4",
        icon: "size-10 rounded-[var(--radius-xl)]",
        "icon-sm": "size-8 rounded-[var(--radius-lg)]",
        "icon-lg": "size-12 rounded-[var(--radius-xl)]",
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

export interface AppleButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onAnimationStart' | 'onDragStart' | 'onDragEnd' | 'onDrag'>,
    VariantProps<typeof appleButtonVariants> {
  asChild?: boolean
}

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
}: AppleButtonProps) {
  const buttonRef = React.useRef<HTMLButtonElement>(null)
  const Comp = asChild ? Slot : motion.button

  const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return
    
    if (haptic !== "none" && haptic !== null && buttonRef.current) {
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
      whileHover={disabled ? {} : { scale: 1.03, y: -1 }}
      whileTap={disabled ? {} : { scale: 0.97, y: 0 }}
      transition={springConfig}
      {...props}
    >
      {children}
    </Comp>
  )
}

AppleButton.displayName = "AppleButton"

export { AppleButton, appleButtonVariants }
