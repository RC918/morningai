/**
 * Spring Animation System - Apple-Level UI/UX
 * Implements iOS-style spring-based animations with haptic feedback simulation
 * 
 * Based on Apple Human Interface Guidelines and iOS 26.1 design patterns
 */

export interface SpringConfig {
  type: 'spring'
  stiffness: number
  damping: number
  mass: number
}

export interface AnimationVariant {
  initial: Record<string, any>
  animate: Record<string, any>
  exit?: Record<string, any>
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
 */
const prefersReducedMotion = (): boolean => {
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

export default {
  springPresets,
  getSpringConfig,
  hapticTypes,
  triggerHaptic
};
