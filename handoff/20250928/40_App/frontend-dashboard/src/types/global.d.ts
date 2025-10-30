/**
 * Global Type Definitions
 * Extends global interfaces and types used across the application
 */

import type { AccessibilityPerformanceMonitor } from '../lib/performance-monitor';

declare global {
  interface Window {
    /**
     * Vite API base URL injected at build time
     */
    __VITE_API_BASE_URL__?: string;
    
    /**
     * Accessibility performance monitor for debugging
     * Available in development mode only
     */
    __a11yPerformance?: AccessibilityPerformanceMonitor;
  }
}

export {};
