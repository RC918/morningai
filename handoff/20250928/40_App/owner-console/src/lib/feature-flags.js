/**
 * Feature Flags for Owner Console
 * 
 * Supports two types of flags:
 * 1. Legacy features (dashboard, checkout, etc.) - from VITE_FEATURES env var
 * 2. New Owner Console flags (OWNER_CONSOLE_*) - from VITE_FEATURE_* env vars
 * 
 * Priority for Owner Console flags: URL params → localStorage → env vars → default (false)
 */

const getEnabledFeatures = () => {
  const featuresEnv = import.meta.env.VITE_FEATURES || 'dashboard,checkout,settings'
  return featuresEnv.split(',').map(feature => feature.trim())
}

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
]

/**
 * Check if a key is a new Owner Console flag
 */
function isOwnerConsoleFlag(key) {
  return OWNER_CONSOLE_FLAGS.includes(key)
}

/**
 * Get feature flag value from URL query parameters
 */
function getUrlParamFlag(key) {
  if (typeof window === 'undefined') return undefined
  
  try {
    const params = new URLSearchParams(window.location.search)
    const paramKey = `feature_${key}`
    const value = params.get(paramKey)
    
    if (value === null) return undefined
    
    return value === 'true' || value === '1'
  } catch {
    return undefined
  }
}

/**
 * Get feature flag value from localStorage
 */
function getLocalStorageFlag(key) {
  if (typeof window === 'undefined') return undefined
  
  try {
    const storageKey = `feature_flag_${key}`
    const value = localStorage.getItem(storageKey)
    
    if (value === null) return undefined
    
    return value === 'true' || value === '1'
  } catch {
    return undefined
  }
}

/**
 * Static map of environment flags for Vite build-time inlining
 * Vite can only inline env vars that are accessed via direct dot notation,
 * not dynamic bracket access. This static map ensures all flags are included.
 */
const ENV_FLAGS = {
  OWNER_CONSOLE_API: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_API,
  OWNER_CONSOLE_GOVERNANCE: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_GOVERNANCE,
  OWNER_CONSOLE_TENANTS: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_TENANTS,
  OWNER_CONSOLE_MONITORING: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_MONITORING,
  OWNER_CONSOLE_SETTINGS: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_SETTINGS,
  OWNER_CONSOLE_SECURITY: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_SECURITY,
  OWNER_CONSOLE_PWA: import.meta.env.VITE_FEATURE_OWNER_CONSOLE_PWA,
}

/**
 * Get feature flag value from environment variables
 */
function getEnvFlag(key) {
  const envValue = ENV_FLAGS[key]
  
  if (envValue === undefined) return undefined
  
  return envValue === 'true' || envValue === '1'
}

/**
 * Check if a feature is enabled
 * 
 * For new Owner Console flags (OWNER_CONSOLE_*):
 * - Priority: URL params → localStorage → env vars → default (false)
 * 
 * For legacy features:
 * - Checks comma-separated VITE_FEATURES env var
 * 
 * @param {string} feature - Feature flag key
 * @returns {boolean} true if feature is enabled, false otherwise
 */
export const isFeatureEnabled = (feature) => {
  if (isOwnerConsoleFlag(feature)) {
    const urlValue = getUrlParamFlag(feature)
    if (urlValue !== undefined) return urlValue
    
    const localStorageValue = getLocalStorageFlag(feature)
    if (localStorageValue !== undefined) return localStorageValue
    
    const envValue = getEnvFlag(feature)
    if (envValue !== undefined) return envValue
    
    return false
  }
  
  const enabledFeatures = getEnabledFeatures()
  return enabledFeatures.includes(feature.toLowerCase())
}

export const getAvailableFeatures = () => {
  return getEnabledFeatures()
}

export const AVAILABLE_FEATURES = {
  DASHBOARD: 'dashboard',
  STRATEGIES: 'strategies', 
  APPROVALS: 'approvals',
  HISTORY: 'history',
  COSTS: 'costs',
  SETTINGS: 'settings',
  CHECKOUT: 'checkout'
}
