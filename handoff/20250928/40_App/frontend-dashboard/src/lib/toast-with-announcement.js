import { toast as sonnerToast } from 'sonner'

let liveRegion = null

const ensureLiveRegion = () => {
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

const announce = (message, type) => {
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
  (...args) => sonnerToast(...args),
  {
    success: (...args) => {
      announce(args[0], 'Success')
      return sonnerToast.success(...args)
    },
    error: (...args) => {
      announce(args[0], 'Error')
      return sonnerToast.error(...args)
    },
    info: (...args) => {
      announce(args[0], 'Info')
      return sonnerToast.info(...args)
    },
    warning: (...args) => {
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
  window.toast = toast
}
