/**
 * Spring Animation System - Type Definitions
 */

export type HapticType = 'light' | 'medium' | 'heavy' | 'success' | 'warning' | 'error' | 'selection';

export interface SpringPreset {
  type: string;
  stiffness: number;
  damping: number;
  mass: number;
  duration: number;
}

export interface HapticConfig {
  intensity: number;
  duration: number;
  pattern?: number[];
}

export const springPresets: {
  gentle: SpringPreset;
  default: SpringPreset;
  bouncy: SpringPreset;
  snappy: SpringPreset;
  smooth: SpringPreset;
  wobbly: SpringPreset;
};

export const hapticTypes: {
  [K in HapticType]: HapticConfig;
};

export function getSpringConfig(preset?: string): SpringPreset | { duration: number };

export interface AnimationVariants {
  initial?: Record<string, unknown>;
  animate?: Record<string, unknown>;
  exit?: Record<string, unknown>;
}

export function getSpringVariants(type?: string, preset?: string): AnimationVariants;

export function getHapticAnimation(type?: HapticType): Record<string, unknown>;

export function triggerHaptic(element: HTMLElement, type?: HapticType): Promise<void>;

export function getContextualAnimation(baseAnimation: string, context?: {
  isMobile?: boolean;
  isLowPower?: boolean;
  connectionSpeed?: string;
  userPreference?: string;
}): AnimationVariants;

export function getUserContext(): {
  isMobile: boolean;
  isLowPower: boolean;
  connectionSpeed: string;
  userPreference: string;
};

export interface AnimationStep {
  duration?: number;
  [key: string]: unknown;
}

export function createAnimationSequence(steps: AnimationStep[], preset?: string): Record<string, unknown>;

export function getStaggerConfig(preset?: string, staggerDelay?: number): Record<string, unknown>;

export function trackAnimation(animationId: string): () => void;

export function getAnimationMetrics(): {
  totalAnimations: number;
  activeAnimations: number;
  droppedFrames: number;
  averageFPS: number;
};

export function resetAnimationMetrics(): void;

declare const _default: {
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

export default _default;
