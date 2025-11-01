const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || (
  typeof window !== 'undefined' && window.location.hostname.includes('vercel.app')
    ? '' // Use relative path for Vercel deployments (proxy handles routing)
    : 'https://morningai-backend-v2.onrender.com'
)
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

interface RequestOptions extends RequestInit {
  headers?: Record<string, string>
}

interface ApiError extends Error {
  status?: number
  requestId?: string
  endpoint?: string
}

class ApiClient {
  private baseURL: string
  private useMock: boolean

  constructor() {
    this.baseURL = API_BASE_URL
    this.useMock = USE_MOCK
  }

  async request(endpoint: string, options: RequestOptions = {}): Promise<any> {
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
        const error = new Error(errorData.error?.message || `HTTP error! status: ${response.status}`) as ApiError
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
      const apiError = error as ApiError
      if (!apiError.requestId) {
        apiError.requestId = requestId
        apiError.endpoint = endpoint
        
        console.error(`Network Error [${requestId}]: ${endpoint} - ${apiError.message}`, {
          url,
          config,
          errorType: apiError.name
        })
        
        window.dispatchEvent(new CustomEvent('api-error', {
          detail: { endpoint, error: apiError.message, status: 0, requestId, type: 'network' }
        }))

        if (window.Sentry) {
          window.Sentry.captureException(apiError, {
            tags: { section: 'api_client', endpoint, error_type: 'network' },
            extra: { requestId, url }
          })
        }
      }
      
      throw apiError
    }
  }

  async checkHealth(): Promise<{ healthy: boolean; error?: string }> {
    try {
      const response = await this.request('/health')
      return { healthy: true, ...response }
    } catch (error) {
      const apiError = error as ApiError
      console.warn('Backend health check failed:', apiError.message)
      return { healthy: false, error: apiError.message }
    }
  }

  async requestWithRetry(endpoint: string, options: RequestOptions = {}, maxRetries = 2): Promise<any> {
    let lastError: ApiError | undefined
    for (let attempt = 0; attempt <= maxRetries; attempt++) {
      try {
        return await this.request(endpoint, options)
      } catch (error) {
        const apiError = error as ApiError
        lastError = apiError
        if (attempt < maxRetries && (apiError.status === 0 || (apiError.status && apiError.status >= 500))) {
          console.warn(`Retry ${attempt + 1}/${maxRetries} for ${endpoint}:`, apiError.message)
          await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)))
          continue
        }
        break
      }
    }
    throw lastError
  }

  async verifyAuth(): Promise<any> {
    return this.request('/auth/verify')
  }

  async login(credentials: any): Promise<any> {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    })
  }

  async getBillingPlans(): Promise<any[]> {
    const endpoint = this.useMock ? '/checkout/mock' : '/billing/plans'
    const data = await this.request(endpoint)
    return this.useMock ? data.pricing_tiers || [] : data.plans || []
  }

  async createCheckoutSession(sessionData: any): Promise<any> {
    const endpoint = this.useMock ? '/checkout/mock' : '/billing/checkout/session'
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(sessionData),
    })
  }

  async getDashboardData(): Promise<any> {
    return this.requestWithRetry('/dashboard/data')
  }

  async getDashboardWidgets(): Promise<any> {
    return this.requestWithRetry('/dashboard/widgets')
  }

  async getReportTemplates(): Promise<any> {
    return this.request('/reports/templates')
  }

  async getReportHistory(): Promise<any> {
    return this.request('/reports/history')
  }

  async generateReport(reportData: any): Promise<any> {
    return this.request('/reports/generate', {
      method: 'POST',
      body: JSON.stringify(reportData),
    })
  }

  async getSettings(): Promise<any> {
    return this.request('/settings')
  }

  async saveSettings(settings: any): Promise<any> {
    return this.request('/settings', {
      method: 'POST',
      body: JSON.stringify(settings),
    })
  }

  async get(endpoint: string): Promise<any> {
    return this.request(endpoint, {
      method: 'GET',
    })
  }

  async post(endpoint: string, data: any): Promise<any> {
    return this.request(endpoint, {
      method: 'POST',
      body: JSON.stringify(data),
    })
  }
}

export const apiClient = new ApiClient()
export default apiClient
