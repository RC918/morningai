import { useEffect, useRef } from 'react'

/**
 * LiveRegion component for announcing dynamic content changes to screen readers
 * Follows WCAG 2.1 AA guidelines for accessible notifications
 * 
 * @param {Object} props
 * @param {string} props.message - The message to announce
 * @param {'polite'|'assertive'|'off'} props.type - The politeness level
 * @param {boolean} props.atomic - Whether to read the entire region or just changes
 * @param {boolean} props.relevant - What changes are relevant (additions, removals, text, all)
 * @param {boolean} props.clearOnUnmount - Whether to clear the message when component unmounts
 */
export const LiveRegion = ({ 
  message, 
  type = 'polite',
  atomic = true,
  relevant = 'additions text',
  clearOnUnmount = false
}) => {
  const regionRef = useRef(null)
  
  useEffect(() => {
    return () => {
      if (clearOnUnmount && regionRef.current) {
        regionRef.current.textContent = ''
      }
    }
  }, [clearOnUnmount])
  
  if (!message || type === 'off') {
    return null
  }
  
  const role = type === 'assertive' ? 'alert' : 'status'
  
  return (
    <div
      ref={regionRef}
      role={role}
      aria-live={type}
      aria-atomic={atomic}
      aria-relevant={relevant}
      className="sr-only"
    >
      {message}
    </div>
  )
}

/**
 * Hook for managing live region announcements
 * Provides a simple API for announcing messages to screen readers
 * 
 * @returns {Object} { announce, announcePolite, announceAssertive }
 */
export const useLiveRegion = () => {
  const regionRef = useRef(null)
  
  const announce = (message, type = 'polite') => {
    if (!regionRef.current) {
      const region = document.createElement('div')
      region.setAttribute('role', type === 'assertive' ? 'alert' : 'status')
      region.setAttribute('aria-live', type)
      region.setAttribute('aria-atomic', 'true')
      region.className = 'sr-only'
      document.body.appendChild(region)
      regionRef.current = region
    }
    
    regionRef.current.textContent = message
    
    setTimeout(() => {
      if (regionRef.current) {
        regionRef.current.textContent = ''
      }
    }, 1000)
  }
  
  const announcePolite = (message) => announce(message, 'polite')
  const announceAssertive = (message) => announce(message, 'assertive')
  
  return {
    announce,
    announcePolite,
    announceAssertive
  }
}

export default LiveRegion
