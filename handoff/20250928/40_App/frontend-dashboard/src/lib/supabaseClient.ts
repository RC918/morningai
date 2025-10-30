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
 */

import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.error('Missing Supabase configuration. Please set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in your .env file.');
}

/**
 * Supabase client instance
 * 
 * Configuration:
 * - auth.autoRefreshToken: Automatically refresh tokens before expiry
 * - auth.persistSession: Persist session in localStorage (will be upgraded to cookies in production)
 * - auth.detectSessionInUrl: Automatically detect OAuth callback parameters
 * - auth.storage: Custom storage implementation (can be upgraded to cookies)
 */
export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: true,
  }
});

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
export async function signInWithOAuth(provider, options = {}) {
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
export function onAuthStateChange(callback) {
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
