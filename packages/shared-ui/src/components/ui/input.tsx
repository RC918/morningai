import * as React from "react"

import { cn } from "../../utils"

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  className?: string;
}

function Input({
  className,
  type,
  ...props
}: InputProps) {
  return (
    <input
      type={type}
      data-slot="input"
      className={cn(
        "file:text-neutral-700 placeholder:text-neutral-400 selection:bg-primary-500 selection:text-white dark:bg-neutral-800 border-neutral-300 flex h-10 w-full min-w-0 rounded-lg border bg-white px-3 py-2 text-sm shadow-sm transition-all outline-none file:inline-flex file:h-7 file:border-0 file:bg-transparent file:text-sm file:font-medium disabled:pointer-events-none disabled:cursor-not-allowed disabled:opacity-50 disabled:bg-neutral-100 font-['Public_Sans',sans-serif] dark:border-neutral-600 dark:text-neutral-100 dark:placeholder:text-neutral-500",
        "focus-visible:border-primary-500 focus-visible:ring-primary-500/20 focus-visible:ring-[3px]",
        "aria-invalid:ring-error-500/20 dark:aria-invalid:ring-error-500/40 aria-invalid:border-error-500",
        className
      )}
      {...props} />
  );
}

export { Input }
export type { InputProps }
