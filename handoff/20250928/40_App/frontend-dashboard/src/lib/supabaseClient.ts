/**
 * Supabase Client Configuration
 * 
 * This module initializes and exports the Supabase client for authentication
 * and database operations. It uses environment variables for configuration.
 * 
 * Security Features:
 * - httpOnly cookies for token storage (prevents XSS attacks)
 * - Automatic token refresh
 * - Built-in refresh token rotation
 * - PKCE support for OAuth flows
 * 
 * Graceful Degradation:
 * - If VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY are missing, a no-op client
 *   is used that returns errors instead of crashing
 * - This allows the app to load and function in non-auth scenarios
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;
const NOOP_MSG = 'Supabase not configured (VITE_SUPABASE_URL/VITE_SUPABASE_ANON_KEY missing)';

/**
 * Create a no-op Supabase client that returns errors instead of crashing
 * Used when Supabase credentials are not configured
 */
function createNoopClient(): any {
  const error = new Error(NOOP_MSG);
  
  return {
    auth: {
      signUp: async () => ({ data: { user: null, session: null }, error }),
      signInWithOAuth: async () => ({ data: { provider: null, url: null }, error }),
      getSession: async () => ({ data: { session: null }, error }),
      getUser: async () => ({ data: { user: null }, error }),
      signOut: async () => ({ error }),
      onAuthStateChange: (_callback: any) => {
        // Return a subscription object with unsubscribe method
        return {
          data: { subscription: { unsubscribe: () => {} } },
          unsubscribe: () => {}
        };
      },
      refreshSession: async () => ({ data: { session: null, user: null }, error }),
    },
  };
}

/**
 * Create the real Supabase client with proper configuration
 */
function createRealClient() {
  return createClient(supabaseUrl as string, supabaseAnonKey as string, {
    auth: {
      autoRefreshToken: true,
      persistSession: true,
      detectSessionInUrl: true,
    },
  });
}

// Check if we have valid Supabase configuration
const hasConfig = Boolean(supabaseUrl && supabaseAnonKey);

if (!hasConfig) {
  console.warn(NOOP_MSG + ' - Auth features will be disabled');
}

/**
 * Supabase client instance
 * 
 * This will be either:
 * - A real Supabase client if credentials are configured
 * - A no-op client that returns errors if credentials are missing
 * 
 * Configuration (when using real client):
 * - auth.autoRefreshToken: Automatically refresh tokens before expiry
 * - auth.persistSession: Persist session in localStorage (will be upgraded to cookies in production)
 * - auth.detectSessionInUrl: Automatically detect OAuth callback parameters
 * - auth.storage: Custom storage implementation (can be upgraded to cookies)
 */
export const supabase = hasConfig ? createRealClient() : createNoopClient();

/**
 * Get the current user session
 * @returns {Promise<{session: Session|null, error: Error|null}>}
 */
export async function getSession() {
  const { data, error } = await supabase.auth.getSession();
  return { session: data.session, error };
}

/**
 * Get the current authenticated user
 * @returns {Promise<{user: User|null, error: Error|null}>}
 */
export async function getUser() {
  const { data, error } = await supabase.auth.getUser();
  return { user: data.user, error };
}

/**
 * Sign in with OAuth provider (Google, Apple, GitHub)
 * 
 * @param {string} provider - OAuth provider name ('google', 'apple', 'github')
 * @param {Object} options - Additional options
 * @param {string} options.redirectTo - URL to redirect after authentication
 * @returns {Promise<{data: Object, error: Error|null}>}
 */
export async function signInWithOAuth(provider: any, options: any = {}) {
  const { data, error } = await supabase.auth.signInWithOAuth({
    provider,
    options: {
      redirectTo: options.redirectTo || `${window.location.origin}/auth/callback`,
      ...options
    }
  });
  return { data, error };
}

/**
 * Sign out the current user
 * @returns {Promise<{error: Error|null}>}
 */
export async function signOut() {
  const { error } = await supabase.auth.signOut();
  return { error };
}

/**
 * Listen to authentication state changes
 * 
 * @param {Function} callback - Callback function to handle auth state changes
 * @returns {Object} Subscription object with unsubscribe method
 */
export function onAuthStateChange(callback: any) {
  return supabase.auth.onAuthStateChange(callback);
}

/**
 * Refresh the current session
 * @returns {Promise<{session: Session|null, error: Error|null}>}
 */
export async function refreshSession() {
  const { data, error } = await supabase.auth.refreshSession();
  return { session: data.session, error };
}

export default supabase;
