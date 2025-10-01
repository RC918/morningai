const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL
    this.useMock = USE_MOCK
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}/api${endpoint}`
    const config = {
      headers: {
        'Content-Type': 'application/json',
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
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      return await response.json()
    } catch (error) {
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
