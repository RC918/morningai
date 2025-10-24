import { useTheme } from "next-themes"
import { Toaster as Sonner, toast } from "sonner"
import { useEffect, useRef } from "react"

const Toaster = ({
  ...props
}) => {
  const { theme = "system" } = useTheme()
  const liveRegionRef = useRef(null)

  useEffect(() => {
    if (!liveRegionRef.current) {
      const region = document.createElement('div')
      region.setAttribute('role', 'status')
      region.setAttribute('aria-live', 'polite')
      region.setAttribute('aria-atomic', 'true')
      region.className = 'sr-only'
      document.body.appendChild(region)
      liveRegionRef.current = region
    }

    const originalToast = toast
    const announceToast = (message, type) => {
      if (liveRegionRef.current && typeof message === 'string') {
        const announcement = type ? `${type}: ${message}` : message
        liveRegionRef.current.textContent = announcement
        
        setTimeout(() => {
          if (liveRegionRef.current) {
            liveRegionRef.current.textContent = ''
          }
        }, 1000)
      }
    }

    toast.success = (...args) => {
      announceToast(args[0], 'Success')
      return originalToast.success(...args)
    }
    
    toast.error = (...args) => {
      announceToast(args[0], 'Error')
      return originalToast.error(...args)
    }
    
    toast.info = (...args) => {
      announceToast(args[0], 'Info')
      return originalToast.info(...args)
    }
    
    toast.warning = (...args) => {
      announceToast(args[0], 'Warning')
      return originalToast.warning(...args)
    }

    return () => {
      if (liveRegionRef.current && document.body.contains(liveRegionRef.current)) {
        document.body.removeChild(liveRegionRef.current)
      }
    }
  }, [])

  return (
    <Sonner
      theme={theme}
      className="toaster group"
      style={
        {
          "--normal-bg": "var(--popover)",
          "--normal-text": "var(--popover-foreground)",
          "--normal-border": "var(--border)"
        }
      }
      {...props} />
  );
}

export { Toaster }
