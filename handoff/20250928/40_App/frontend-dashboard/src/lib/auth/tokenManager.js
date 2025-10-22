const TOKEN_KEY = 'auth_token'
const REFRESH_TOKEN_KEY = 'refresh_token'
const TOKEN_EXPIRY_KEY = 'token_expiry'
const REFRESH_BUFFER_MS = 5 * 60 * 1000

class TokenManager {
  constructor() {
    this.refreshTimer = null
    this.isRefreshing = false
    this.refreshSubscribers = []
    this.apiBaseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
  }

  setTokens(accessToken, refreshToken, expiresIn) {
    localStorage.setItem(TOKEN_KEY, accessToken)
    
    if (refreshToken) {
      localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
    }
    
    if (expiresIn) {
      const expiryTime = Date.now() + (expiresIn * 1000)
      localStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString())
      this.scheduleTokenRefresh(expiresIn * 1000)
    }
  }

  getAccessToken() {
    return localStorage.getItem(TOKEN_KEY)
  }

  getRefreshToken() {
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  getTokenExpiry() {
    const expiry = localStorage.getItem(TOKEN_EXPIRY_KEY)
    return expiry ? parseInt(expiry, 10) : null
  }

  isTokenExpired() {
    const expiry = this.getTokenExpiry()
    if (!expiry) return false
    return Date.now() >= expiry
  }

  shouldRefreshToken() {
    const expiry = this.getTokenExpiry()
    if (!expiry) return false
    return Date.now() >= (expiry - REFRESH_BUFFER_MS)
  }

  clearTokens() {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(TOKEN_EXPIRY_KEY)
    
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
      this.refreshTimer = null
    }
  }

  scheduleTokenRefresh(expiresInMs) {
    if (this.refreshTimer) {
      clearTimeout(this.refreshTimer)
    }

    const refreshTime = Math.max(0, expiresInMs - REFRESH_BUFFER_MS)
    
    this.refreshTimer = setTimeout(async () => {
      try {
        await this.refreshAccessToken()
      } catch (error) {
        console.error('Scheduled token refresh failed:', error)
        window.dispatchEvent(new CustomEvent('auth:token-refresh-failed', { 
          detail: { error: error.message } 
        }))
      }
    }, refreshTime)
  }

  async refreshAccessToken() {
    if (this.isRefreshing) {
      return new Promise((resolve, reject) => {
        this.refreshSubscribers.push({ resolve, reject })
      })
    }

    this.isRefreshing = true

    try {
      const refreshToken = this.getRefreshToken()
      
      if (!refreshToken) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${this.apiBaseUrl}/api/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ refresh_token: refreshToken })
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.error?.message || 'Token refresh failed')
      }

      const data = await response.json()
      
      this.setTokens(data.access_token, data.refresh_token, data.expires_in)

      this.refreshSubscribers.forEach(subscriber => subscriber.resolve(data.access_token))
      this.refreshSubscribers = []

      window.dispatchEvent(new CustomEvent('auth:token-refreshed', { 
        detail: { token: data.access_token } 
      }))

      return data.access_token
    } catch (error) {
      this.refreshSubscribers.forEach(subscriber => subscriber.reject(error))
      this.refreshSubscribers = []

      this.clearTokens()

      window.dispatchEvent(new CustomEvent('auth:token-refresh-failed', { 
        detail: { error: error.message } 
      }))

      throw error
    } finally {
      this.isRefreshing = false
    }
  }

  async getValidToken() {
    if (this.isTokenExpired()) {
      throw new Error('Token expired')
    }

    if (this.shouldRefreshToken()) {
      try {
        return await this.refreshAccessToken()
      } catch (error) {
        console.error('Token refresh failed:', error)
        return this.getAccessToken()
      }
    }

    return this.getAccessToken()
  }

  async ensureValidToken() {
    try {
      return await this.getValidToken()
    } catch (error) {
      this.clearTokens()
      throw error
    }
  }
}

export const tokenManager = new TokenManager()
export default tokenManager
