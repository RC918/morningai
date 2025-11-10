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
 * Check if a feature is enabled
 * 
 * For new Owner Console flags (OWNER_CONSOLE_*):
 * - Priority: URL params → localStorage → env vars → default (false)
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
    if (urlValue !== undefined) return urlValue;
    
    const localStorageValue = getLocalStorageFlag(key);
    if (localStorageValue !== undefined) return localStorageValue;
    
    const envValue = getEnvFlag(key);
    if (envValue !== undefined) return envValue;
    
    return false;
  }
  
  return legacyIsEnabled(key.toLowerCase());
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
