/**
 * Spring Animation System - Type Definitions
 * 
 * Type definitions for the spring-animation library that align with Framer Motion types.
 * This ensures type compatibility when using spring animations with Framer Motion components.
 */

import type { Variants, Transition, TargetAndTransition } from 'framer-motion';

/**
 * Haptic feedback types matching iOS patterns
 */
export type HapticType = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection';

/**
 * Spring preset names
 */
export type SpringPresetName = 'gentle' | 'default' | 'bouncy' | 'snappy' | 'smooth' | 'wobbly';

/**
 * Animation variant types
 */
export type AnimationVariantType = 
  | 'fade' 
  | 'scale' 
  | 'pop' 
  | 'bounce' 
  | 'slideUp' 
  | 'slideDown' 
  | 'slideLeft' 
  | 'slideRight' 
  | 'expand' 
  | 'rotate' 
  | 'shake' 
  | 'pulse';

/**
 * User context for contextual animations
 */
export interface UserContext {
  isMobile?: boolean;
  isLowPower?: boolean;
  connectionSpeed?: 'slow' | 'medium' | 'fast';
  userPreference?: 'default' | 'playful' | 'minimal';
}

/**
 * Animation sequence step
 */
export interface AnimationStep {
  duration?: number;
  [key: string]: unknown;
}

/**
 * Animation performance metrics
 */
export interface AnimationMetrics {
  totalAnimations: number;
  activeAnimations: number;
  droppedFrames: number;
  averageFPS: number;
}

/**
 * Haptic configuration
 */
export interface HapticConfig {
  intensity: number;
  duration: number;
  pattern?: number[];
}

/**
 * Spring presets object
 */
export const springPresets: Record<SpringPresetName, Transition>;

/**
 * Haptic types object
 */
export const hapticTypes: Record<HapticType, HapticConfig>;

/**
 * Get spring configuration based on preset name
 * Returns Framer Motion Transition type
 */
export function getSpringConfig(preset?: SpringPresetName | string): Transition;

/**
 * Get spring-based animation variants for Framer Motion
 * Returns Framer Motion Variants type
 */
export function getSpringVariants(type?: AnimationVariantType | string, preset?: SpringPresetName | string): Variants;

/**
 * Get haptic animation properties
 * Returns Framer Motion TargetAndTransition type
 */
export function getHapticAnimation(type?: HapticType | string): TargetAndTransition;

/**
 * Trigger haptic feedback (visual simulation)
 * Returns a promise that resolves when animation completes
 */
export function triggerHaptic(element: HTMLElement | null, type?: HapticType | string): Promise<void>;

/**
 * Get animation based on context (screen size, user preferences, etc.)
 */
export function getContextualAnimation(baseAnimation: AnimationVariantType | string, context?: UserContext): Variants;

/**
 * Detect user context
 */
export function getUserContext(): UserContext;

/**
 * Create a sequence of spring animations
 */
export function createAnimationSequence(steps: AnimationStep[], preset?: SpringPresetName | string): Transition;

/**
 * Get stagger configuration for children animations
 */
export function getStaggerConfig(preset?: SpringPresetName | string, staggerDelay?: number): {
  staggerChildren: number;
  delayChildren: number;
  transition: Transition;
};

/**
 * Track animation performance
 * Returns a cleanup function to prevent memory leaks
 */
export function trackAnimation(animationId: string): () => void;

/**
 * Get animation performance metrics
 */
export function getAnimationMetrics(): AnimationMetrics;

/**
 * Reset animation metrics
 */
export function resetAnimationMetrics(): void;

/**
 * Default export with all functions
 */
declare const springAnimation: {
  springPresets: typeof springPresets;
  getSpringConfig: typeof getSpringConfig;
  getSpringVariants: typeof getSpringVariants;
  hapticTypes: typeof hapticTypes;
  getHapticAnimation: typeof getHapticAnimation;
  triggerHaptic: typeof triggerHaptic;
  getContextualAnimation: typeof getContextualAnimation;
  getUserContext: typeof getUserContext;
  createAnimationSequence: typeof createAnimationSequence;
  getStaggerConfig: typeof getStaggerConfig;
  trackAnimation: typeof trackAnimation;
  getAnimationMetrics: typeof getAnimationMetrics;
  resetAnimationMetrics: typeof resetAnimationMetrics;
};

export default springAnimation;
