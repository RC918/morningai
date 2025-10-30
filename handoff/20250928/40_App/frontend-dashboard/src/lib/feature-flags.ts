/**
 * Feature Flags Configuration
 * 
 * This module provides a centralized feature flag system to enable safe parallel development
 * across Platform, MVP, and Owner Console squads.
 * 
 * Usage:
 * ```typescript
 * import { isFeatureEnabled, FEATURE_FLAGS } from '@/lib/feature-flags';
 * 
 * if (isFeatureEnabled('MVP_AGENT_REGISTRY')) {
 *   // New MVP feature code
 * }
 * ```
 * 
 * @see docs/PARALLEL_DEVELOPMENT_STRATEGY.md
 */

export type FeatureFlagKey = keyof typeof FEATURE_FLAGS;

/**
 * Feature Flags Registry
 * 
 * All new features should be added here with default value `false`.
 * Features can be enabled via:
 * 1. Environment variables (VITE_FEATURE_*)
 * 2. localStorage (for local development)
 * 3. URL query parameters (for testing)
 */
export const FEATURE_FLAGS = {
  
  /**
   * Agent Registry & Task Router (Issue #760)
   * Enables the new agent registry system with typed clients
   */
  MVP_AGENT_REGISTRY: false,
  
  /**
   * Closed-loop Scenarios (Issue #761)
   * Enables FAQ → PR → CI → Deploy closed-loop automation
   */
  MVP_CLOSED_LOOP: false,
  
  /**
   * Metrics & Dashboard (Issue #762)
   * Enables the new metrics collection and visualization dashboard
   */
  MVP_METRICS_DASHBOARD: false,
  
  /**
   * Monitoring Foundation (Issue #768)
   * Enables the monitoring infrastructure and metrics schema
   */
  MVP_MONITORING_FOUNDATION: false,
  
  
  /**
   * API Connection (Issue #767)
   * Enables Owner Console API connection with JWT + Refresh Token
   */
  OWNER_CONSOLE_API: false,
  
  /**
   * Agent Governance Dashboard (Issue #769)
   * Enables agent reputation, permissions, and compliance monitoring
   */
  OWNER_CONSOLE_GOVERNANCE: false,
  
  /**
   * Tenant Management (Issue #770)
   * Enables tenant account, permissions, and quota management
   */
  OWNER_CONSOLE_TENANTS: false,
  
  /**
   * System Monitoring (Issue #771)
   * Enables system health, performance metrics, and alerting
   */
  OWNER_CONSOLE_MONITORING: false,
  
  /**
   * Platform Settings (Issue #772)
   * Enables platform-level configuration and security policies
   */
  OWNER_CONSOLE_SETTINGS: false,
  
  /**
   * Security & Audit (Issue #773)
   * Enables security audit logs and compliance reporting
   */
  OWNER_CONSOLE_SECURITY: false,
  
  /**
   * PWA Implementation (Issue #774)
   * Enables Progressive Web App features (Service Worker, Push Notifications)
   */
  OWNER_CONSOLE_PWA: false,
  
  
  /**
   * Storybook Type Safety (Issue #851)
   * Enables type-safe Storybook stories with proper TypeScript integration
   */
  PLATFORM_STORYBOOK_TYPES: false,
  
  /**
   * Strict Mode (Issue #935) - DELAYED
   * Enables TypeScript strict mode (delayed until MVP/Owner Console skeleton complete)
   */
  PLATFORM_STRICT_MODE: false,
  
  /**
   * Spring Animation Types (Issue #936) - DELAYED
   * Enables stricter typing for spring-animation library
   */
  PLATFORM_SPRING_ANIMATION_TYPES: false,
  
  
  /**
   * Legacy Navigation Features (Backward Compatibility)
   * These are existing features that should remain enabled by default
   */
  DASHBOARD: true,
  STRATEGIES: true,
  APPROVALS: true,
  HISTORY: true,
  COSTS: true,
  GOVERNANCE: true,
  SETTINGS: true,
  CHECKOUT: true,
} as const;

/**
 * Feature Flag Sources (priority order)
 */
enum FeatureFlagSource {
  URL_PARAM = 'url_param',
  LOCAL_STORAGE = 'local_storage',
  ENV_VAR = 'env_var',
  DEFAULT = 'default',
}

/**
 * Available Features (for backward compatibility with existing code)
 * Maps feature names to feature flag keys
 */
export const AVAILABLE_FEATURES = {
  DASHBOARD: 'DASHBOARD',
  STRATEGIES: 'STRATEGIES',
  APPROVALS: 'APPROVALS',
  HISTORY: 'HISTORY',
  COSTS: 'COSTS',
  GOVERNANCE: 'GOVERNANCE',
  SETTINGS: 'SETTINGS',
  CHECKOUT: 'CHECKOUT',
} as const;

/**
 * Get feature flag value from environment variables
 */
function getEnvFlag(key: FeatureFlagKey | string): boolean | undefined {
  const envKey = `VITE_FEATURE_${key}`;
  const envValue = (import.meta.env as any)[envKey] as string | undefined;
  
  if (envValue === undefined) return undefined;
  
  return envValue === 'true' || envValue === '1';
}

/**
 * Get feature flag value from localStorage
 */
function getLocalStorageFlag(key: FeatureFlagKey | string): boolean | undefined {
  if (typeof window === 'undefined') return undefined;
  
  try {
    const storageKey = `feature_flag_${key}`;
    const value = localStorage.getItem(storageKey);
    
    if (value === null) return undefined;
    
    return value === 'true' || value === '1';
  } catch {
    return undefined;
  }
}

/**
 * Get feature flag value from URL query parameters
 */
function getUrlParamFlag(key: FeatureFlagKey | string): boolean | undefined {
  if (typeof window === 'undefined') return undefined;
  
  try {
    const params = new URLSearchParams(window.location.search);
    const paramKey = `feature_${key}`;
    const value = params.get(paramKey);
    
    if (value === null) return undefined;
    
    return value === 'true' || value === '1';
  } catch {
    return undefined;
  }
}

/**
 * Check if a feature is enabled
 * 
 * Priority order:
 * 1. URL query parameter (?feature_MVP_AGENT_REGISTRY=true)
 * 2. localStorage (feature_flag_MVP_AGENT_REGISTRY=true)
 * 3. Environment variable (VITE_FEATURE_MVP_AGENT_REGISTRY=true)
 * 4. Default value from FEATURE_FLAGS (or true for legacy feature names)
 * 
 * @param key - Feature flag key (can be FeatureFlagKey or legacy feature name)
 * @returns true if feature is enabled, false otherwise
 */
export function isFeatureEnabled(key: FeatureFlagKey | string): boolean {
  const urlValue = getUrlParamFlag(key);
  if (urlValue !== undefined) return urlValue;
  
  const localStorageValue = getLocalStorageFlag(key);
  if (localStorageValue !== undefined) return localStorageValue;
  
  const envValue = getEnvFlag(key);
  if (envValue !== undefined) return envValue;
  
  if (key in FEATURE_FLAGS) {
    return FEATURE_FLAGS[key as FeatureFlagKey];
  }
  
  if (typeof console !== 'undefined' && console.warn) {
    console.warn(`[Feature Flags] Unknown feature flag key: "${key}". Defaulting to false. Did you misspell it?`);
  }
  
  return false;
}

/**
 * Get the source of a feature flag value
 * Useful for debugging and understanding why a feature is enabled/disabled
 */
export function getFeatureFlagSource(key: FeatureFlagKey | string): FeatureFlagSource {
  if (getUrlParamFlag(key) !== undefined) return FeatureFlagSource.URL_PARAM;
  if (getLocalStorageFlag(key) !== undefined) return FeatureFlagSource.LOCAL_STORAGE;
  if (getEnvFlag(key) !== undefined) return FeatureFlagSource.ENV_VAR;
  return FeatureFlagSource.DEFAULT;
}

/**
 * Set a feature flag in localStorage (for local development)
 * 
 * @param key - Feature flag key
 * @param enabled - Whether to enable or disable the feature
 */
export function setFeatureFlag(key: FeatureFlagKey | string, enabled: boolean): void {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = `feature_flag_${key}`;
    localStorage.setItem(storageKey, enabled ? 'true' : 'false');
  } catch (error) {
    console.error(`Failed to set feature flag ${key}:`, error);
  }
}

/**
 * Clear a feature flag from localStorage
 */
export function clearFeatureFlag(key: FeatureFlagKey | string): void {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = `feature_flag_${key}`;
    localStorage.removeItem(storageKey);
  } catch (error) {
    console.error(`Failed to clear feature flag ${key}:`, error);
  }
}

/**
 * Get all feature flags with their current values and sources
 * Useful for debugging and feature flag dashboard
 */
export function getAllFeatureFlags(): Array<{
  key: FeatureFlagKey;
  enabled: boolean;
  source: FeatureFlagSource;
}> {
  return Object.keys(FEATURE_FLAGS).map((key) => ({
    key: key as FeatureFlagKey,
    enabled: isFeatureEnabled(key as FeatureFlagKey),
    source: getFeatureFlagSource(key as FeatureFlagKey),
  }));
}

/**
 * Feature Flag Debug Panel (for development)
 * 
 * Usage in DevTools console:
 * ```javascript
 * window.__FEATURE_FLAGS__.list()
 * window.__FEATURE_FLAGS__.enable('MVP_AGENT_REGISTRY')
 * window.__FEATURE_FLAGS__.disable('MVP_AGENT_REGISTRY')
 * ```
 */
if (typeof window !== 'undefined' && import.meta.env.DEV) {
  (window as any).__FEATURE_FLAGS__ = {
    list: () => {
      console.table(getAllFeatureFlags());
    },
    enable: (key: FeatureFlagKey) => {
      setFeatureFlag(key, true);
      console.log(`✅ Enabled feature: ${key}`);
    },
    disable: (key: FeatureFlagKey) => {
      setFeatureFlag(key, false);
      console.log(`❌ Disabled feature: ${key}`);
    },
    clear: (key: FeatureFlagKey) => {
      clearFeatureFlag(key);
      console.log(`🗑️  Cleared feature: ${key}`);
    },
  };
  
  console.log('🚩 Feature Flags Debug Panel available: window.__FEATURE_FLAGS__');
}
