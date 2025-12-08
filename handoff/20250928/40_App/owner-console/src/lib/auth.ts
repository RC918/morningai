/**
 * Authentication Module for Owner Console
 * 
 * Issue #767: API Connection
 * Squad: Owner Console Squad
 * Feature Flag: OWNER_CONSOLE_API
 * 
 * Task 1: Enhanced Token Security (v2 API)
 * - HttpOnly cookies for access and refresh tokens
 * - Automatic token rotation on refresh
 * - Redis-based token blacklist
 * - No token storage in localStorage (security improvement)
 * - Uses /api/auth/v2/* endpoints for enhanced security
 * 
 * This module provides:
 * - JWT token management via HttpOnly cookies
 * - Refresh token mechanism with rotation
 * - Automatic token refresh on expiry
 * - Secure cookie-based authentication
 * 
 * @see docs/PARALLEL_DEVELOPMENT_STRATEGY.md
 * @see docs/TASK_1_ENHANCED_TOKEN_SECURITY.md
 */

import { isFeatureEnabled } from './feature-flags.ts';

/**
 * E2E Test Environment Flag
 * Only enable localStorage token persistence in E2E test environment
 * to prevent XSS attacks in production
 */
const IS_E2E = import.meta.env.VITE_E2E === 'true';

export interface AuthTokens {
  accessToken?: string; // Access token (for fallback when cookies are blocked)
  expiresAt: number; // Unix timestamp in milliseconds
}

export interface User {
  id: string;
  email: string;
  role: 'owner' | 'admin' | 'viewer';
  tenantId: string;
  name?: string;
  avatar?: string;
}

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  user?: User;
  tokens?: AuthTokens;
  next_step?: 'enroll_2fa' | 'challenge_2fa' | 'session';
  tmp_login_token?: string;
  requires_2fa?: boolean;
  message?: string;
}

export interface RefreshTokenResponse {
  tokens: {
    accessToken?: string;
    expiresAt: number;
  };
}

/**
 * Error codes for token refresh failures
 * - 'network_error': Transient network issues (fetch failed, timeout, 5xx errors)
 * - 'session_invalid': Backend explicitly rejected the session (401/403)
 * - 'unknown': Other unexpected errors
 */
export type RefreshErrorCode = 'network_error' | 'session_invalid' | 'unknown';

/**
 * Custom error class for token refresh failures
 * Allows callers to distinguish between transient network errors and invalid sessions
 */
export class RefreshAccessTokenError extends Error {
  code: RefreshErrorCode;
  status?: number;

  constructor(code: RefreshErrorCode, message: string, status?: number) {
    super(message);
    this.code = code;
    this.status = status;
    this.name = 'RefreshAccessTokenError';
  }
}


const TOKEN_EXPIRY_KEY = 'morningai_token_expiry';
const USER_STORAGE_KEY = 'morningai_user';
const ACCESS_TOKEN_KEY = 'morningai_access_token';
const TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000; // Refresh 5 minutes before expiry

let inMemoryAccessToken: string | null = null;


/**
 * Store access token in memory and localStorage (for E2E tests only)
 * 
 * SECURITY: 
 * - In-memory storage is preferred for production (prevents XSS attacks)
 * - localStorage is ONLY used in E2E test environment (VITE_E2E=true)
 * - Production builds never store tokens in localStorage to prevent XSS attacks
 * - localStorage is necessary for E2E tests because Playwright's storageState restoration has timing issues with sessionStorage
 * - Token is cleared on logout to minimize security risk
 * 
 * RATIONALE FOR localStorage IN E2E ONLY:
 * - sessionStorage has timing issues: page loads before Playwright restores storage
 * - localStorage is restored synchronously before page JavaScript executes
 * - E2E tests need reliable token persistence across page navigations
 * - Production builds are protected by IS_E2E gate (VITE_E2E defaults to false)
 */
export function storeAccessToken(token: string | null | undefined): void {
  // Treat falsy and bad sentinel values as "no token"
  // This prevents storing literal "null" or "undefined" strings which would
  // cause "Authorization: Bearer null" to be sent in API requests
  if (!token || token === 'null' || token === 'undefined') {
    inMemoryAccessToken = null;
    if (IS_E2E && typeof localStorage !== 'undefined') {
      try {
        localStorage.removeItem(ACCESS_TOKEN_KEY);
      } catch (error) {
        console.error('Failed to clear access token from localStorage:', error);
      }
    }
    return;
  }
  
  inMemoryAccessToken = token;
  
  if (IS_E2E && typeof localStorage !== 'undefined') {
    try {
      localStorage.setItem(ACCESS_TOKEN_KEY, token);
    } catch (error) {
      console.error('Failed to store access token in localStorage:', error);
    }
  }
}

/**
 * Get access token from memory or localStorage (E2E tests only)
 * 
 * SECURITY:
 * - Always prefer in-memory token first
 * - Only read from localStorage in E2E test environment (VITE_E2E=true)
 * - Production builds never read tokens from localStorage to prevent XSS attacks
 * - Filters out literal "null" and "undefined" strings to prevent "Authorization: Bearer null"
 */
export function getAccessToken(): string | null {
  // Check in-memory token first, filtering out bad sentinel values
  if (inMemoryAccessToken && inMemoryAccessToken !== 'null' && inMemoryAccessToken !== 'undefined') {
    return inMemoryAccessToken;
  }
  
  if (IS_E2E && typeof localStorage !== 'undefined') {
    try {
      const storedToken = localStorage.getItem(ACCESS_TOKEN_KEY);
      // Filter out bad sentinel values from localStorage
      if (storedToken && storedToken !== 'null' && storedToken !== 'undefined') {
        inMemoryAccessToken = storedToken;
        return storedToken;
      }
    } catch (error) {
      console.error('Failed to retrieve access token from localStorage:', error);
    }
  }
  
  return null;
}

/**
 * Single-flight promise for token refresh
 * Prevents concurrent API calls from triggering multiple refresh requests
 */
let tokenRefreshPromise: Promise<string | null> | null = null;

/**
 * Get access token, refreshing if necessary
 * 
 * This function handles the case where the in-memory token is lost after page refresh
 * but the session is still valid (expiresAt in localStorage). In this case, it will
 * automatically call /api/auth/v2/refresh to get a new access token.
 * 
 * Also handles the case where the token exists but is expired or about to expire,
 * proactively refreshing to avoid 401 errors.
 * 
 * Uses single-flight pattern to prevent concurrent refresh requests.
 * 
 * @returns Promise<string | null> - The access token or null if not authenticated
 */
export async function getOrRefreshAccessToken(): Promise<string | null> {
  // Check if we have a valid session (expiresAt in localStorage)
  const expiresAt = getStoredTokenExpiry();
  if (!expiresAt) {
    // No session at all, user needs to login
    return null;
  }
  
  // Check if we have a valid token in memory that is NOT about to expire
  const existingToken = getAccessToken();
  if (existingToken && !isTokenExpired(expiresAt)) {
    // Token exists and is not near expiry -> fast path
    return existingToken;
  }
  
  // Either no token in memory, or token is expired/within buffer -> try refresh
  // If session is truly invalid, refreshAccessToken will throw 'session_invalid'
  // and clear tokens, effectively logging the user out
  
  // We need to refresh: either no token in memory, or token is about to expire
  // Use single-flight pattern to prevent concurrent refresh requests
  if (tokenRefreshPromise) {
    return tokenRefreshPromise;
  }
  
  tokenRefreshPromise = (async () => {
    try {
      const newTokens = await refreshAccessToken();
      return newTokens.accessToken ?? null;
    } catch (error) {
      // Handle different error types appropriately
      if (error instanceof RefreshAccessTokenError) {
        if (error.code === 'session_invalid') {
          // Session is invalid - tokens already cleared by refreshAccessToken
          console.warn('Session invalid during token refresh');
        } else if (error.code === 'network_error') {
          // Transient network error - do NOT clear tokens
          // User stays logged in, but this API call will fail
          console.warn('Network error during token refresh, keeping session:', error.message);
          // Return existing token if available, even if about to expire
          // This allows the request to proceed and potentially succeed
          const fallbackToken = getAccessToken();
          if (fallbackToken) {
            return fallbackToken;
          }
        }
      } else {
        // Unexpected error - log but don't clear tokens to be safe
        console.error('Unexpected error while refreshing access token:', error);
      }
      return null;
    } finally {
      tokenRefreshPromise = null;
    }
  })();
  
  return tokenRefreshPromise;
}

/**
 * Store token expiry time
 * Note: Actual tokens are stored in HttpOnly cookies by the backend
 */
export function storeTokenExpiry(expiresAt: number): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(TOKEN_EXPIRY_KEY, expiresAt.toString());
  } catch (error) {
    console.error('Failed to store token expiry:', error);
  }
}

/**
 * Retrieve stored token expiry time
 */
export function getStoredTokenExpiry(): number | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const stored = localStorage.getItem(TOKEN_EXPIRY_KEY);
    if (!stored) return null;
    
    const expiresAt = parseInt(stored, 10);
    if (isNaN(expiresAt)) {
      clearTokens();
      return null;
    }
    
    return expiresAt;
  } catch (error) {
    console.error('Failed to retrieve token expiry:', error);
    clearTokens();
    return null;
  }
}

/**
 * Clear stored auth data
 * Note: HttpOnly cookies are cleared by the backend on logout
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  
  inMemoryAccessToken = null;
  
  try {
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
    localStorage.removeItem(ACCESS_TOKEN_KEY);
  } catch (error) {
    console.error('Failed to clear auth data:', error);
  }
  
  clearCsrfToken();
}

/**
 * Clear tokens and redirect to login page
 * Use this when authentication has failed and user needs to re-login
 */
export function clearTokensAndRedirectToLogin(): void {
  clearTokens();
  if (typeof window !== 'undefined') {
    window.location.href = '/login';
  }
}

/**
 * Store user information
 */
export function storeUser(user: User): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(USER_STORAGE_KEY, JSON.stringify(user));
  } catch (error) {
    console.error('Failed to store user:', error);
  }
}

/**
 * Retrieve stored user information
 */
export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const stored = localStorage.getItem(USER_STORAGE_KEY);
    if (!stored) return null;
    
    return JSON.parse(stored) as User;
  } catch (error) {
    console.error('Failed to retrieve user:', error);
    return null;
  }
}


/**
 * Check if access token is expired or about to expire
 */
export function isTokenExpired(expiresAt: number): boolean {
  const now = Date.now();
  return now >= (expiresAt - TOKEN_REFRESH_BUFFER_MS);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const expiresAt = getStoredTokenExpiry();
  if (!expiresAt) return false;
  
  return Date.now() < expiresAt;
}


const API_BASE_URL = (import.meta as any).env?.VITE_API_BASE_URL || (typeof process !== 'undefined' ? process.env.VITE_API_BASE_URL : '') || 
  (import.meta.env.MODE === 'development' ? 'http://localhost:5000' : '');

if (import.meta.env.PROD && !API_BASE_URL) {
  console.error(
    '[Auth] API Base URL is not configured. ' +
    'Set VITE_API_BASE_URL in environment variables. ' +
    'Expected: https://morningai-backend-v2-stg.onrender.com (staging) or production URL'
  );
}

/**
 * CSRF token storage
 * Stored in-memory and sessionStorage for cross-origin compatibility
 * Cannot use document.cookie in cross-origin scenarios (even with SameSite=None)
 */
let csrfToken: string | null = null;

/**
 * Single-flight promise for CSRF token fetching
 * Prevents concurrent requests from fetching the same token multiple times
 */
let csrfTokenPromise: Promise<void> | null = null;

if (typeof sessionStorage !== 'undefined') {
  try {
    csrfToken = sessionStorage.getItem('csrf_token');
  } catch (error) {
    console.error('Failed to load CSRF token from sessionStorage:', error);
  }
}

/**
 * Get CSRF token from cookie (preferred) or in-memory storage (fallback)
 * Tests set csrf_token cookie, so we must read from there first
 * 
 * P0 Fix: Always sync sessionStorage with cookie value
 * When backend rotates CSRF token (e.g., on login), the cookie changes but
 * sessionStorage may still have the old value. This caused "CSRF token invalid"
 * errors because ensureCsrfToken() would see sessionStorage token and skip
 * fetching, while getCsrfToken() correctly read the new cookie value.
 * Now we always sync sessionStorage when cookie differs to prevent drift.
 */
function getCsrfToken(): string | null {
  if (typeof document !== 'undefined') {
    const cookieToken = getCookie('csrf_token');
    if (cookieToken) {
      // Sync sessionStorage with cookie to prevent drift
      if (typeof sessionStorage !== 'undefined') {
        try {
          const sessionToken = sessionStorage.getItem('csrf_token');
          if (sessionToken !== cookieToken) {
            sessionStorage.setItem('csrf_token', cookieToken);
            csrfToken = cookieToken;
          }
        } catch (error) {
          // Ignore sessionStorage errors, cookie is the source of truth
        }
      }
      return cookieToken;
    }
  }
  
  if (typeof sessionStorage !== 'undefined') {
    try {
      const sessionToken = sessionStorage.getItem('csrf_token');
      if (sessionToken) {
        return sessionToken;
      }
    } catch (error) {
      console.error('Failed to read CSRF token from sessionStorage:', error);
    }
  }
  
  return csrfToken;
}

/**
 * Store CSRF token in both in-memory and sessionStorage
 */
function storeCsrfToken(token: string): void {
  csrfToken = token;
  
  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionStorage.setItem('csrf_token', token);
    } catch (error) {
      console.error('Failed to store CSRF token in sessionStorage:', error);
    }
  }
}

/**
 * Clear CSRF token from both in-memory and sessionStorage
 */
function clearCsrfToken(): void {
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
 * Ensure CSRF token exists by fetching it if missing
 * 
 * P0 Fix: Read CSRF token from JSON response instead of document.cookie
 * This is required for cross-origin authentication (admin.gm365.me → morningai-backend-v2.onrender.com)
 * Even with SameSite=None, HttpOnly cookies cannot be read by JavaScript
 * 
 * P1 Enhancement: Single-flight promise pattern
 * Prevents concurrent requests from fetching the same token multiple times
 * 
 * Preview Mode: Skip for /ux-metrics in preview when VITE_PREVIEW_PUBLIC_METRICS is enabled
 */
async function ensureCsrfToken(): Promise<void> {
  if (typeof window === 'undefined') return;
  
  if (import.meta.env.VITE_PREVIEW_PUBLIC_METRICS === 'true' &&
      window.location.pathname.startsWith('/ux-metrics')) {
    return;
  }
  
  if (!API_BASE_URL) {
    console.warn('CSRF token fetch skipped: VITE_API_BASE_URL not configured');
    return;
  }
  
  // Use getCsrfToken() which syncs sessionStorage with cookie automatically
  // This ensures we don't have stale tokens after backend rotates the cookie
  const existingToken = getCsrfToken();
  if (existingToken) {
    return;
  }
  
  if (csrfToken) {
    clearCsrfToken();
  }
  
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
        console.error('CSRF fetch failed: Expected JSON but got', contentType, 'from', url);
        console.error('Response preview:', text.substring(0, 200));
        return;
      }
      
      if (response.ok) {
        const data = await response.json();
        if (data.csrf_token) {
          storeCsrfToken(data.csrf_token);
        }
      } else {
        console.error('Failed to fetch CSRF token:', response.status, response.statusText);
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
 * Get cookie value by name
 * 
 * Note: This function is kept for potential future use but should NOT be used
 * for CSRF tokens in cross-origin scenarios. Use getCsrfToken() instead.
 */
function getCookie(name: string): string | null {
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
 * Check if CSRF token should be included for this HTTP method
 */
function shouldIncludeCSRF(method?: string): boolean {
  if (!method) return false;
  const upperMethod = method.toUpperCase();
  return ['POST', 'PUT', 'PATCH', 'DELETE'].includes(upperMethod);
}

/**
 * Check if a 403 response is a CSRF failure
 * 
 * Discriminates between CSRF token failures and real authorization failures
 * by inspecting the response body for CSRF-related error messages.
 * 
 * Backend returns: {'error': 'CSRF token missing/invalid/...'}
 * 
 * @param response - The 403 response to check
 * @returns Promise<boolean> - True if this is a CSRF failure, false otherwise
 */
async function isCsrfFailure(response: Response): Promise<boolean> {
  if (!response.headers || typeof response.headers.get !== 'function') {
    return false;
  }
  
  const contentType = response.headers.get('Content-Type') || '';
  if (!contentType.includes('application/json')) {
    return false;
  }
  
  try {
    const errorData = await response.clone().json();
    const errorMessage = [
      errorData.error,
      errorData.message,
      errorData.detail
    ]
      .filter(Boolean)
      .join(' ')
      .toLowerCase();
    
    return errorMessage.includes('csrf') || errorMessage.includes('xsrf');
  } catch (error) {
    console.debug('Failed to parse 403 response as JSON, treating as non-CSRF error');
    return false;
  }
}

/**
 * Make authenticated API request
 * Tokens are automatically sent via HttpOnly cookies
 * CSRF token is included for unsafe methods (POST, PUT, PATCH, DELETE)
 * 
 * P0 Enhancement: 401 Refresh Retry Mechanism
 * - On 401 response, attempts to refresh token and retry request once
 * - If retry fails, clears tokens and redirects to login
 * 
 * P1 Enhancement: CSRF Defensive Programming
 * - Ensures CSRF token exists before first request
 * - Handles 403 CSRF failures with automatic token refresh and retry
 * - Discriminates between CSRF failures and real authorization errors
 * - Prevents requests from failing due to missing or expired CSRF tokens
 * 
 * Note: Backend does not currently use 419 status code for CSRF failures
 */
async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const expiresAt = getStoredTokenExpiry();
  
  if (!expiresAt) {
    throw new Error('Not authenticated');
  }
  
  if (isTokenExpired(expiresAt)) {
    await refreshAccessToken();
  }
  
  if (shouldIncludeCSRF(options.method) && !getCsrfToken()) {
    await ensureCsrfToken();
  }
  
  const headers = new Headers(options.headers);
  if (shouldIncludeCSRF(options.method)) {
    const csrfToken = getCsrfToken();
    if (csrfToken) {
      headers.set('X-CSRF-Token', csrfToken);
    }
  }
  
  // Only add Authorization header if we have a valid token
  // Filter out literal "null" and "undefined" strings to prevent "Authorization: Bearer null"
  const accessToken = getAccessToken();
  if (accessToken && accessToken !== 'null' && accessToken !== 'undefined') {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });
  
  if (response.status === 403) {
    const isCsrf = await isCsrfFailure(response);
    
    if (!isCsrf) {
      return response;
    }
    
    try {
      clearCsrfToken();
      await ensureCsrfToken();
      
      const retryHeaders = new Headers(options.headers);
      if (shouldIncludeCSRF(options.method)) {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
          retryHeaders.set('X-CSRF-Token', csrfToken);
        }
      }
      
      // Only add Authorization header if we have a valid token
      const accessToken = getAccessToken();
      if (accessToken && accessToken !== 'null' && accessToken !== 'undefined') {
        retryHeaders.set('Authorization', `Bearer ${accessToken}`);
      }
      
      const retryResponse = await fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: 'include',
      });
      
      if (retryResponse.status === 403) {
        const isRetryCsrf = await isCsrfFailure(retryResponse);
        if (isRetryCsrf) {
          throw new Error('CSRF token validation failed. Please refresh the page.');
        }
        return retryResponse;
      }
      
      return retryResponse;
    } catch (error) {
      if (error instanceof Error && error.message.includes('CSRF')) {
        throw error;
      }
      console.error('CSRF token refresh failed:', error);
      return response;
    }
  }
  
  if (response.status === 401) {
    try {
      await refreshAccessToken();
      
      const retryHeaders = new Headers(options.headers);
      if (shouldIncludeCSRF(options.method)) {
        const csrfToken = getCsrfToken();
        if (csrfToken) {
          retryHeaders.set('X-CSRF-Token', csrfToken);
        }
      }
      
      // Only add Authorization header if we have a valid token
      const accessToken = getAccessToken();
      if (accessToken && accessToken !== 'null' && accessToken !== 'undefined') {
        retryHeaders.set('Authorization', `Bearer ${accessToken}`);
      }
      
      const retryResponse = await fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: 'include',
      });
      
      if (retryResponse.status === 401) {
        clearTokens();
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        throw new Error('Authentication failed. Please login again.');
      }
      
      return retryResponse;
    } catch (error) {
      clearTokens();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
      throw error;
    }
  }
  
  return response;
}


/**
 * Login with email and password
 * Tokens are stored in HttpOnly cookies by the backend
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  await ensureCsrfToken();
  
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    if (import.meta.env.PROD) {
      throw new Error(
        'Backend API is not configured. Please contact your system administrator. ' +
        '(OWNER_CONSOLE_API feature flag is disabled in production)'
      );
    }
    
    console.warn(
      '[Auth] Mock authentication is active. Using fake user data instead of real backend. ' +
      'Set VITE_FEATURE_OWNER_CONSOLE_API=true to enable real authentication.'
    );
    const mockTokens = {
      expiresAt: Date.now() + 60 * 60 * 1000,
    };
    return {
      user: {
        id: 'mock-user-id',
        email: credentials.email,
        role: 'owner',
        tenantId: 'mock-tenant-id',
        name: 'Mock User',
      },
      tokens: mockTokens,
    };
  }
  
  if (!API_BASE_URL) {
    throw new Error(
      'API Base URL is not configured. ' +
      'Please set VITE_API_BASE_URL environment variable. ' +
      'Contact your system administrator for the correct backend URL.'
    );
  }
  
  const response = await fetch(`${API_BASE_URL}/api/auth/v2/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
    body: JSON.stringify(credentials),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Login failed' }));
    throw new Error(error.message || 'Login failed');
  }
  
  const data: LoginResponse = await response.json();
  
  if (data.tokens && data.user) {
    storeTokenExpiry(data.tokens.expiresAt);
    storeUser(data.user);
    
    if (data.tokens.accessToken) {
      storeAccessToken(data.tokens.accessToken);
    }
  }
  
  return data;
}

/**
 * Logout and clear tokens
 * Backend will blacklist the refresh token and clear cookies
 */
export async function logout(): Promise<void> {
  if (isFeatureEnabled('OWNER_CONSOLE_API')) {
    try {
      const csrfToken = getCsrfToken();
      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      };
      
      if (csrfToken) {
        headers['X-CSRF-Token'] = csrfToken;
      }
      
      await fetch(`${API_BASE_URL}/api/auth/v2/logout`, {
        method: 'POST',
        headers,
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  }
  
  clearTokens();
  clearCsrfToken();
}

/**
 * Refresh access token using refresh token
 * Backend handles token rotation automatically
 * 
 * P1 Enhancement: CSRF-aware token refresh
 * - Ensures CSRF token exists before making the request
 * - Handles 403 CSRF failures with automatic token refresh and retry
 * - Discriminates between CSRF failures and real session invalid errors
 * - Prevents token refresh from failing due to missing or expired CSRF tokens
 */
export async function refreshAccessToken(): Promise<AuthTokens> {
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    const newTokens: AuthTokens = {
      expiresAt: Date.now() + 60 * 60 * 1000,
    };
    storeTokenExpiry(newTokens.expiresAt);
    return newTokens;
  }
  
  // Ensure CSRF token is bootstrapped before making the request
  // This handles the case where page reload clears in-memory token
  // and sessionStorage might not have the token yet
  if (!getCsrfToken()) {
    await ensureCsrfToken();
  }
  
  // Build headers with CSRF token for cross-origin requests
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
  };
  
  // Include CSRF token (required when SameSite=None)
  const csrfToken = getCsrfToken();
  if (csrfToken) {
    headers['X-CSRF-Token'] = csrfToken;
  }
  
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/auth/v2/refresh`, {
      method: 'POST',
      headers,
      credentials: 'include',
    });
  } catch (error) {
    // Network error (fetch failed, timeout, DNS error, etc.)
    // Do NOT clear tokens - this is a transient error
    throw new RefreshAccessTokenError(
      'network_error',
      'Network error while refreshing access token',
      undefined
    );
  }
  
  // Handle 403 CSRF failures with retry logic (mirrors authenticatedFetch pattern)
  if (response.status === 403) {
    const isCsrf = await isCsrfFailure(response);
    
    if (isCsrf) {
      // CSRF failure - try to re-bootstrap CSRF token and retry once
      try {
        clearCsrfToken();
        await ensureCsrfToken();
        
        // Build retry headers with fresh CSRF token
        const retryHeaders: HeadersInit = {
          'Content-Type': 'application/json',
        };
        const freshCsrfToken = getCsrfToken();
        if (freshCsrfToken) {
          retryHeaders['X-CSRF-Token'] = freshCsrfToken;
        }
        
        const retryResponse = await fetch(`${API_BASE_URL}/api/auth/v2/refresh`, {
          method: 'POST',
          headers: retryHeaders,
          credentials: 'include',
        });
        
        if (retryResponse.ok) {
          // Retry succeeded - process the response
          const data: RefreshTokenResponse = await retryResponse.json();
          const newTokens: AuthTokens = {
            accessToken: data.tokens.accessToken,
            expiresAt: data.tokens.expiresAt,
          };
          storeTokenExpiry(newTokens.expiresAt);
          if (data.tokens.accessToken) {
            storeAccessToken(data.tokens.accessToken);
          }
          return newTokens;
        }
        
        // Retry also failed - check if it's still a CSRF issue
        if (retryResponse.status === 403) {
          const isRetryCsrf = await isCsrfFailure(retryResponse);
          if (isRetryCsrf) {
            // CSRF still failing after retry - treat as network error, don't clear tokens
            throw new RefreshAccessTokenError(
              'network_error',
              'CSRF token validation failed. Please refresh the page.',
              403
            );
          }
        }
        
        // Retry failed with non-CSRF error - fall through to normal error handling
        response = retryResponse;
      } catch (error) {
        if (error instanceof RefreshAccessTokenError) {
          throw error;
        }
        // CSRF re-bootstrap failed - treat as network error
        throw new RefreshAccessTokenError(
          'network_error',
          'Failed to refresh CSRF token',
          undefined
        );
      }
    }
  }
  
  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      // Backend explicitly rejected the session (not CSRF) - clear tokens
      clearTokens();
      throw new RefreshAccessTokenError(
        'session_invalid',
        'Session is invalid or expired. Please login again.',
        response.status
      );
    }
    
    // Other HTTP errors (5xx, etc.) - treat as transient, do NOT clear tokens
    throw new RefreshAccessTokenError(
      'network_error',
      `Token refresh failed with status ${response.status}`,
      response.status
    );
  }
  
  const data: RefreshTokenResponse = await response.json();
  
  const newTokens: AuthTokens = {
    accessToken: data.tokens.accessToken,
    expiresAt: data.tokens.expiresAt,
  };
  
  storeTokenExpiry(newTokens.expiresAt);
  
  if (data.tokens.accessToken) {
    storeAccessToken(data.tokens.accessToken);
  }
  
  return newTokens;
}

/**
 * Get current user
 */
export async function getCurrentUser(): Promise<User> {
  const storedUser = getStoredUser();
  if (storedUser) {
    return storedUser;
  }
  
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    throw new Error('Not authenticated');
  }
  
  const response = await authenticatedFetch(`${API_BASE_URL}/api/auth/v2/me`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  
  const user: User = await response.json();
  storeUser(user);
  
  return user;
}


let refreshInterval: ReturnType<typeof setInterval> | null = null;

/**
 * Start automatic token refresh
 * 
 * Checks token expiry every minute and refreshes if needed
 */
export function startTokenRefresh(): void {
  if (refreshInterval) {
    return;
  }
  
  refreshInterval = setInterval(async () => {
    const expiresAt = getStoredTokenExpiry();
    
    if (!expiresAt) {
      stopTokenRefresh();
      return;
    }
    
    if (isTokenExpired(expiresAt)) {
      try {
        await refreshAccessToken();
      } catch (error) {
        console.error('Automatic token refresh failed:', error);
        stopTokenRefresh();
        clearTokens();
        
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
      }
    }
  }, 60 * 1000);
}

/**
 * Stop automatic token refresh
 */
export function stopTokenRefresh(): void {
  if (refreshInterval) {
    clearInterval(refreshInterval);
    refreshInterval = null;
  }
}


/**
 * Initialize authentication
 * 
 * Call this on app startup to:
 * - Bootstrap CSRF token if missing
 * - Check if user is authenticated
 * - Start automatic token refresh
 * - Redirect to login if needed
 */
export async function initAuth(): Promise<{ isAuthenticated: boolean; user: User | null }> {
  await ensureCsrfToken();
  
  const authenticated = isAuthenticated();
  const user = getStoredUser();
  
  if (authenticated && user) {
    startTokenRefresh();
  }
  
  return {
    isAuthenticated: authenticated,
    user,
  };
}

/**
 * Cleanup authentication
 * 
 * Call this on app unmount
 */
export function cleanupAuth(): void {
  stopTokenRefresh();
}


export { authenticatedFetch };
