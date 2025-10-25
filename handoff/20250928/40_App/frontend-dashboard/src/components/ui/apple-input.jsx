import * as React from "react"
import { motion, AnimatePresence } from "framer-motion"
import { cva } from "class-variance-authority"
import { Eye, EyeOff, AlertCircle, CheckCircle2 } from "lucide-react"

import { cn } from "@/lib/utils"
import { getSpringConfig, triggerHaptic } from "@/lib/spring-animation"

const appleInputVariants = cva(
  "flex w-full rounded-xl border bg-background/80 backdrop-blur-sm text-base transition-all outline-none disabled:cursor-not-allowed disabled:opacity-50 md:text-sm",
  {
    variants: {
      variant: {
        default:
          "border-input focus:border-primary focus:ring-[3px] focus:ring-primary/20",
        filled:
          "bg-accent/50 border-transparent focus:bg-accent/70 focus:border-primary/50 focus:ring-[3px] focus:ring-primary/20",
        outline:
          "bg-transparent border-input focus:border-primary focus:ring-[3px] focus:ring-primary/20",
      },
      inputSize: {
        sm: "h-9 px-3 py-2 text-sm",
        default: "h-11 px-4 py-3",
        lg: "h-13 px-5 py-4 text-base",
      },
      state: {
        default: "",
        error: "border-destructive focus:border-destructive focus:ring-destructive/20",
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
}) {
  const [isFocused, setIsFocused] = React.useState(false)
  const [showPassword, setShowPassword] = React.useState(false)
  const [hasValue, setHasValue] = React.useState(!!value || !!props.defaultValue)
  const inputRef = React.useRef(null)

  const inputType = type === "password" && showPassword ? "text" : type

  const handleFocus = React.useCallback((e) => {
    setIsFocused(true)
    if (haptic !== "none" && inputRef.current) {
      triggerHaptic(inputRef.current, haptic)
    }
    onFocus?.(e)
  }, [haptic, onFocus])

  const handleBlur = React.useCallback((e) => {
    setIsFocused(false)
    onBlur?.(e)
  }, [onBlur])

  const handleChange = React.useCallback((e) => {
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

  const labelVariants = {
    default: {
      y: 0,
      scale: 1,
      color: "var(--muted-foreground)",
    },
    focused: {
      y: -24,
      scale: 0.85,
      color: state === "error" ? "var(--destructive)" : state === "success" ? "var(--green-500)" : "var(--primary)",
    },
  }

  const showFloatingLabel = label && (isFocused || hasValue)
  const showStateIcon = (state === "error" && errorText) || (state === "success" && successText)

  return (
    <div className="relative w-full">
      {/* Floating Label */}
      {label && (
        <motion.label
          htmlFor={props.id}
          className={cn(
            "absolute left-4 pointer-events-none origin-left font-medium transition-colors",
            showFloatingLabel ? "text-xs" : "text-sm top-1/2 -translate-y-1/2",
            disabled && "opacity-50"
          )}
          initial="default"
          animate={showFloatingLabel ? "focused" : "default"}
          variants={labelVariants}
          transition={springConfig}
        >
          {label}
          {required && <span className="text-destructive ml-1">*</span>}
        </motion.label>
      )}

      {/* Input Container */}
      <div className="relative">
        {/* Left Icon */}
        {leftIcon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground pointer-events-none">
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
            label && "pt-6 pb-2",
            leftIcon && "pl-10",
            (rightIcon || showPasswordToggle || showStateIcon) && "pr-10",
            "placeholder:text-muted-foreground/50 selection:bg-primary selection:text-primary-foreground"
          )}
          disabled={disabled}
          required={required}
          onFocus={handleFocus}
          onBlur={handleBlur}
          onChange={handleChange}
          value={value}
          whileFocus={{ scale: 1.01 }}
          transition={springConfig}
          {...props}
        />

        {/* Right Icons */}
        <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
          {/* State Icon */}
          <AnimatePresence>
            {state === "error" && errorText && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={springConfig}
              >
                <AlertCircle className="w-4 h-4 text-destructive" />
              </motion.div>
            )}
            {state === "success" && successText && (
              <motion.div
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                transition={springConfig}
              >
                <CheckCircle2 className="w-4 h-4 text-green-500" />
              </motion.div>
            )}
          </AnimatePresence>

          {/* Password Toggle */}
          {type === "password" && showPasswordToggle && (
            <motion.button
              type="button"
              onClick={togglePasswordVisibility}
              className="text-muted-foreground hover:text-foreground transition-colors focus:outline-none"
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              transition={springConfig}
              aria-label={showPassword ? "Hide password" : "Show password"}
            >
              {showPassword ? (
                <EyeOff className="w-4 h-4" />
              ) : (
                <Eye className="w-4 h-4" />
              )}
            </motion.button>
          )}

          {/* Custom Right Icon */}
          {rightIcon && !showPasswordToggle && (
            <div className="text-muted-foreground">
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
              state === "error" && errorText && "text-destructive",
              state === "success" && successText && "text-green-600 dark:text-green-500",
              !errorText && !successText && "text-muted-foreground"
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
