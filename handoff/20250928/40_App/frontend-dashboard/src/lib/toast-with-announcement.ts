import { toast as sonnerToast } from 'sonner'

let liveRegion: HTMLDivElement | null = null

const ensureLiveRegion = (): HTMLDivElement | null => {
  if (!liveRegion && typeof document !== 'undefined') {
    liveRegion = document.createElement('div')
    liveRegion.setAttribute('role', 'status')
    liveRegion.setAttribute('aria-live', 'polite')
    liveRegion.setAttribute('aria-atomic', 'true')
    liveRegion.className = 'sr-only'
    liveRegion.style.position = 'absolute'
    liveRegion.style.left = '-10000px'
    liveRegion.style.width = '1px'
    liveRegion.style.height = '1px'
    liveRegion.style.overflow = 'hidden'
    document.body.appendChild(liveRegion)
  }
  return liveRegion
}

const announce = (message: any, type?: string): void => {
  const region = ensureLiveRegion()
  if (region && typeof message === 'string') {
    const announcement = type ? `${type}: ${message}` : message
    region.textContent = announcement
    
    setTimeout(() => {
      if (region) {
        region.textContent = ''
      }
    }, 1000)
  }
}

export const toast = Object.assign(
  (...args: Parameters<typeof sonnerToast>) => sonnerToast(...args),
  {
    success: (...args: Parameters<typeof sonnerToast.success>) => {
      announce(args[0], 'Success')
      return sonnerToast.success(...args)
    },
    error: (...args: Parameters<typeof sonnerToast.error>) => {
      announce(args[0], 'Error')
      return sonnerToast.error(...args)
    },
    info: (...args: Parameters<typeof sonnerToast.info>) => {
      announce(args[0], 'Info')
      return sonnerToast.info(...args)
    },
    warning: (...args: Parameters<typeof sonnerToast.warning>) => {
      announce(args[0], 'Warning')
      return sonnerToast.warning(...args)
    },
    promise: sonnerToast.promise,
    loading: sonnerToast.loading,
    custom: sonnerToast.custom,
    message: sonnerToast.message,
    dismiss: sonnerToast.dismiss
  }
)

if (typeof window !== 'undefined') {
  (window as any).toast = toast
}
