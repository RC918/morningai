"use client"

import * as React from "react"
import { OTPInput, OTPInputContext } from "input-otp"
import { MinusIcon } from "lucide-react"

import { cn } from "../../utils"

type InputOTPProps = React.ComponentPropsWithoutRef<typeof OTPInput>

function InputOTP({
  className,
  containerClassName,
  maxLength = 6,
  ...props
}: InputOTPProps) {
  return (
    <OTPInput
      data-slot="input-otp"
      maxLength={maxLength}
      containerClassName={cn("flex items-center gap-2 has-disabled:opacity-50", containerClassName)}
      className={cn("disabled:cursor-not-allowed", className)}
      {...props} />
  );
}

interface InputOTPGroupProps extends React.HTMLAttributes<HTMLDivElement> {
  className?: string;
}

function InputOTPGroup({
  className,
  ...props
}: InputOTPGroupProps) {
  return (
    <div
      data-slot="input-otp-group"
      className={cn("flex items-center", className)}
      {...props} />
  );
}

interface InputOTPSlotProps extends React.HTMLAttributes<HTMLDivElement> {
  index: number;
  className?: string;
}

function InputOTPSlot({
  index,
  className,
  ...props
}: InputOTPSlotProps) {
  const inputOTPContext = React.useContext(OTPInputContext)
  const { char, hasFakeCaret, isActive } = inputOTPContext?.slots[index] ?? {}

  return (
    <div
      data-slot="input-otp-slot"
      data-active={isActive}
      className={cn(
        "data-[active=true]:border-ring data-[active=true]:ring-ring/50 data-[active=true]:aria-invalid:ring-destructive/20 dark:data-[active=true]:aria-invalid:ring-destructive/40 aria-invalid:border-destructive data-[active=true]:aria-invalid:border-destructive dark:bg-input/30 border-input relative flex h-9 w-9 items-center justify-center border-y border-r text-sm shadow-xs transition-all outline-none first:rounded-l-md first:border-l last:rounded-r-md data-[active=true]:z-10 data-[active=true]:ring-[3px]",
        className
      )}
      {...props}>
      {char}
      {hasFakeCaret && (
        <div
          className="pointer-events-none absolute inset-0 flex items-center justify-center">
          <div className="animate-caret-blink bg-foreground h-4 w-px duration-1000" />
        </div>
      )}
    </div>
  );
}

interface InputOTPSeparatorProps extends React.HTMLAttributes<HTMLDivElement> {}

function InputOTPSeparator({
  ...props
}: InputOTPSeparatorProps) {
  return (
    <div data-slot="input-otp-separator" role="separator" {...props}>
      <MinusIcon />
    </div>
  );
}

export { InputOTP, InputOTPGroup, InputOTPSlot, InputOTPSeparator }
export type { InputOTPProps, InputOTPGroupProps, InputOTPSlotProps, InputOTPSeparatorProps }
