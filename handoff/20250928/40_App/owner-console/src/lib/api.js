const isProduction = import.meta.env.MODE === 'production'
const defaultURL = isProduction 
  ? 'https://morningai-backend-v2.onrender.com'
  : 'http://localhost:5001'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || defaultURL
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL
    this.useMock = USE_MOCK
  }

  async request(endpoint, options = {}) {
    const requestId = Math.random().toString(36).substr(2, 9)
    const url = `${this.baseURL}/api${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
        'X-Request-ID': requestId,
        ...options.headers,
      },
      ...options,
    }

    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    try {
      const response = await fetch(url, config)
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const error = new Error(errorData.error?.message || `HTTP error! status: ${response.status}`)
        error.status = response.status
        error.requestId = requestId
        error.endpoint = endpoint
        
        if (response.status === 401) {
          console.warn(`Authentication failed [${requestId}]: ${endpoint}`)
          
          localStorage.removeItem('auth_token')
          
          window.dispatchEvent(new CustomEvent('auth-error', {
            detail: { endpoint, requestId, message: 'Authentication required' }
          }))
          
          if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/auth')) {
            const returnUrl = encodeURIComponent(window.location.pathname + window.location.search)
            window.location.href = `/login?returnUrl=${returnUrl}`
          }
          
          throw error
        }
        
        console.error(`API Error [${requestId}]: ${endpoint} - ${error.message}`, {
          status: response.status,
          url,
          config
        })
        
        window.dispatchEvent(new CustomEvent('api-error', {
          detail: { endpoint, error: error.message, status: response.status, requestId }
        }))

        if (window.Sentry) {
          window.Sentry.captureException(error, {
            tags: { section: 'api_client', endpoint },
            extra: { requestId, status: response.status, url }
          })
        }

        throw error
      }
      return await response.json()
    } catch (error) {
      if (!error.requestId) {
        error.requestId = requestId
        error.endpoint = endpoint
        
        console.error(`Network Error [${requestId}]: ${endpoint} - ${error.message}`, {
          url,
          config,
          errorType: error.name
        })
        
        window.dispatchEvent(new CustomEvent('api-error', {
          detail: { endpoint, error: error.message, status: 0, requestId, type: 'network' }
        }))

        if (window.Sentry) {
          window.Sentry.captureException(error, {
            tags: { section: 'api_client', endpoint, error_type: 'network' },
            extra: { requestId, url }
          })
        }
      }
      
      throw error
    }
  }

  async checkHealth() {
    try {
      const response = await this.request('/health')
      return { healthy: true, ...response }
    } catch (error) {
      console.warn('Backend health check failed:', error.message)
      return { healthy: false, error: error.message }
    }
  }

  async requestWithRetry(endpoint, options = {}, maxRetries = 2) {
    let lastError
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.request(endpoint, options)
      } catch (error) {
        lastError = error
        if (attempt < maxRetries && (error.status === 0 || error.status >= 500)) {
          console.warn(`Retry ${attempt + 1}/${maxRetries} for ${endpoint}:`, error.message)
          await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
          continue
        }
        break
      }
    }
    throw lastError
  }

  async verifyAuth() {
    return this.request('/auth/verify')
  }

  async login(credentials) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  }

  async getBillingPlans() {
    const endpoint = this.useMock ? '/checkout/mock' : '/billing/plans'
    const data = await this.request(endpoint)
    return this.useMock ? data.pricing_tiers || [] : data.plans || []
  }

  async createCheckoutSession(sessionData) {
    const endpoint = this.useMock ? '/checkout/mock' : '/billing/checkout/session'
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(sessionData),
    })
  }

  async getDashboardData() {
    return this.requestWithRetry('/dashboard/data')
  }

  async getDashboardWidgets() {
    return this.requestWithRetry('/dashboard/widgets')
  }

  async getReportTemplates() {
    return this.request('/reports/templates')
  }

  async getReportHistory() {
    return this.request('/reports/history')
  }

  async generateReport(reportData) {
    return this.request('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(reportData),
    })
  }

  async getSettings() {
    return this.request('/settings')
  }

  async saveSettings(settings) {
    return this.request('/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    })
  }

  async get(endpoint) {
    return this.request(endpoint, {
      method: 'GET',
    })
  }

  async post(endpoint, data) {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }

  async getGovernanceAgents() {
    return this.requestWithRetry('/governance/agents')
  }

  async getGovernanceAgentDetails(agentId) {
    return this.requestWithRetry(`/governance/agents/${agentId}`)
  }

  async getGovernanceEvents(params = {}) {
    const queryParams = new URLSearchParams()
    if (params.agent_id) queryParams.append('agent_id', params.agent_id)
    if (params.limit) queryParams.append('limit', params.limit)
    
    const query = queryParams.toString()
    return this.requestWithRetry(`/governance/events${query ? `?${query}` : ''}`)
  }

  async getGovernanceCosts(params = {}) {
    const queryParams = new URLSearchParams()
    if (params.trace_id) queryParams.append('trace_id', params.trace_id)
    if (params.period) queryParams.append('period', params.period)
    
    const query = queryParams.toString()
    return this.requestWithRetry(`/governance/costs${query ? `?${query}` : ''}`)
  }

  async getGovernanceViolations(params = {}) {
    const queryParams = new URLSearchParams()
    if (params.agent_id) queryParams.append('agent_id', params.agent_id)
    if (params.limit) queryParams.append('limit', params.limit)
    
    const query = queryParams.toString()
    return this.requestWithRetry(`/governance/violations${query ? `?${query}` : ''}`)
  }

  async getGovernanceStatistics() {
    return this.requestWithRetry('/governance/statistics')
  }

  async getGovernanceLeaderboard(limit = 10) {
    return this.requestWithRetry(`/governance/leaderboard?limit=${limit}`)
  }

  async getGovernanceHealth() {
    return this.request('/governance/health')
  }
}

export const apiClient = new ApiClient()
export default apiClient
