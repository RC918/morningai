/**
 * Unified CSRF Token Management Module
 *
 * This module provides a single source of truth for CSRF token management,
 * consolidating the previously duplicated logic from auth.ts and api-client.ts.
 *
 * Storage Strategy:
 * - Cookie: Set by backend, read-only from frontend (source of truth for auth flows)
 * - SessionStorage: Persistent across page reloads within the same session
 * - In-memory (csrfTokenCache): Fast access for API client, cleared on page refresh
 *
 * Two different priority modes:
 * - Auth mode (getCsrfToken): Cookie > SessionStorage > In-memory
 *   Used by auth.ts to ensure cookie rotation is respected
 * - API Client mode (getApiClientCsrfToken): Cache > Cookie
 *   Used by api-client.ts to preserve cross-origin behavior where cache takes priority
 *
 * IMPORTANT: Choosing the Correct Mode
 * - For auth flows (login, logout, token refresh): Use `getCsrfToken()` (cookie-first)
 * - For API client requests: Use `getApiClientCsrfToken()` (cache-first)
 * - Do NOT use `getApiClientCsrfToken()` in auth flows - this will break cookie rotation
 * - Do NOT use `getCsrfToken()` in cross-origin API requests - this may cause issues
 *
 * @module csrf-token
 */

const API_BASE_URL =
  (import.meta as any).env?.VITE_API_BASE_URL ||
  (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') ||
  '';

/**
 * In-memory CSRF token cache for auth flows
 * Used as fallback when cookie/sessionStorage are not available
 */
let csrfToken: string | null = null;

/**
 * In-memory CSRF token cache for API client
 * This is separate from csrfToken to preserve the original api-client.ts behavior
 * where cached token from response body takes priority over cookie
 */
let csrfTokenCache: string | null = null;

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
 * Bootstrap CSRF token for API client
 * This matches the original api-client.ts behavior:
 * - Fetches token from /api/auth/v2/csrf
 * - Caches token in csrfTokenCache (not sessionStorage)
 * - Logs specific messages expected by tests
 *
 * @returns Promise that resolves when token is available
 */
export async function bootstrapCsrf(): Promise<void> {
  if (!API_BASE_URL) {
    return;
  }

  const url = `${API_BASE_URL}/api/auth/v2/csrf`;
  console.debug('Bootstrapping CSRF token from:', url);

  try {
    const response = await fetch(url, {
      method: 'GET',
      credentials: 'include',
    });

    if (!response.ok) {
      console.error('CSRF bootstrap failed with status:', response.status);
      return;
    }

    const contentType = response.headers?.get?.('content-type') || '';
    if (!contentType.includes('application/json')) {
      return;
    }

    const data = await response.json();
    if (data.csrf_token) {
      csrfTokenCache = data.csrf_token;
      console.debug('CSRF token cached from response body');
    }
  } catch (error) {
    console.warn('Failed to bootstrap CSRF token:', error);
  }
}

/**
 * Get CSRF token for API client requests
 * This preserves the original api-client.ts behavior:
 * - Priority: Cache (from response body) > Cookie (for same-origin)
 * - Does NOT read from sessionStorage (that's for auth flows)
 *
 * @returns CSRF token or null if not available
 */
export function getApiClientCsrfToken(): string | null {
  if (typeof document === 'undefined') return null;

  // Priority 1: Cache from response body (for cross-origin scenarios)
  if (csrfTokenCache) {
    return csrfTokenCache;
  }

  // Priority 2: Cookie (for same-origin scenarios)
  const match = document.cookie.match(/csrf_token=([^;]+)/);
  return match ? match[1] : null;
}

/**
 * Set the API client CSRF token cache
 * Used when receiving token from response headers
 *
 * @param token - The token to cache
 */
export function setApiClientCsrfCache(token: string): void {
  csrfTokenCache = token;
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
 * Updates both the API client cache and the auth storage layers
 *
 * @param headers - Response headers
 */
export function updateCsrfFromResponse(headers: Headers): void {
  const newToken = headers.get('X-CSRF-Token');
  if (newToken) {
    // Update API client cache
    csrfTokenCache = newToken;
    // Also sync to auth storage layers
    storeCsrfToken(newToken);
  }
}

/**
 * For testing: Reset all CSRF state
 * This should only be used in test environments
 */
export function _resetCsrfState(): void {
  csrfToken = null;
  csrfTokenCache = null;
  csrfTokenPromise = null;
  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionStorage.removeItem('csrf_token');
    } catch (error) {
      // Ignore
    }
  }
}
