/**
 * Feature Flags Wrapper for Owner Console
 * 
 * This wrapper bridges the new TypeScript feature flags system with the legacy
 * feature-flags.js implementation. It provides multi-source priority resolution
 * for new Owner Console flags while delegating legacy features to the old system.
 * 
 * New Owner Console flags (OWNER_CONSOLE_*):
 * - Priority: URL params → localStorage → env vars → default (false)
 * 
 * Legacy features (dashboard, checkout, etc.):
 * - Delegated to feature-flags.js (comma-separated VITE_FEATURES env var)
 */

import { 
  isFeatureEnabled as legacyIsEnabled, 
  AVAILABLE_FEATURES as LEGACY_AVAILABLE 
} from './feature-flags.js';

export const AVAILABLE_FEATURES = LEGACY_AVAILABLE;

/**
 * New Owner Console feature flags
 */
const OWNER_CONSOLE_FLAGS = [
  'OWNER_CONSOLE_API',
  'OWNER_CONSOLE_GOVERNANCE',
  'OWNER_CONSOLE_TENANTS',
  'OWNER_CONSOLE_MONITORING',
  'OWNER_CONSOLE_SETTINGS',
  'OWNER_CONSOLE_SECURITY',
  'OWNER_CONSOLE_PWA',
] as const;

type OwnerConsoleFlag = typeof OWNER_CONSOLE_FLAGS[number];

/**
 * Check if a key is a new Owner Console flag
 */
function isOwnerConsoleFlag(key: string): key is OwnerConsoleFlag {
  return OWNER_CONSOLE_FLAGS.includes(key as OwnerConsoleFlag);
}

/**
 * Get feature flag value from URL query parameters
 */
function getUrlParamFlag(key: string): boolean | undefined {
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
 * Get feature flag value from localStorage
 */
function getLocalStorageFlag(key: string): boolean | undefined {
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
 * Get feature flag value from environment variables
 */
function getEnvFlag(key: string): boolean | undefined {
  const envKey = `VITE_FEATURE_${key}`;
  const envValue = (import.meta.env as any)[envKey] as string | undefined;
  
  if (envValue === undefined) return undefined;
  
  return envValue === 'true' || envValue === '1';
}

/**
 * Get default value for a feature flag
 * 
 * For OWNER_CONSOLE_API: defaults to true in production builds to prevent
 * accidentally shipping mock authentication to production/staging.
 * 
 * For other flags: defaults to false
 */
function getDefaultValue(key: string): boolean {
  if (key === 'OWNER_CONSOLE_API' && import.meta.env.PROD) {
    return true;
  }
  
  return false;
}

/**
 * Check if a feature is enabled
 * 
 * For new Owner Console flags (OWNER_CONSOLE_*):
 * - Priority: URL params → localStorage → env vars → default (production-aware)
 * - OWNER_CONSOLE_API defaults to true in production builds
 * 
 * For legacy features:
 * - Delegates to feature-flags.js (comma-separated VITE_FEATURES)
 * 
 * @param key - Feature flag key
 * @returns true if feature is enabled, false otherwise
 */
export function isFeatureEnabled(key: string): boolean {
  if (isOwnerConsoleFlag(key)) {
    if (import.meta.env.PROD && key === 'OWNER_CONSOLE_API') {
      const envValue = getEnvFlag(key);
      if (envValue !== undefined) return envValue;
      return true;
    }
    
    const urlValue = getUrlParamFlag(key);
    if (urlValue !== undefined) {
      logFeatureFlagResolution(key, 'url', urlValue);
      return urlValue;
    }
    
    const localStorageValue = getLocalStorageFlag(key);
    if (localStorageValue !== undefined) {
      logFeatureFlagResolution(key, 'localStorage', localStorageValue);
      return localStorageValue;
    }
    
    const envValue = getEnvFlag(key);
    if (envValue !== undefined) {
      logFeatureFlagResolution(key, 'env', envValue);
      return envValue;
    }
    
    const defaultValue = getDefaultValue(key);
    logFeatureFlagResolution(key, 'default', defaultValue);
    
    if (key === 'OWNER_CONSOLE_API' && !defaultValue && import.meta.env.PROD) {
      console.warn(
        '[Feature Flags] OWNER_CONSOLE_API is disabled in production build. ' +
        'This will use mock authentication instead of real backend. ' +
        'Set VITE_FEATURE_OWNER_CONSOLE_API=true in environment variables.'
      );
    }
    
    return defaultValue;
  }
  
  return legacyIsEnabled(key.toLowerCase());
}

/**
 * Log feature flag resolution for diagnostics
 * Only logs in development or when explicitly enabled
 */
function logFeatureFlagResolution(key: string, source: string, value: boolean): void {
  if (import.meta.env.DEV || (typeof window !== 'undefined' && localStorage.getItem('debug_feature_flags') === 'true')) {
    console.info(`[Feature Flags] ${key} resolved from ${source}: ${value}`);
  }
}

/**
 * Set a feature flag in localStorage (for local development)
 */
export function setFeatureFlag(key: string, enabled: boolean): void {
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
export function clearFeatureFlag(key: string): void {
  if (typeof window === 'undefined') return;
  
  try {
    const storageKey = `feature_flag_${key}`;
    localStorage.removeItem(storageKey);
  } catch (error) {
    console.error(`Failed to clear feature flag ${key}:`, error);
  }
}
