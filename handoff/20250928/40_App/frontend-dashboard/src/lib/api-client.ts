/**
 * API Client Adapter (P1 Fix: Consolidate duplicate API clients)
 * 
 * This file now serves as a thin adapter that forwards to the canonical api.ts implementation.
 * This eliminates code duplication while preserving the functional-style API for new code.
 * 
 * Migration path:
 * - Phase 1 (this PR): Adapter forwards to api.ts, both import paths work
 * - Phase 2 (follow-up PR): Migrate all imports to use api.ts directly
 * - Phase 3 (follow-up PR): Remove this adapter file
 */

import { apiClient as classApiClient } from './api'

/**
 * Functional-style API client that forwards to the canonical class-based implementation
 * 
 * Usage: apiClient<T>('/api/endpoint', { method: 'POST', body: JSON.stringify(data) })
 * 
 * Note: This adapter normalizes URLs to work with api.ts which expects endpoints without '/api' prefix
 */
export const apiClient = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const endpoint = url.startsWith('/api') ? url.slice(4) : url
  
  return classApiClient.request(endpoint, options as any) as Promise<T>
}

/**
 * Legacy customFetch for backward compatibility
 * Forwards to the canonical implementation
 * 
 * @deprecated Use apiClient() instead
 */
export const customFetch = async (options: { url: string; [key: string]: any }) => {
  const { url, ...fetchOptions } = options
  const endpoint = url.startsWith('/api') ? url.slice(4) : url
  
  return classApiClient.request(endpoint, fetchOptions as any)
}

/**
 * Bootstrap CSRF token - forwards to canonical implementation
 */
export const bootstrapCsrf = () => classApiClient.bootstrapCsrf()
