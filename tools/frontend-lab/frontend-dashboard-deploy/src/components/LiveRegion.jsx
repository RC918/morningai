import { useEffect, useRef } from 'react'

export const LiveRegion = ({ 
  message, 
  politeness = 'polite',
  clearAfter = 5000,
  className = ''
}) => {
  const regionRef = useRef(null)

  useEffect(() => {
    if (message && clearAfter > 0) {
      const timer = setTimeout(() => {
        if (regionRef.current) {
          regionRef.current.textContent = ''
        }
      }, clearAfter)
      return () => clearTimeout(timer)
    }
  }, [message, clearAfter])

  return (
    <div
      ref={regionRef}
      role={politeness === 'assertive' ? 'alert' : 'status'}
      aria-live={politeness}
      aria-atomic="true"
      className={`sr-only ${className}`}
    >
      {message}
    </div>
  )
}

export default LiveRegion
