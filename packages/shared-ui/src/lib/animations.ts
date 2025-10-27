/**
 * Animation utilities for Apple-level UI/UX
 * Based on MorningAI design system
 */

/**
 * Get transition configuration with animation budget management
 * @param duration - Duration in seconds (max 0.6s)
 * @param delay - Delay in seconds
 * @returns Framer Motion transition config
 */
export const getTransition = (duration = 0.3, delay = 0) => {
  return {
    duration: Math.min(duration, 0.6), // Max 600ms per animation budget
    delay,
    ease: [0.4, 0, 0.2, 1], // Standard easing
  }
}

/**
 * Spring-based transition for Apple-like animations
 * @param stiffness - Spring stiffness (default: 300)
 * @param damping - Spring damping (default: 30)
 * @returns Framer Motion spring transition
 */
export const getSpringTransition = (stiffness = 300, damping = 30) => {
  return {
    type: "spring",
    stiffness,
    damping,
  }
}

/**
 * Fade in animation variants
 */
export const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: getTransition(0.3),
  },
}

/**
 * Slide up animation variants
 */
export const slideUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: getTransition(0.4),
  },
}

/**
 * Scale animation variants
 */
export const scale = {
  hidden: { opacity: 0, scale: 0.95 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: getTransition(0.3),
  },
}

/**
 * Stagger children animation
 * @param staggerDelay - Delay between children (default: 0.1s)
 */
export const staggerContainer = (staggerDelay = 0.1) => ({
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: staggerDelay,
      delayChildren: 0.2,
    },
  },
})

/**
 * Check if user prefers reduced motion
 * @returns boolean
 */
export const prefersReducedMotion = () => {
  if (typeof window === "undefined") return false
  return window.matchMedia("(prefers-reduced-motion: reduce)").matches
}

/**
 * Get animation variants with reduced motion support
 * @param variants - Animation variants
 * @returns Variants or empty object if reduced motion is preferred
 */
export const withReducedMotion = (variants: any) => {
  return prefersReducedMotion() ? {} : variants
}

/**
 * Hover scale animation
 */
export const hoverScale = {
  scale: 1.05,
  transition: getSpringTransition(400, 25),
}

/**
 * Tap scale animation
 */
export const tapScale = {
  scale: 0.95,
  transition: getSpringTransition(400, 25),
}

/**
 * Button press animation (Apple-style)
 */
export const buttonPress = {
  whileHover: hoverScale,
  whileTap: tapScale,
}
