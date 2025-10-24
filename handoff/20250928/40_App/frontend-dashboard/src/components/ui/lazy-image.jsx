import * as React from "react"
import { cn } from "@/lib/utils"

/**
 * LazyImage component with Intersection Observer for lazy loading
 * Includes loading placeholder and WebP support with fallback
 */
const LazyImage = React.forwardRef(({
  src,
  alt,
  className,
  placeholderClassName,
  onLoad,
  onError,
  ...props
}, ref) => {
  const [isLoaded, setIsLoaded] = React.useState(false)
  const [isInView, setIsInView] = React.useState(false)
  const [hasError, setHasError] = React.useState(false)
  const imgRef = React.useRef(null)
  const observerRef = React.useRef(null)

  React.useImperativeHandle(ref, () => imgRef.current)

  React.useEffect(() => {
    if (!('IntersectionObserver' in window)) {
      setIsInView(true)
      return
    }

    observerRef.current = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsInView(true)
          observerRef.current?.disconnect()
        }
      },
      {
        rootMargin: '50px', // Start loading 50px before entering viewport
        threshold: 0.01
      }
    )

    if (imgRef.current) {
      observerRef.current.observe(imgRef.current)
    }

    return () => {
      observerRef.current?.disconnect()
    }
  }, [])

  const handleLoad = (e) => {
    setIsLoaded(true)
    onLoad?.(e)
  }

  const handleError = (e) => {
    setHasError(true)
    onError?.(e)
  }

  return (
    <div
      ref={imgRef}
      className={cn("relative overflow-hidden", className)}
      {...props}
    >
      {/* Loading placeholder */}
      {!isLoaded && !hasError && (
        <div
          className={cn(
            "absolute inset-0 bg-muted animate-pulse",
            placeholderClassName
          )}
          aria-hidden="true"
        />
      )}

      {/* Error state */}
      {hasError && (
        <div
          className={cn(
            "absolute inset-0 flex items-center justify-center bg-muted text-muted-foreground",
            placeholderClassName
          )}
          role="img"
          aria-label={alt || "Image failed to load"}
        >
          <svg
            className="w-8 h-8"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
            />
          </svg>
        </div>
      )}

      {/* Actual image - only load when in view */}
      {isInView && (
        <img
          src={src}
          alt={alt}
          loading="lazy"
          decoding="async"
          onLoad={handleLoad}
          onError={handleError}
          className={cn(
            "transition-opacity duration-300",
            isLoaded ? "opacity-100" : "opacity-0",
            className
          )}
        />
      )}
    </div>
  )
})

LazyImage.displayName = "LazyImage"

/**
 * Get image URL with WebP support and fallback
 * @param {string} filename - Base filename without extension
 * @param {string} extension - Original extension (png, jpg, etc.)
 * @returns {string} - Image URL with WebP if supported
 */
const getOptimizedImageUrl = (filename, extension = 'png') => {
  const supportsWebP = (() => {
    const canvas = document.createElement('canvas')
    if (canvas.getContext && canvas.getContext('2d')) {
      return canvas.toDataURL('image/webp').indexOf('data:image/webp') === 0
    }
    return false
  })()

  return supportsWebP
    ? `/images/${filename}.webp`
    : `/images/${filename}.${extension}`
}

/**
 * Picture component with multiple sources for responsive images
 */
const ResponsiveImage = React.forwardRef(({
  src,
  alt,
  sources = [],
  className,
  ...props
}, ref) => {
  const [isLoaded, setIsLoaded] = React.useState(false)

  return (
    <picture className={cn("block", className)}>
      {sources.map((source, index) => (
        <source
          key={index}
          srcSet={source.srcSet}
          media={source.media}
          type={source.type}
        />
      ))}
      <img
        ref={ref}
        src={src}
        alt={alt}
        loading="lazy"
        decoding="async"
        onLoad={() => setIsLoaded(true)}
        className={cn(
          "transition-opacity duration-300",
          isLoaded ? "opacity-100" : "opacity-0"
        )}
        {...props}
      />
    </picture>
  )
})

ResponsiveImage.displayName = "ResponsiveImage"

export { LazyImage, ResponsiveImage, getOptimizedImageUrl }
