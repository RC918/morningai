/**
 * Motion Utilities - Issue #470
 * Provides motion governance with reduced-motion support and IntersectionObserver
 */
import React from 'react'

export const prefersReducedMotion = () => {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export const getAnimationVariants = (type = 'fade') => {
  if (prefersReducedMotion()) {
    return {
      initial: { opacity: 1 },
      animate: { opacity: 1 },
      exit: { opacity: 1 }
    }
  }

  const variants = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1 },
      exit: { opacity: 0 }
    },
    slideUp: {
      initial: { opacity: 0, y: 20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: -20 }
    },
    slideDown: {
      initial: { opacity: 0, y: -20 },
      animate: { opacity: 1, y: 0 },
      exit: { opacity: 0, y: 20 }
    },
    slideLeft: {
      initial: { opacity: 0, x: 20 },
      animate: { opacity: 1, x: 0 },
      exit: { opacity: 0, x: -20 }
    },
    slideRight: {
      initial: { opacity: 0, x: -20 },
      animate: { opacity: 1, x: 0 },
      exit: { opacity: 0, x: 20 }
    },
    scale: {
      initial: { opacity: 0, scale: 0.95 },
      animate: { opacity: 1, scale: 1 },
      exit: { opacity: 0, scale: 0.95 }
    }
  }

  return variants[type] || variants.fade
}

export const getTransition = (duration = 0.3, delay = 0) => {
  if (prefersReducedMotion()) {
    return { duration: 0 }
  }

  return {
    duration: Math.min(duration, 0.6), // Max 600ms per guidelines
    delay,
    ease: [0.4, 0, 0.2, 1] // Smooth easing
  }
}

export class AnimationObserver {
  constructor(options = {}) {
    this.options = {
      threshold: options.threshold || 0.1,
      rootMargin: options.rootMargin || '0px',
      triggerOnce: options.triggerOnce !== false
    }
    this.observer = null
    this.elements = new Map()
  }

  observe(element, callback) {
    if (!element || prefersReducedMotion()) {
      if (callback) callback(element, true)
      return
    }

    if (!this.observer) {
      this.observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
          const callback = this.elements.get(entry.target)
          if (callback && entry.isIntersecting) {
            callback(entry.target, true)
            if (this.options.triggerOnce) {
              this.unobserve(entry.target)
            }
          }
        })
      }, {
        threshold: this.options.threshold,
        rootMargin: this.options.rootMargin
      })
    }

    this.elements.set(element, callback)
    this.observer.observe(element)
  }

  unobserve(element) {
    if (this.observer && element) {
      this.observer.unobserve(element)
      this.elements.delete(element)
    }
  }

  disconnect() {
    if (this.observer) {
      this.observer.disconnect()
      this.elements.clear()
    }
  }
}

export const useScrollAnimation = (ref, options = {}) => {
  const [isVisible, setIsVisible] = React.useState(false)

  React.useEffect(() => {
    const element = ref.current
    if (!element) return

    const observer = new AnimationObserver(options)
    observer.observe(element, () => {
      setIsVisible(true)
    })

    return () => observer.disconnect()
  }, [ref, options])

  return isVisible
}

let activeAnimations = 0
const MAX_ANIMATIONS = 3

export const requestAnimation = () => {
  if (prefersReducedMotion()) return false
  if (activeAnimations >= MAX_ANIMATIONS) return false
  
  activeAnimations++
  return true
}

export const releaseAnimation = () => {
  activeAnimations = Math.max(0, activeAnimations - 1)
}

export const withMotionBudget = (Component) => {
  return (props) => {
    const canAnimate = requestAnimation()
    
    React.useEffect(() => {
      return () => releaseAnimation()
    }, [])

    if (!canAnimate) {
      return <Component {...props} animate={false} />
    }

    return <Component {...props} />
  }
}

export const getMotionClass = (animationClass) => {
  if (prefersReducedMotion()) {
    return ''
  }
  return animationClass
}

export default {
  prefersReducedMotion,
  getAnimationVariants,
  getTransition,
  AnimationObserver,
  useScrollAnimation,
  requestAnimation,
  releaseAnimation,
  withMotionBudget,
  getMotionClass
}
