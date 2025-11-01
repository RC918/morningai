/**
 * Animation utilities for Apple-level UI/UX
 * Based on MorningAI design system
 */

export interface SpringConfig {
  type: 'spring'
  stiffness: number
  damping: number
  mass: number
}

export interface HapticConfig {
  intensity: number
  duration: number
  pattern?: number[]
}

export type HapticType = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection'
export type SpringPresetType = 'gentle' | 'default' | 'bouncy' | 'snappy' | 'smooth' | 'wobbly'

/**
 * Check if user prefers reduced motion
 * @returns boolean
 */
export const prefersReducedMotion = (): boolean => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};

/**
 * Apple-style spring presets matching iOS animations
 */
export const springPresets: Record<string, SpringConfig> = {
  gentle: {
    type: 'spring',
    stiffness: 120,
    damping: 14,
    mass: 0.5
  },
  
  default: {
    type: 'spring',
    stiffness: 170,
    damping: 26,
    mass: 1
  },
  
  bouncy: {
    type: 'spring',
    stiffness: 260,
    damping: 20,
    mass: 0.8
  },
  
  snappy: {
    type: 'spring',
    stiffness: 300,
    damping: 30,
    mass: 0.6
  },
  
  smooth: {
    type: 'spring',
    stiffness: 100,
    damping: 20,
    mass: 1.2
  },
  
  wobbly: {
    type: 'spring',
    stiffness: 180,
    damping: 12,
    mass: 1
  }
};

/**
 * Get spring configuration based on preset name
 */
export const getSpringConfig = (preset: string = 'default'): SpringConfig | { duration: number } => {
  if (prefersReducedMotion()) {
    return { duration: 0 };
  }
  
  return springPresets[preset] || springPresets.default;
};

/**
 * Haptic feedback types matching iOS patterns
 */
export const hapticTypes: Record<string, HapticConfig> = {
  light: { intensity: 0.3, duration: 10 },
  medium: { intensity: 0.5, duration: 15 },
  heavy: { intensity: 0.7, duration: 20 },
  success: { intensity: 0.6, duration: 25, pattern: [10, 5, 10] },
  warning: { intensity: 0.7, duration: 30, pattern: [15, 10, 15] },
  error: { intensity: 0.8, duration: 35, pattern: [20, 10, 20, 10, 20] },
  selection: { intensity: 0.4, duration: 8 }
};

/**
 * Trigger haptic feedback (visual simulation)
 * Returns a promise that resolves when animation completes
 */
export const triggerHaptic = async (element: HTMLElement, type: string = 'light'): Promise<void> => {
  if (!element || prefersReducedMotion()) {
    return Promise.resolve();
  }
  
  const haptic = hapticTypes[type] || hapticTypes.light;
  
  element.classList.add(`haptic-${type}`);
  
  return new Promise<void>((resolve) => {
    setTimeout(() => {
      element.classList.remove(`haptic-${type}`);
      resolve();
    }, haptic.duration);
  });
};

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
