import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cva, type VariantProps } from "class-variance-authority"
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"
import { useScreenReaderAnnouncement } from "@/hooks/use-accessibility"

const appleInputVariants = cva(
  "flex w-full rounded-xl border bg-background/80 backdrop-blur-sm text-base transition-all outline-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
  {
    variants: {
      variant: {
        default:
          "border-gray-300 focus:border-blue-600 focus:ring-[3px] focus:ring-blue-600/20",
        filled:
          "bg-gray-100/50 border-transparent focus:bg-gray-100/70 focus:border-blue-600/50 focus:ring-[3px] focus:ring-blue-600/20",
        outline:
          "bg-transparent border-gray-300 focus:border-blue-600 focus:ring-[3px] focus:ring-blue-600/20",
      },
      inputSize: {
        sm: "h-9 px-3 py-2 text-sm",
        default: "h-11 px-4 py-3",
        lg: "h-13 px-5 py-4 text-base",
      },
      state: {
        default: "",
        error: "border-red-600 focus:border-red-600 focus:ring-red-600/20",
        success: "border-green-500 focus:border-green-500 focus:ring-green-500/20",
      },
    },
    defaultVariants: {
      variant: "default",
      inputSize: "default",
      state: "default",
    },
  }
)

export interface AppleInputProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'size' | 'onAnimationStart' | 'onDragStart' | 'onDragEnd' | 'onDrag'>,
    VariantProps<typeof appleInputVariants> {
  label?: string
  helperText?: string
  errorText?: string
  successText?: string
  showPasswordToggle?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  haptic?: "none" | "light" | "medium" | "heavy"
}

function AppleInput({
  className,
  type = "text",
  variant,
  inputSize,
  state,
  label,
  helperText,
  errorText,
  successText,
  showPasswordToggle = false,
  leftIcon,
  rightIcon,
  haptic = "light",
  disabled = false,
  required = false,
  onFocus,
  onBlur,
  onChange,
  value,
  ...props
}: AppleInputProps) {
  const [isFocused, setIsFocused] = React.useState(false)
  const [showPassword, setShowPassword] = React.useState(false)
  const [hasValue, setHasValue] = React.useState(!!value || !!props.defaultValue)
  const inputRef = React.useRef<HTMLInputElement>(null)
  const { announce } = useScreenReaderAnnouncement()

  const inputType = type === "password" && showPassword ? "text" : type

  React.useEffect(() => {
    if (state === "error" && errorText) {
      announce(`Error: ${errorText}`, 'assertive')
    } else if (state === "success" && successText) {
      announce(`Success: ${successText}`, 'polite')
    }
  }, [state, errorText, successText, announce])

  const handleFocus = React.useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(true)
    if (haptic !== "none" && inputRef.current) {
      triggerHaptic(inputRef.current, haptic)
    }
    onFocus?.(e)
  }, [haptic, onFocus])

  const handleBlur = React.useCallback((e: React.FocusEvent<HTMLInputElement>) => {
    setIsFocused(false)
    onBlur?.(e)
  }, [onBlur])

  const handleChange = React.useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setHasValue(e.target.value.length > 0)
    onChange?.(e)
  }, [onChange])

  const togglePasswordVisibility = React.useCallback(() => {
    setShowPassword(!showPassword)
    if (inputRef.current) {
      triggerHaptic(inputRef.current, "light")
    }
  }, [showPassword])

  const springConfig = getSpringConfig('smooth')

  const showStateIcon = (state === "error" && errorText) || (state === "success" && successText)

  return (
    <div className="relative w-full">
      {/* Label */}
      {label && (
        <label
          htmlFor={props.id}
          className={cn(
            "block text-sm font-medium mb-1.5",
            disabled && "opacity-50"
          )}
        >
          {label}
          {required && <span className="text-red-600 ml-1">*</span>}
        </label>
      )}

      {/* Input Container */}
      <div className="relative">
        {/* Left Icon */}
        {leftIcon && (
          <div className="absolute inset-y-0 left-3 flex items-center text-gray-500 pointer-events-none [transform:none] [filter:none] [&>svg]:[vector-effect:non-scaling-stroke] [&>svg]:[shape-rendering:crispEdges]">
            {leftIcon}
          </div>
        )}

        {/* Input Field */}
        <motion.input
          ref={inputRef}
          type={inputType}
          data-slot="input"
          className={cn(
            appleInputVariants({ variant, inputSize, state, className }),
            leftIcon && "pl-10",
            (rightIcon || showPasswordToggle || showStateIcon) && "pr-10",
            "placeholder:text-gray-400 selection:bg-blue-600 selection:text-white"
          )}
          disabled={disabled}
          required={required}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onChange={handleChange}
          value={value}
          whileFocus={{ boxShadow: "0 0 0 3px rgba(59, 130, 246, 0.2)" }}
          transition={springConfig}
          {...props}
        />

        {/* Right Icons */}
        <div className="absolute inset-y-0 right-3 flex items-center gap-2">
          {/* State Icon */}
          <AnimatePresence>
            {state === "error" && errorText && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={springConfig}
                className="[transform:none] [filter:none]"
              >
                <AlertCircle className="w-5 h-5 text-red-600 [vector-effect:non-scaling-stroke] [shape-rendering:crispEdges]" />
              </motion.div>
            )}
            {state === "success" && successText && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                transition={springConfig}
                className="[transform:none] [filter:none]"
              >
                <CheckCircle2 className="w-5 h-5 text-green-500 [vector-effect:non-scaling-stroke] [shape-rendering:crispEdges]" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Password Toggle */}
          {type === "password" && showPasswordToggle && (
            <motion.button
              type="button"
              onClick={togglePasswordVisibility}
              className="text-gray-500 hover:text-gray-700 transition-colors focus:outline-none"
              whileHover={{ opacity: 0.7 }}
              whileTap={{ opacity: 0.5 }}
              transition={springConfig}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="w-5 h-5 [vector-effect:non-scaling-stroke] [shape-rendering:crispEdges]" />
              ) : (
                <Eye className="w-5 h-5 [vector-effect:non-scaling-stroke] [shape-rendering:crispEdges]" />
              )}
            </motion.button>
          )}

          {/* Custom Right Icon */}
          {rightIcon && !showPasswordToggle && (
            <div className="text-gray-500 [transform:none] [filter:none] [&>svg]:[vector-effect:non-scaling-stroke] [&>svg]:[shape-rendering:crispEdges]">
              {rightIcon}
            </div>
          )}
        </div>
      </div>

      {/* Helper/Error/Success Text */}
      <AnimatePresence mode="wait">
        {(helperText || errorText || successText) && (
          <motion.p
            key={errorText || successText || helperText}
            initial={{ opacity: 0, y: -4 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -4 }}
            transition={springConfig}
            className={cn(
              "text-xs mt-1.5 ml-1",
              state === "error" && errorText && "text-red-600",
              state === "success" && successText && "text-green-600",
              !errorText && !successText && "text-gray-500"
            )}
            role={state === "error" ? "alert" : undefined}
            aria-live={state === "error" ? "assertive" : "polite"}
          >
            {errorText || successText || helperText}
          </motion.p>
        )}
      </AnimatePresence>
    </div>
  )
}

AppleInput.displayName = "AppleInput"

export { AppleInput, appleInputVariants }
