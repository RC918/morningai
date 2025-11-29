/**
 * Failures & Experiments API Client
 * 
 * Provides functions to interact with the failures and experiments API endpoints.
 * Phase 5 PR-6: Owner Console Dashboard
 * 
 * Auth Fix: Uses authenticatedFetch() from auth.ts for proper cookie-based auth
 * - Owner Console uses HttpOnly cookie-based authentication (not Bearer tokens)
 * - authenticatedFetch handles: cookies, CSRF tokens, automatic token refresh
 * - Previous bug: used raw fetch with Bearer token which doesn't work with cookie auth
 */

import { authenticatedFetch } from './auth.ts';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

/**
 * Get failure summary statistics
 * @returns {Promise<{summary: Object, timestamp: string}>}
 */
export async function getFailureSummary() {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/failures/summary`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch failure summary' }))
    throw new Error(error.error || 'Failed to fetch failure summary')
  }

  return response.json()
}

/**
 * Get list of failures with pagination
 * @param {Object} options - Query options
 * @param {number} options.limit - Number of failures to return (default: 50)
 * @param {number} options.offset - Pagination offset (default: 0)
 * @param {string} options.error_type - Filter by error type
 * @param {string} options.task_type - Filter by task type
 * @returns {Promise<{failures: Array, count: number, limit: number, offset: number}>}
 */
export async function getFailures({ limit = 50, offset = 0, error_type, task_type } = {}) {
  const params = new URLSearchParams({ limit: limit.toString(), offset: offset.toString() })
  if (error_type) params.append('error_type', error_type)
  if (task_type) params.append('task_type', task_type)
  
  const response = await authenticatedFetch(`${API_BASE_URL}/api/failures?${params}`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch failures' }))
    throw new Error(error.error || 'Failed to fetch failures')
  }

  return response.json()
}

/**
 * Get evaluation metrics summary
 * @returns {Promise<{metrics: Object, timestamp: string}>}
 */
export async function getEvalMetrics() {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/failures/eval/metrics`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch eval metrics' }))
    throw new Error(error.error || 'Failed to fetch eval metrics')
  }

  return response.json()
}

/**
 * Replay a failed workflow
 * @param {string} failureId - ID of the failure to replay
 * @param {Object} options - Replay options
 * @param {string} options.repo - Override repository
 * @returns {Promise<Object>}
 */
export async function replayFailure(failureId, { repo } = {}) {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/failures/${failureId}/replay`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ repo })
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to replay failure' }))
    throw new Error(error.error || 'Failed to replay failure')
  }

  return response.json()
}

/**
 * Get experiment summary
 * @returns {Promise<{summary: Object, timestamp: string}>}
 */
export async function getExperimentSummary() {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/experiments/summary`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch experiment summary' }))
    throw new Error(error.error || 'Failed to fetch experiment summary')
  }

  return response.json()
}

/**
 * Get list of experiments
 * @returns {Promise<{experiments: Object, environment: string, active_experiments: Array}>}
 */
export async function getExperiments() {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/experiments`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch experiments' }))
    throw new Error(error.error || 'Failed to fetch experiments')
  }

  return response.json()
}

/**
 * Get experiment comparison data for visualization
 * @returns {Promise<{comparisons: Array, environment: string, active_experiments: Array}>}
 */
export async function getExperimentComparison() {
  const response = await authenticatedFetch(`${API_BASE_URL}/api/experiments/comparison`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Failed to fetch experiment comparison' }))
    throw new Error(error.error || 'Failed to fetch experiment comparison')
  }

  return response.json()
}

/**
 * Check failures API health
 * @returns {Promise<{failure_recorder_available: boolean, components: Object}>}
 */
export async function checkFailuresHealth() {
  const response = await fetch(`${API_BASE_URL}/api/failures/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error('Failures API is unhealthy')
  }

  return response.json()
}

/**
 * Check experiments API health
 * @returns {Promise<{experiment_manager_available: boolean, components: Object}>}
 */
export async function checkExperimentsHealth() {
  const response = await fetch(`${API_BASE_URL}/api/experiments/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error('Experiments API is unhealthy')
  }

  return response.json()
}
