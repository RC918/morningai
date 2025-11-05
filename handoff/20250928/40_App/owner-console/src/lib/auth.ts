/**
 * Authentication Module for Owner Console
 * 
 * Issue #767: API Connection
 * Squad: Owner Console Squad
 * 
 * Week 0 P0-4: Feature flag OWNER_CONSOLE_API removed - Owner Console now always uses real API.
 * Mock data has been removed. Real backend configuration is required.
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


export interface AuthTokens {
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
  user: User;
  tokens: AuthTokens;
  requires_2fa?: boolean;
}

export interface RefreshTokenResponse {
  tokens: {
    expiresAt: number;
  };
}


const TOKEN_EXPIRY_KEY = 'morningai_token_expiry';
const USER_STORAGE_KEY = 'morningai_user';
const TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000; // Refresh 5 minutes before expiry


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
  
  try {
    localStorage.removeItem(TOKEN_EXPIRY_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear auth data:', error);
  }
  
  clearCsrfToken();
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

import { API_BASE_URL } from './config';

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
 */
function getCsrfToken(): string | null {
  if (typeof document !== 'undefined') {
    const cookieToken = getCookie('csrf_token');
    if (cookieToken) {
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
 */
async function ensureCsrfToken(): Promise<void> {
  if (typeof window === 'undefined') return;
  
  const cookieToken = typeof document !== 'undefined' ? getCookie('csrf_token') : null;
  let sessionToken = null;
  if (typeof sessionStorage !== 'undefined') {
    try {
      sessionToken = sessionStorage.getItem('csrf_token');
    } catch (error) {
      console.error('Failed to read CSRF token from sessionStorage:', error);
    }
  }
  
  if (cookieToken || sessionToken) {
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
      const csrfUrl = `${API_BASE_URL}/api/auth/v2/csrf`;
      
      const response = await fetch(csrfUrl, {
        method: 'GET',
        credentials: 'include',
      });
      
      if (!response.ok) {
        console.error('Failed to fetch CSRF token:', response.status, response.statusText);
        return;
      }
      
      const contentType = response.headers.get('content-type');
      if (!contentType || !contentType.includes('application/json')) {
        const text = await response.text();
        console.error('CSRF fetch error: Expected JSON but got', contentType);
        console.error('Request URL:', csrfUrl);
        console.error('Response preview:', text.substring(0, 200));
        return;
      }
      
      const data = await response.json();
      if (data.csrf_token) {
        storeCsrfToken(data.csrf_token);
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
  
  try {
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
    
    storeTokenExpiry(data.tokens.expiresAt);
    storeUser(data.user);
    
    return data;
  } catch (error) {
    if (error instanceof TypeError && error.message.toLowerCase().includes('fetch')) {
      throw new Error('Network connection failed. Please check your connection or contact support.');
    }
    throw error;
  }
}

/**
 * Logout and clear tokens
 * Backend will blacklist the refresh token and clear cookies
 */
export async function logout(): Promise<void> {
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
  
  clearTokens();
  clearCsrfToken();
}

/**
 * Refresh access token using refresh token
 * Backend handles token rotation automatically
 */
export async function refreshAccessToken(): Promise<AuthTokens> {
  const response = await fetch(`${API_BASE_URL}/api/auth/v2/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    credentials: 'include',
  });
  
  if (!response.ok) {
    clearTokens();
    throw new Error('Token refresh failed. Please login again.');
  }
  
  const data: RefreshTokenResponse = await response.json();
  
  const newTokens: AuthTokens = {
    expiresAt: data.tokens.expiresAt,
  };
  
  storeTokenExpiry(newTokens.expiresAt);
  
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
