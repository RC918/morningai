/**
 * Agent Evaluation API Client
 * 
 * Provides functions to interact with the agent evaluation API endpoints.
 */

import { getOrRefreshAccessToken } from './auth'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5000'

/**
 * Get agent evaluation results
 * @param {number} limit - Maximum number of evaluation runs to return (default: 10)
 * @returns {Promise<{evaluations: Array, latest: Object, count: number, timestamp: string}>}
 */
export async function getAgentEvaluationResults(limit = 10) {
  const token = await getOrRefreshAccessToken()
  
  const headers = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(`${API_BASE_URL}/api/agent-evaluation/results?limit=${limit}`, {
    method: 'GET',
    headers,
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: 'Failed to fetch evaluation results' } }))
    throw new Error(error.error?.message || 'Failed to fetch evaluation results')
  }

  return response.json()
}

/**
 * Get current agent evaluation metrics
 * @returns {Promise<{metrics: Object, targets: Object, last_evaluation: string, timestamp: string}>}
 */
export async function getAgentEvaluationMetrics() {
  const token = await getOrRefreshAccessToken()
  
  const headers = { 'Content-Type': 'application/json' }
  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }
  
  const response = await fetch(`${API_BASE_URL}/api/agent-evaluation/metrics`, {
    method: 'GET',
    headers,
    credentials: 'include'
  })

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: { message: 'Failed to fetch evaluation metrics' } }))
    throw new Error(error.error?.message || 'Failed to fetch evaluation metrics')
  }

  return response.json()
}

/**
 * Check agent evaluation API health
 * @returns {Promise<{status: string, service: string, timestamp: string}>}
 */
export async function checkAgentEvaluationHealth() {
  const response = await fetch(`${API_BASE_URL}/api/agent-evaluation/health`, {
    method: 'GET',
    headers: {
      'Content-Type': 'application/json'
    }
  })

  if (!response.ok) {
    throw new Error('Agent evaluation API is unhealthy')
  }

  return response.json()
}
