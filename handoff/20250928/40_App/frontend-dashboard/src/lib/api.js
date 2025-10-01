const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
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
        
        window.dispatchEvent(new CustomEvent('api-error', {
          detail: { endpoint, error: error.message, status: response.status, requestId }
        }))

        if (window.Sentry) {
          window.Sentry.captureException(error, {
            tags: { section: 'api_client' },
            extra: { endpoint, requestId, status: response.status }
          })
        }

        throw error
      }
      return await response.json()
    } catch (error) {
      if (!error.requestId) {
        error.requestId = requestId
        error.endpoint = endpoint
        
        window.dispatchEvent(new CustomEvent('api-error', {
          detail: { endpoint, error: error.message, status: 0, requestId }
        }))

        if (window.Sentry) {
          window.Sentry.captureException(error, {
            tags: { section: 'api_client' },
            extra: { endpoint, requestId }
          })
        }
      }
      
      console.error(`API request failed: ${endpoint}`, error)
      throw error
    }
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
    return this.request('/dashboard/data')
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
}

export const apiClient = new ApiClient()
export default apiClient
