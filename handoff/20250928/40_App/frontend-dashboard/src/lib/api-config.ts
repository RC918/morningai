/**
 * Centralized API configuration
 * 
 * This module provides a single source of truth for the API base URL.
 * All API calls should use this configuration to ensure consistency.
 * 
 * Environment Variables:
 * - VITE_API_BASE_URL: Override the default API URL (required for Vercel previews)
 * 
 * Default Behavior:
 * - Production: Uses https://morningai-backend-v2.onrender.com
 * - Development: Uses VITE_API_BASE_URL if set, otherwise falls back to production URL
 * 
 * Security Notes:
 * - Never falls back to localhost in production builds
 * - Always uses HTTPS for production backend
 * - Vercel previews must set VITE_API_BASE_URL environment variable
 */

/**
 * Get the API base URL from environment or use production default
 * 
 * This ensures that:
 * 1. Vercel previews can override via VITE_API_BASE_URL env var
 * 2. Production builds never fall back to localhost (security)
 * 3. All API calls use the same base URL (consistency)
 */
export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://morningai-backend-v2.onrender.com'

/**
 * Check if we're in development mode
 */
export const isDevelopment = import.meta.env.DEV

/**
 * Check if we're using the default production URL
 */
export const isUsingDefaultUrl = !import.meta.env.VITE_API_BASE_URL

/**
 * Log configuration on startup (development only)
 */
if (isDevelopment) {
  console.debug('[API Config]', {
    baseUrl: API_BASE_URL,
    isDefault: isUsingDefaultUrl,
    env: import.meta.env.MODE
  })
}
