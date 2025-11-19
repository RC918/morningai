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
} from './feature-flags.legacy.js';

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
 * Supports case-insensitive boolean parsing for common formats
 */
function getEnvFlag(key: string): boolean | undefined {
  const envKey = `VITE_FEATURE_${key}`;
  const envValue = (import.meta.env as any)[envKey] as string | undefined;
  
  if (envValue === undefined) return undefined;
  
  const normalizedValue = envValue.toLowerCase().trim();
  
  if (['true', '1', 'yes', 'on'].includes(normalizedValue)) {
    return true;
  }
  
  if (['false', '0', 'no', 'off'].includes(normalizedValue)) {
    return false;
  }
  
  console.warn(`[Feature Flags] Invalid value for ${envKey}: "${envValue}". Expected true/false.`);
  return undefined;
}

/**
 * Get default value for a feature flag
 * 
 * For OWNER_CONSOLE_API: defaults to true in production builds to prevent
 * accidentally shipping mock authentication to production/staging.
 * 
 * For other flags: defaults to false
 */
function getDefaultValue(key: string, isProd: boolean): boolean {
  if (key === 'OWNER_CONSOLE_API' && isProd) {
    return true;
  }
  
  return false;
}

/**
 * Feature flag source values
 */
export interface FeatureFlagSources {
  url?: boolean;
  localStorage?: boolean;
  env?: boolean;
}

/**
 * Resolve feature flag value based on sources and production mode
 * 
 * This is a pure function that can be tested without relying on import.meta.env
 * 
 * @param key - Feature flag key
 * @param isProd - Whether running in production mode
 * @param sources - Feature flag values from different sources
 * @returns Resolved feature flag value
 */
export function resolveFeatureFlag(
  key: string,
  isProd: boolean,
  sources: FeatureFlagSources
): boolean {
  // Production lock for OWNER_CONSOLE_API: ignore URL/localStorage
  if (isProd && key === 'OWNER_CONSOLE_API') {
    return sources.env ?? true;
  }
  
  return sources.url ?? sources.localStorage ?? sources.env ?? getDefaultValue(key, isProd);
}

/**
 * Check if a feature is enabled
 * 
 * For new Owner Console flags (OWNER_CONSOLE_*):
 * - Production mode (OWNER_CONSOLE_API): env var → default (true)
 * - Development mode: URL params → localStorage → env vars → default (false)
 * 
 * For legacy features:
 * - Delegates to feature-flags.js (comma-separated VITE_FEATURES)
 * 
 * @param key - Feature flag key
 * @returns true if feature is enabled, false otherwise
 */
export function isFeatureEnabled(key: string): boolean {
  if (isOwnerConsoleFlag(key)) {
    const isProd = import.meta.env.PROD;
    const sources: FeatureFlagSources = {
      url: getUrlParamFlag(key),
      localStorage: getLocalStorageFlag(key),
      env: getEnvFlag(key),
    };
    
    const result = resolveFeatureFlag(key, isProd, sources);
    
    if (sources.url !== undefined && (!isProd || key !== 'OWNER_CONSOLE_API')) {
      logFeatureFlagResolution(key, 'url', sources.url);
    } else if (sources.localStorage !== undefined && (!isProd || key !== 'OWNER_CONSOLE_API')) {
      logFeatureFlagResolution(key, 'localStorage', sources.localStorage);
    } else if (sources.env !== undefined) {
      logFeatureFlagResolution(key, 'env', sources.env);
    } else {
      logFeatureFlagResolution(key, 'default', result);
    }
    
    if (key === 'OWNER_CONSOLE_API' && !result && isProd) {
      console.warn(
        '[Feature Flags] OWNER_CONSOLE_API is disabled in production build. ' +
        'This will use mock authentication instead of real backend. ' +
        'Set VITE_FEATURE_OWNER_CONSOLE_API=true in environment variables.'
      );
    }
    
    return result;
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
