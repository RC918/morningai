/**
 * Performance optimization utilities
 * Week 6 - Performance Optimization
 */

interface PreloadResource {
  href: string
  as: string
  type?: string
}

interface ConnectionInfo {
  effectiveType: string
  downlink: number
  rtt: number
  saveData: boolean
}

interface LoadingStrategy {
  shouldLazyLoad: boolean
  shouldPreload: boolean
  shouldUseWebP: boolean
  shouldAnimate: boolean
  imageQuality: 'low' | 'high'
  maxConcurrentRequests: number
}

/**
 * Check if browser supports WebP format
 * @returns {boolean}
 */
export const supportsWebP = (() => {
  let supported: boolean | null = null
  
  return (): boolean => {
    if (supported !== null) return supported
    
    try {
      const canvas = document.createElement('canvas')
      if (canvas.getContext && canvas.getContext('2d')) {
        supported = canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0
      } else {
        supported = false
      }
    } catch (e) {
      supported = false
    }
    
    return supported
  }
})()

/**
 * Get optimized image URL with WebP support and fallback
 * @param {string} filename - Base filename without extension
 * @param {string} extension - Original extension (png, jpg, etc.)
 * @param {string} basePath - Base path for images (default: '/images')
 * @returns {string} - Optimized image URL
 */
export const getOptimizedImageUrl = (filename: string, extension: string = 'png', basePath: string = '/images'): string => {
  const useWebP = supportsWebP()
  const ext = useWebP ? 'webp' : extension
  return `${basePath}/${filename}.${ext}`
}

/**
 * Preload critical resources
 * @param {Array<{href: string, as: string, type?: string}>} resources
 */
export const preloadResources = (resources: PreloadResource[]): void => {
  resources.forEach(({ href, as, type }: PreloadResource) => {
    const link = document.createElement('link')
    link.rel = 'preload'
    link.href = href
    link.as = as
    if (type) link.type = type
    if (as === 'font') link.crossOrigin = 'anonymous'
    document.head.appendChild(link)
  })
}

/**
 * Prefetch resources for next navigation
 * @param {Array<string>} urls
 */
export const prefetchResources = (urls: string[]): void => {
  urls.forEach((url: string) => {
    const link = document.createElement('link')
    link.rel = 'prefetch'
    link.href = url
    document.head.appendChild(link)
  })
}

/**
 * Measure and report Web Vitals
 * @param {Function} onReport - Callback to handle metrics
 */
export const reportWebVitals = (onReport: (metric: any) => void): void => {
  if (typeof onReport !== 'function') return

  import('web-vitals').then(({ onCLS, onFCP, onLCP, onTTFB, onINP }) => {
    onCLS(onReport)
    onINP(onReport)
    onFCP(onReport)
    onLCP(onReport)
    onTTFB(onReport)
  }).catch((error) => {
    console.warn('Failed to load web-vitals:', error)
  })
}

/**
 * Debounce function for performance optimization
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in milliseconds
 * @returns {Function}
 */
export const debounce = <T extends (...args: any[]) => any>(func: T, wait: number = 300): ((...args: Parameters<T>) => void) => {
  let timeout: ReturnType<typeof setTimeout> | undefined
  return function executedFunction(...args: Parameters<T>) {
    const later = () => {
      clearTimeout(timeout)
      func(...args)
    }
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)
  }
}

/**
 * Throttle function for performance optimization
 * @param {Function} func - Function to throttle
 * @param {number} limit - Time limit in milliseconds
 * @returns {Function}
 */
export const throttle = <T extends (...args: any[]) => any>(func: T, limit: number = 300): ((...args: Parameters<T>) => void) => {
  let inThrottle: boolean | undefined
  return function executedFunction(...args: Parameters<T>) {
    if (!inThrottle) {
      func(...args)
      inThrottle = true
      setTimeout(() => (inThrottle = false), limit)
    }
  }
}

/**
 * Request Idle Callback wrapper with fallback
 * @param {Function} callback
 * @param {Object} options
 */
export const requestIdleCallback = (callback: IdleRequestCallback, options: IdleRequestOptions = {}): number => {
  if ('requestIdleCallback' in window) {
    return window.requestIdleCallback(callback, options)
  }
  return setTimeout(() => {
    callback({
      didTimeout: false,
      timeRemaining: () => 50,
    } as IdleDeadline)
  }, 1) as any
}

/**
 * Cancel Idle Callback wrapper with fallback
 * @param {number} id
 */
export const cancelIdleCallback = (id: number): void => {
  if ('cancelIdleCallback' in window) {
    return window.cancelIdleCallback(id)
  }
  return clearTimeout(id)
}

/**
 * Intersection Observer helper for lazy loading
 * @param {Function} callback
 * @param {Object} options
 * @returns {IntersectionObserver}
 */
export const createIntersectionObserver = (callback: IntersectionObserverCallback, options: IntersectionObserverInit = {}): IntersectionObserver => {
  const defaultOptions: IntersectionObserverInit = {
    root: null,
    rootMargin: '50px',
    threshold: 0.01,
  }

  return new IntersectionObserver(callback, { ...defaultOptions, ...options })
}

/**
 * Check if element is in viewport
 * @param {HTMLElement} element
 * @returns {boolean}
 */
export const isInViewport = (element: HTMLElement): boolean => {
  const rect = element.getBoundingClientRect()
  return (
    rect.top >= 0 &&
    rect.left >= 0 &&
    rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) &&
    rect.right <= (window.innerWidth || document.documentElement.clientWidth)
  )
}

/**
 * Get connection speed information
 * @returns {Object}
 */
export const getConnectionInfo = (): ConnectionInfo | null => {
  if ('connection' in navigator) {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection
    return {
      effectiveType: connection.effectiveType,
      downlink: connection.downlink,
      rtt: connection.rtt,
      saveData: connection.saveData,
    }
  }
  return null
}

/**
 * Check if user prefers reduced motion
 * @returns {boolean}
 */
export const prefersReducedMotion = (): boolean => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

/**
 * Get device memory information
 * @returns {number|null}
 */
export const getDeviceMemory = (): number | null => {
  return (navigator as any).deviceMemory || null
}

/**
 * Check if device is low-end
 * @returns {boolean}
 */
export const isLowEndDevice = (): boolean => {
  const memory = getDeviceMemory()
  const connection = getConnectionInfo()
  
  return (
    (memory !== null && memory <= 4) ||
    (connection !== null && ['slow-2g', '2g'].includes(connection.effectiveType)) ||
    (connection !== null && connection.saveData)
  )
}

/**
 * Adaptive loading strategy based on device capabilities
 * @returns {Object}
 */
export const getLoadingStrategy = (): LoadingStrategy => {
  const isLowEnd = isLowEndDevice()
  const reducedMotion = prefersReducedMotion()
  
  return {
    shouldLazyLoad: true, // Always lazy load
    shouldPreload: !isLowEnd, // Only preload on high-end devices
    shouldUseWebP: supportsWebP(), // Use WebP if supported
    shouldAnimate: !reducedMotion, // Respect motion preferences
    imageQuality: isLowEnd ? 'low' : 'high', // Adjust image quality
    maxConcurrentRequests: isLowEnd ? 2 : 6, // Limit concurrent requests
  }
}

export default {
  supportsWebP,
  getOptimizedImageUrl,
  preloadResources,
  prefetchResources,
  reportWebVitals,
  debounce,
  throttle,
  requestIdleCallback,
  cancelIdleCallback,
  createIntersectionObserver,
  isInViewport,
  getConnectionInfo,
  prefersReducedMotion,
  getDeviceMemory,
  isLowEndDevice,
  getLoadingStrategy,
}
