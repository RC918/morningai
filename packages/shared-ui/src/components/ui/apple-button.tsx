import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { motion, type Transition } from "framer-motion"

import { cn } from "../../utils"

const appleButtonVariants = cva(
  "inline-flex items-center justify-center gap-2 whitespace-nowrap font-medium transition-all disabled:pointer-events-none disabled:opacity-50 [&_svg]:pointer-events-none [&_svg:not([class*='size-'])]:size-4 shrink-0 [&_svg]:shrink-0 outline-none focus-visible:ring-[3px] focus-visible:ring-offset-0",
  {
    variants: {
      variant: {
        primary:
          "bg-primary-600 text-white shadow-sm hover:bg-primary-700 hover:shadow-md focus-visible:ring-primary-600/30 active:shadow-sm",
        secondary:
          "bg-neutral-100 text-neutral-900 shadow-sm hover:bg-neutral-200 hover:shadow-md focus-visible:ring-neutral-500/30 active:shadow-sm",
        destructive:
          "bg-error-600 text-white shadow-sm hover:bg-error-700 hover:shadow-md focus-visible:ring-error-600/30 active:shadow-sm",
        outline:
          "border border-neutral-300 bg-white/80 backdrop-blur-sm shadow-xs hover:bg-neutral-50 hover:text-neutral-900 focus-visible:ring-primary-600/20 active:bg-neutral-100/80",
        ghost:
          "hover:bg-neutral-100/80 hover:text-neutral-900 focus-visible:ring-primary-600/20 active:bg-neutral-100",
        link:
          "text-primary-600 underline-offset-4 hover:underline focus-visible:ring-primary-600/20",
        filled:
          "bg-neutral-100 text-neutral-900 shadow-xs hover:shadow-sm focus-visible:ring-neutral-500/30 active:shadow-xs",
        tinted:
          "bg-primary-600/10 text-primary-600 hover:bg-primary-600/20 focus-visible:ring-primary-600/30 active:bg-primary-600/15",
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

export type AppleButtonHapticVariant = NonNullable<VariantProps<typeof appleButtonVariants>['haptic']>

export interface AppleButtonProps
  extends Omit<React.ButtonHTMLAttributes<HTMLButtonElement>, 'onAnimationStart' | 'onDragStart' | 'onDragEnd' | 'onDrag'>,
    VariantProps<typeof appleButtonVariants> {
  asChild?: boolean
  /**
   * Adapter function for haptic feedback.
   * Called when the button is clicked with the button element and haptic type.
   * Applications can inject their own haptic implementation.
   */
  onHapticFeedback?: (element: HTMLButtonElement, type: AppleButtonHapticVariant) => void
  /**
   * Spring animation configuration for framer-motion.
   * Applications can inject their own spring configuration.
   * If not provided, framer-motion will use its default transition.
   */
  springConfig?: Transition
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
  onHapticFeedback,
  springConfig,
  ...props
}: AppleButtonProps) {
  const buttonRef = React.useRef<HTMLButtonElement>(null)
  const Comp = asChild ? Slot : motion.button

  const handleClick = React.useCallback((e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return
    
    if (onHapticFeedback && haptic !== "none" && haptic != null && buttonRef.current) {
      onHapticFeedback(buttonRef.current, haptic)
    }
    
    onClick?.(e)
  }, [disabled, haptic, onClick, onHapticFeedback])

  // Motion props should only be applied when not using asChild (Slot)
  const motionProps = asChild ? {} : {
    whileHover: disabled ? {} : { scale: 1.02 },
    whileTap: disabled ? {} : { scale: 0.98 },
    transition: springConfig,
  }

  return (
    <Comp
      ref={buttonRef}
      data-slot="button"
      className={cn(appleButtonVariants({ variant, size, className }))}
      disabled={disabled}
      onClick={handleClick}
      {...motionProps}
      {...props}
    >
      {children}
    </Comp>
  )
}

AppleButton.displayName = "AppleButton"

export { AppleButton, appleButtonVariants }
