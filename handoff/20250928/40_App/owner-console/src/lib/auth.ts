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

import { isFeatureEnabled } from './feature-flags';


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
}

export interface RefreshTokenResponse {
  accessToken: string;
  expiresAt: number;
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


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

/**
 * Make authenticated API request
 * Tokens are automatically sent via HttpOnly cookies
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
  
  return fetch(url, {
    ...options,
    credentials: 'include',
  });
}


/**
 * Login with email and password
 * Tokens are stored in HttpOnly cookies by the backend
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
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
}

/**
 * Logout and clear tokens
 * Backend will blacklist the refresh token and clear cookies
 */
export async function logout(): Promise<void> {
  if (isFeatureEnabled('OWNER_CONSOLE_API')) {
    try {
      await fetch(`${API_BASE_URL}/api/auth/v2/logout`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
      });
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  }
  
  clearTokens();
}

/**
 * Refresh access token using refresh token
 * Backend handles token rotation automatically
 */
export async function refreshAccessToken(): Promise<AuthTokens> {
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    const newTokens: AuthTokens = {
      expiresAt: Date.now() + 60 * 60 * 1000,
    };
    storeTokenExpiry(newTokens.expiresAt);
    return newTokens;
  }
  
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
    expiresAt: data.expiresAt,
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
 * - Check if user is authenticated
 * - Start automatic token refresh
 * - Redirect to login if needed
 */
export function initAuth(): { isAuthenticated: boolean; user: User | null } {
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
