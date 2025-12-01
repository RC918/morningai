/**
 * AI Policies API Client
 * 
 * Provides functions to interact with the AI policies API endpoints.
 * Phase 6 PR-2: AI Policy Editor UI
 * 
 * P1 Enhancement: 401 Retry Mechanism
 * - On 401 "Token expired" response, attempts to refresh token and retry request once
 * - If retry fails, clears tokens and redirects to login
 */

import { getOrRefreshAccessToken, refreshAccessToken, clearTokens, RefreshAccessTokenError } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

/**
 * Helper function to make authenticated fetch requests with 401 retry logic
 * @param {string} url - Full URL to fetch
 * @param {Object} options - Fetch options
 * @param {string} errorMessage - Error message to throw on failure
 * @returns {Promise<Response>} Fetch response
 */
async function authenticatedFetchWithRetry(url, options, errorMessage) {
  const buildHeaders = async () => {
    const token = await getOrRefreshAccessToken()
    const headers = { 'Content-Type': 'application/json' }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`
    }
    return headers
  }
  
  const headers = await buildHeaders()
  
  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include'
  })
  
  // Handle 401 Token Expired with retry logic
  if (response.status === 401) {
    try {
      // Attempt to refresh the token
      await refreshAccessToken()
      
      // Rebuild headers with new token
      const retryHeaders = await buildHeaders()
      
      // Retry the request once
      const retryResponse = await fetch(url, {
        ...options,
        headers: retryHeaders,
        credentials: 'include'
      })
      
      if (retryResponse.status === 401) {
        // Retry also failed - clear tokens and redirect to login
        clearTokens()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
        throw new Error('Authentication failed. Please login again.')
      }
      
      return retryResponse
    } catch (error) {
      // If refresh failed with session_invalid, clear tokens and redirect
      if (error instanceof RefreshAccessTokenError && error.code === 'session_invalid') {
        clearTokens()
        if (typeof window !== 'undefined') {
          window.location.href = '/login'
        }
      }
      throw error
    }
  }
  
  return response
}

/**
 * Get policy templates for guided editor
 * @returns {Promise<{templates: Object, count: number}>}
 */
export async function getPolicyTemplates() {
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies/templates`,
    { method: 'GET' },
    'Failed to fetch policy templates'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch policy templates' }))
    throw new Error(error.error || 'Failed to fetch policy templates')
  }

  return response.json()
}

/**
 * List AI policies for current tenant
 * @param {Object} options - Query options
 * @param {number} options.limit - Number of policies to return (default: 50)
 * @param {number} options.offset - Pagination offset (default: 0)
 * @param {string} options.policy_type - Filter by policy type
 * @param {string} options.status - Filter by status (active, inactive, draft)
 * @returns {Promise<{policies: Array, count: number, limit: number, offset: number}>}
 */
export async function listPolicies({ limit = 50, offset = 0, policy_type, status } = {}) {
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() })
  if (policy_type) params.append('policy_type', policy_type)
  if (status) params.append('status', status)
  
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies?${params}`,
    { method: 'GET' },
    'Failed to fetch policies'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch policies' }))
    throw new Error(error.error || 'Failed to fetch policies')
  }

  return response.json()
}

/**
 * Get a specific policy by ID
 * @param {string} policyId - Policy UUID
 * @returns {Promise<Object>} Policy object
 */
export async function getPolicy(policyId) {
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies/${policyId}`,
    { method: 'GET' },
    'Failed to fetch policy'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch policy' }))
    throw new Error(error.error || 'Failed to fetch policy')
  }

  return response.json()
}

/**
 * Create a new AI policy
 * @param {Object} policy - Policy data
 * @param {string} policy.name - Policy name (required)
 * @param {string} policy.policy_type - Policy type (required)
 * @param {Object} policy.rules - Policy rules (required)
 * @param {string} policy.description - Policy description
 * @param {number} policy.priority - Priority (default: 0)
 * @param {string} policy.status - Status (draft, active, inactive)
 * @returns {Promise<Object>} Created policy
 */
export async function createPolicy(policy) {
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies`,
    { method: 'POST', body: JSON.stringify(policy) },
    'Failed to create policy'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to create policy' }))
    throw new Error(error.error || 'Failed to create policy')
  }

  return response.json()
}

/**
 * Update an existing AI policy
 * @param {string} policyId - Policy UUID
 * @param {Object} updates - Fields to update
 * @param {string} updates.name - Policy name
 * @param {string} updates.description - Policy description
 * @param {Object} updates.rules - Policy rules
 * @param {number} updates.priority - Priority
 * @param {string} updates.status - Status
 * @returns {Promise<Object>} Updated policy
 */
export async function updatePolicy(policyId, updates) {
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies/${policyId}`,
    { method: 'PUT', body: JSON.stringify(updates) },
    'Failed to update policy'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to update policy' }))
    throw new Error(error.error || 'Failed to update policy')
  }

  return response.json()
}

/**
 * Delete an AI policy
 * @param {string} policyId - Policy UUID
 * @returns {Promise<{message: string, policy_id: string}>}
 */
export async function deletePolicy(policyId) {
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies/${policyId}`,
    { method: 'DELETE' },
    'Failed to delete policy'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to delete policy' }))
    throw new Error(error.error || 'Failed to delete policy')
  }

  return response.json()
}

/**
 * Evaluate if a request is allowed based on tenant policies
 * @param {string} capability - Capability to evaluate
 * @param {Object} context - Additional context
 * @returns {Promise<{allowed: boolean, reason: string, applied_policies: Array}>}
 */
export async function evaluateRequest(capability, context = {}) {
  const response = await authenticatedFetchWithRetry(
    `${API_BASE_URL}/api/ai-policies/evaluate`,
    { method: 'POST', body: JSON.stringify({ capability, context }) },
    'Failed to evaluate request'
  )

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to evaluate request' }))
    throw new Error(error.error || 'Failed to evaluate request')
  }

  return response.json()
}
