/**
 * Unified CSRF Token Management Module
 *
 * This module provides a single source of truth for CSRF token management,
 * consolidating the previously duplicated logic from auth.ts and api-client.ts.
 *
 * Storage Strategy:
 * - Cookie: Set by backend, read-only from frontend (source of truth when available)
 * - SessionStorage: Persistent across page reloads within the same session
 * - In-memory: Fast access, cleared on page refresh
 *
 * Priority for reading: Cookie > SessionStorage > In-memory
 * All storage layers are kept in sync when any value is read or written.
 *
 * @module csrf-token
 */

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') ||
  '';

/**
 * In-memory CSRF token cache
 * Used as fallback when cookie/sessionStorage are not available
 */
let csrfToken: string | null = null;

/**
 * Single-flight promise for CSRF token fetching
 * Prevents concurrent requests from fetching the same token multiple times
 */
let csrfTokenPromise: Promise<void> | null = null;

/**
 * Initialize from sessionStorage on module load (browser only)
 */
if (typeof sessionStorage !== 'undefined') {
  try {
    csrfToken = sessionStorage.getItem('csrf_token');
  } catch (error) {
    console.error('Failed to load CSRF token from sessionStorage:', error);
  }
}

/**
 * Get cookie value by name
 *
 * @param name - Cookie name to retrieve
 * @returns Cookie value or null if not found
 */
export function getCookie(name: string): string | null {
  if (typeof document === 'undefined') return null;

  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);

  if (parts.length === 2) {
    const cookieValue = parts.pop();
    return cookieValue ? cookieValue.split(';').shift() || null : null;
  }

  return null;
}

/**
 * Sync all storage layers with the given token value
 * This is the core function that ensures consistency across all storage mechanisms
 *
 * @param token - The token value to sync across all storage layers
 */
function syncAllStorageLayers(token: string): void {
  csrfToken = token;

  if (typeof sessionStorage !== 'undefined') {
    try {
      const currentSessionToken = sessionStorage.getItem('csrf_token');
      if (currentSessionToken !== token) {
        sessionStorage.setItem('csrf_token', token);
      }
    } catch (error) {
      // Ignore sessionStorage errors, in-memory is the fallback
    }
  }
}

/**
 * Get CSRF token from the most authoritative source available
 *
 * Priority: Cookie (backend source of truth) > SessionStorage > In-memory
 *
 * When reading from cookie, all other storage layers are synced to ensure
 * consistency when backend rotates the token (e.g., on login).
 *
 * @returns CSRF token or null if not available
 */
export function getCsrfToken(): string | null {
  // Priority 1: Cookie (source of truth when available)
  if (typeof document !== 'undefined') {
    const cookieToken = getCookie('csrf_token');
    if (cookieToken) {
      // Always sync all storage layers with cookie value
      syncAllStorageLayers(cookieToken);
      return cookieToken;
    }
  }

  // Priority 2: SessionStorage (persists across page reloads)
  if (typeof sessionStorage !== 'undefined') {
    try {
      const sessionToken = sessionStorage.getItem('csrf_token');
      if (sessionToken) {
        // Sync in-memory with sessionStorage
        csrfToken = sessionToken;
        return sessionToken;
      }
    } catch (error) {
      console.error('Failed to read CSRF token from sessionStorage:', error);
    }
  }

  // Priority 3: In-memory (fallback)
  return csrfToken;
}

/**
 * Store CSRF token in all storage layers
 *
 * @param token - The token to store
 */
export function storeCsrfToken(token: string): void {
  syncAllStorageLayers(token);
}

/**
 * Clear CSRF token from all storage layers
 */
export function clearCsrfToken(): void {
  csrfToken = null;

  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionStorage.removeItem('csrf_token');
    } catch (error) {
      console.error('Failed to clear CSRF token from sessionStorage:', error);
    }
  }
}

/**
 * Check if we should skip CSRF operations for preview mode
 *
 * @returns true if CSRF should be skipped
 */
function shouldSkipCsrf(): boolean {
  if (typeof window === 'undefined') return true;

  // Skip for /ux-metrics in preview mode
  if (
    import.meta.env.VITE_PREVIEW_PUBLIC_METRICS === 'true' &&
    window.location.pathname.startsWith('/ux-metrics')
  ) {
    return true;
  }

  return false;
}

/**
 * Check if CSRF token exists in any storage layer
 * This checks directly without using getCsrfToken() to avoid
 * returning early based on stale in-memory values in test environments
 *
 * @returns Object with token value and source
 */
function checkExistingToken(): { token: string | null; source: 'cookie' | 'session' | 'memory' | null } {
  // Check cookie first (source of truth)
  if (typeof document !== 'undefined') {
    const cookieToken = getCookie('csrf_token');
    if (cookieToken) {
      return { token: cookieToken, source: 'cookie' };
    }
  }

  // Check sessionStorage
  if (typeof sessionStorage !== 'undefined') {
    try {
      const sessionToken = sessionStorage.getItem('csrf_token');
      if (sessionToken) {
        return { token: sessionToken, source: 'session' };
      }
    } catch (error) {
      console.error('Failed to read CSRF token from sessionStorage:', error);
    }
  }

  return { token: null, source: null };
}

/**
 * Ensure CSRF token exists by fetching it if missing
 *
 * Features:
 * - Single-flight pattern: Prevents concurrent requests from fetching multiple times
 * - Cross-origin support: Reads token from JSON response body (not just cookies)
 * - Automatic sync: Syncs all storage layers when token is fetched
 * - Preview mode: Skips for /ux-metrics when VITE_PREVIEW_PUBLIC_METRICS is enabled
 *
 * @returns Promise that resolves when token is available
 */
export async function ensureCsrfToken(): Promise<void> {
  if (shouldSkipCsrf()) return;

  if (!API_BASE_URL) {
    console.warn('CSRF token fetch skipped: VITE_API_BASE_URL not configured');
    return;
  }

  // Check existing token directly (not via getCsrfToken to avoid stale in-memory values)
  const existing = checkExistingToken();

  if (existing.token) {
    // Token exists - sync all storage layers if from cookie
    if (existing.source === 'cookie') {
      syncAllStorageLayers(existing.token);
    } else if (existing.source === 'session') {
      // Sync in-memory with sessionStorage
      csrfToken = existing.token;
    }
    return;
  }

  // Clear any stale in-memory token
  if (csrfToken) {
    clearCsrfToken();
  }

  // Use single-flight pattern to prevent concurrent fetches
  if (csrfTokenPromise) {
    return csrfTokenPromise;
  }

  csrfTokenPromise = (async () => {
    try {
      const url = `${API_BASE_URL}/api/auth/v2/csrf`;
      const response = await fetch(url, {
        method: 'GET',
        credentials: 'include',
      });

      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('application/json')) {
        const text = await response.text();
        console.error(
          'CSRF fetch failed: Expected JSON but got',
          contentType,
          'from',
          url
        );
        console.error('Response preview:', text.substring(0, 200));
        return;
      }

      if (response.ok) {
        const data = await response.json();
        if (data.csrf_token) {
          storeCsrfToken(data.csrf_token);
        }
      } else {
        console.error(
          'Failed to fetch CSRF token:',
          response.status,
          response.statusText
        );
      }
    } catch (error) {
      console.error('Failed to fetch CSRF token:', error);
    } finally {
      csrfTokenPromise = null;
    }
  })();

  return csrfTokenPromise;
}

/**
 * Bootstrap CSRF token (alias for ensureCsrfToken for backward compatibility)
 * This is kept for api-client.ts compatibility
 *
 * @returns Promise that resolves when token is available
 */
export async function bootstrapCsrf(): Promise<void> {
  return ensureCsrfToken();
}

/**
 * HTTP methods that require CSRF token
 */
export const UNSAFE_METHODS = ['POST', 'PUT', 'PATCH', 'DELETE'];

/**
 * Check if a request method requires CSRF protection
 *
 * @param method - HTTP method
 * @returns true if CSRF token should be included
 */
export function shouldIncludeCsrf(method: string): boolean {
  return UNSAFE_METHODS.includes(method.toUpperCase());
}

/**
 * Get CSRF token for use in request headers
 * This is a convenience function that returns the token in the format
 * expected by the X-CSRF-Token header
 *
 * @returns CSRF token or null
 */
export function getCsrfTokenForHeader(): string | null {
  return getCsrfToken();
}

/**
 * Update CSRF token from response header if present
 * Some endpoints may return a new CSRF token in the response header
 *
 * @param headers - Response headers
 */
export function updateCsrfFromResponse(headers: Headers): void {
  const newToken = headers.get('X-CSRF-Token');
  if (newToken) {
    storeCsrfToken(newToken);
  }
}

/**
 * For testing: Reset all CSRF state
 * This should only be used in test environments
 */
export function _resetCsrfState(): void {
  csrfToken = null;
  csrfTokenPromise = null;
  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionStorage.removeItem('csrf_token');
    } catch (error) {
      // Ignore
    }
  }
}
