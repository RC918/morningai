/**
 * Authentication Module for Owner Console
 * 
 * Issue #767: API Connection
 * Squad: Owner Console Squad
 * Feature Flag: OWNER_CONSOLE_API
 * 
 * This module provides:
 * - JWT token management
 * - Refresh token mechanism
 * - Automatic token refresh on expiry
 * - Secure token storage
 * 
 * @see docs/PARALLEL_DEVELOPMENT_STRATEGY.md
 */

import { isFeatureEnabled } from './feature-flags';


export interface AuthTokens {
  accessToken: string;
  refreshToken: string;
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


const TOKEN_STORAGE_KEY = 'morningai_auth_tokens';
const USER_STORAGE_KEY = 'morningai_user';
const TOKEN_REFRESH_BUFFER_MS = 5 * 60 * 1000; // Refresh 5 minutes before expiry


/**
 * Store auth tokens securely
 * 
 * In production, consider using:
 * - HttpOnly cookies for refresh token
 * - Memory storage for access token
 * - Encrypted localStorage as fallback
 */
export function storeTokens(tokens: AuthTokens): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(tokens));
  } catch (error) {
    console.error('Failed to store auth tokens:', error);
  }
}

/**
 * Retrieve stored auth tokens
 */
export function getStoredTokens(): AuthTokens | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const stored = localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!stored) return null;
    
    const tokens = JSON.parse(stored) as AuthTokens;
    
    if (!tokens.accessToken || !tokens.refreshToken || !tokens.expiresAt) {
      clearTokens();
      return null;
    }
    
    return tokens;
  } catch (error) {
    console.error('Failed to retrieve auth tokens:', error);
    clearTokens();
    return null;
  }
}

/**
 * Clear stored auth tokens
 */
export function clearTokens(): void {
  if (typeof window === 'undefined') return;
  
  try {
    localStorage.removeItem(TOKEN_STORAGE_KEY);
    localStorage.removeItem(USER_STORAGE_KEY);
  } catch (error) {
    console.error('Failed to clear auth tokens:', error);
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
export function isTokenExpired(tokens: AuthTokens): boolean {
  const now = Date.now();
  const expiresAt = tokens.expiresAt;
  
  return now >= (expiresAt - TOKEN_REFRESH_BUFFER_MS);
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  const tokens = getStoredTokens();
  if (!tokens) return false;
  
  return Date.now() < tokens.expiresAt;
}


const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000';

/**
 * Make authenticated API request
 */
async function authenticatedFetch(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const tokens = getStoredTokens();
  
  if (!tokens) {
    throw new Error('Not authenticated');
  }
  
  if (isTokenExpired(tokens)) {
    await refreshAccessToken();
    const newTokens = getStoredTokens();
    if (!newTokens) {
      throw new Error('Token refresh failed');
    }
    
    const headers = new Headers(options.headers);
    headers.set('Authorization', `Bearer ${newTokens.accessToken}`);
    
    return fetch(url, { ...options, headers });
  }
  
  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${tokens.accessToken}`);
  
  return fetch(url, { ...options, headers });
}


/**
 * Login with email and password
 */
export async function login(credentials: LoginCredentials): Promise<LoginResponse> {
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    return {
      user: {
        id: 'mock-user-id',
        email: credentials.email,
        role: 'owner',
        tenantId: 'mock-tenant-id',
        name: 'Mock User',
      },
      tokens: {
        accessToken: 'mock-access-token',
        refreshToken: 'mock-refresh-token',
        expiresAt: Date.now() + 60 * 60 * 1000, // 1 hour
      },
    };
  }
  
  const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(credentials),
  });
  
  if (!response.ok) {
    const error = await response.json().catch(() => ({ message: 'Login failed' }));
    throw new Error(error.message || 'Login failed');
  }
  
  const data: LoginResponse = await response.json();
  
  storeTokens(data.tokens);
  storeUser(data.user);
  
  return data;
}

/**
 * Logout and clear tokens
 */
export async function logout(): Promise<void> {
  const tokens = getStoredTokens();
  
  if (tokens && isFeatureEnabled('OWNER_CONSOLE_API')) {
    try {
      await fetch(`${API_BASE_URL}/api/auth/logout`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${tokens.accessToken}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          refreshToken: tokens.refreshToken,
        }),
      });
    } catch (error) {
      console.error('Logout API call failed:', error);
    }
  }
  
  clearTokens();
}

/**
 * Refresh access token using refresh token
 */
export async function refreshAccessToken(): Promise<AuthTokens> {
  const tokens = getStoredTokens();
  
  if (!tokens) {
    throw new Error('No refresh token available');
  }
  
  if (!isFeatureEnabled('OWNER_CONSOLE_API')) {
    const newTokens: AuthTokens = {
      accessToken: 'mock-refreshed-access-token',
      refreshToken: tokens.refreshToken,
      expiresAt: Date.now() + 60 * 60 * 1000, // 1 hour
    };
    storeTokens(newTokens);
    return newTokens;
  }
  
  const response = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refreshToken: tokens.refreshToken,
    }),
  });
  
  if (!response.ok) {
    clearTokens();
    throw new Error('Token refresh failed. Please login again.');
  }
  
  const data: RefreshTokenResponse = await response.json();
  
  const newTokens: AuthTokens = {
    accessToken: data.accessToken,
    refreshToken: tokens.refreshToken, // Keep existing refresh token
    expiresAt: data.expiresAt,
  };
  
  storeTokens(newTokens);
  
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
  
  const response = await authenticatedFetch(`${API_BASE_URL}/api/auth/me`);
  
  if (!response.ok) {
    throw new Error('Failed to fetch user');
  }
  
  const user: User = await response.json();
  storeUser(user);
  
  return user;
}


let refreshInterval: NodeJS.Timeout | null = null;

/**
 * Start automatic token refresh
 * 
 * Checks token expiry every minute and refreshes if needed
 */
export function startTokenRefresh(): void {
  if (refreshInterval) {
    return; // Already started
  }
  
  refreshInterval = setInterval(async () => {
    const tokens = getStoredTokens();
    
    if (!tokens) {
      stopTokenRefresh();
      return;
    }
    
    if (isTokenExpired(tokens)) {
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
  }, 60 * 1000); // Check every minute
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
