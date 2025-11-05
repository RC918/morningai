/**
 * Centralized configuration for the owner console application.
 * 
 * This module provides a single source of truth for API configuration,
 * with defensive normalization to handle malformed environment variables.
 */

/**
 * Normalizes a base URL to ensure it's absolute and properly formatted.
 * 
 * @param raw - The raw URL string from environment variables
 * @returns A normalized absolute URL without trailing slash
 */
export function normalizeBaseUrl(raw: string): string {
  const trimmed = (raw || '').trim();
  
  // If empty, return localhost default
  if (!trimmed) {
    return 'http://localhost:5000';
  }
  
  // If missing http:// or https://, prepend https://
  if (!/^https?:\/\//i.test(trimmed)) {
    return `https://${trimmed.replace(/\/+$/, '')}`;
  }
  
  // Remove trailing slashes
  return trimmed.replace(/\/+$/, '');
}

/**
 * The base URL for API requests.
 * 
 * This is derived from VITE_API_BASE_URL environment variable with defensive normalization.
 * Falls back to localhost:5000 for local development.
 */
export const API_BASE_URL = normalizeBaseUrl(
  import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'
);

// Log the API origin at startup for debugging (without leaking the full URL)
try {
  const url = new URL(API_BASE_URL);
  console.info('[config] API_BASE_URL origin:', url.origin);
} catch (error) {
  console.error('[config] Invalid API_BASE_URL:', API_BASE_URL, error);
}
