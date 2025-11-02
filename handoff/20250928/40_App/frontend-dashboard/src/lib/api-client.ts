const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://morningai-backend-v2.onrender.com'

/**
 * CSRF token cache for cross-origin scenarios
 * In cross-origin requests, document.cookie cannot read cookies set by different domain
 * So we cache the token from the response body as a fallback
 */
let csrfTokenCache: string | null = null

/**
 * Get CSRF token from cache or cookie
 * Priority: cache (from response body) > cookie (for same-origin)
 */
function getCsrfToken(): string | null {
  if (typeof document === 'undefined') return null
  
  if (csrfTokenCache) {
    return csrfTokenCache
  }
  
  const match = document.cookie.match(/csrf_token=([^;]+)/)
  return match ? match[1] : null
}

/**
 * Refresh access token using refresh token
 */
async function refreshAccessToken(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/v2/refresh`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
    })
    
    if (!response.ok) {
      throw new Error('Token refresh failed')
    }
  } catch (error) {
    console.error('Token refresh failed:', error)
    throw error
  }
}

/**
 * API client with automatic credentials and CSRF token injection
 * 
 * P0 Security Enhancement:
 * - Adds credentials: 'include' to send HttpOnly cookies
 * - Injects X-CSRF-Token header for POST/PUT/PATCH/DELETE requests
 * - Uses cookie-based authentication instead of localStorage tokens
 * - Implements 401 refresh retry mechanism
 */
export const apiClient = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const response = await customFetch({ url, ...options })
  return response as T
}

export const customFetch = async (options: any) => {
  const { url, ...fetchOptions } = options
  
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`
  
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...fetchOptions.headers,
  }
  
  const unsafeMethods = ['POST', 'PUT', 'PATCH', 'DELETE']
  if (fetchOptions.method && unsafeMethods.includes(fetchOptions.method.toUpperCase())) {
    const csrfToken = getCsrfToken()
    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken
    }
  }
  
  const config = {
    ...fetchOptions,
    headers,
    credentials: 'include' as RequestCredentials,
  }

  try {
    const response = await fetch(fullUrl, config)
    
    if (!response.ok) {
      if (response.status === 401) {
        if (headers['X-Auth-Retry']) {
          console.warn(`Authentication retry failed: ${fullUrl}`)
          const errorData = await response.json().catch(() => ({}))
          const error: any = new Error(errorData.error?.message || `HTTP error! status: ${response.status}`)
          error.status = response.status
          throw error
        }
        
        console.warn(`Authentication failed: ${fullUrl}`)
        
        try {
          await refreshAccessToken()
          
          const retryHeaders: Record<string, string> = {
            'Content-Type': 'application/json',
            'X-Auth-Retry': '1',
            ...fetchOptions.headers,
          }
          
          if (fetchOptions.method && unsafeMethods.includes(fetchOptions.method.toUpperCase())) {
            const csrfToken = getCsrfToken()
            if (csrfToken) {
              retryHeaders['X-CSRF-Token'] = csrfToken
            }
          }
          
          const retryConfig = {
            ...fetchOptions,
            headers: retryHeaders,
            credentials: 'include' as RequestCredentials,
          }
          
          const retryResponse = await fetch(fullUrl, retryConfig)
          
          if (retryResponse.status === 401) {
            window.dispatchEvent(new CustomEvent('auth-error', {
              detail: { url: fullUrl, message: 'Authentication required' }
            }))
            
            if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/auth')) {
              const returnUrl = encodeURIComponent(window.location.pathname + window.location.search)
              window.location.href = `/login?returnUrl=${returnUrl}`
            }
            
            const errorData = await retryResponse.json().catch(() => ({}))
            const error: any = new Error(errorData.error?.message || `HTTP error! status: ${retryResponse.status}`)
            error.status = retryResponse.status
            throw error
          }
          
          if (!retryResponse.ok) {
            const errorData = await retryResponse.json().catch(() => ({}))
            const error: any = new Error(errorData.error?.message || `HTTP error! status: ${retryResponse.status}`)
            error.status = retryResponse.status
            throw error
          }
          
          return await retryResponse.json()
        } catch (refreshError) {
          window.dispatchEvent(new CustomEvent('auth-error', {
            detail: { url: fullUrl, message: 'Authentication required' }
          }))
          
          if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/auth')) {
            const returnUrl = encodeURIComponent(window.location.pathname + window.location.search)
            window.location.href = `/login?returnUrl=${returnUrl}`
          }
          
          throw refreshError
        }
      }
      
      const errorData = await response.json().catch(() => ({}))
      const error: any = new Error(errorData.error?.message || `HTTP error! status: ${response.status}`)
      error.status = response.status
      throw error
    }
    
    return await response.json()
  } catch (error) {
    console.error(`API request failed: ${fullUrl}`, error)
    throw error
  }
}

/**
 * Bootstrap CSRF token before making authenticated requests
 * Call this on app initialization
 * 
 * P0 Fix: Cache CSRF token from response body for cross-origin scenarios
 * Backend returns { csrf_token: "..." } in response body which we can read cross-origin
 */
export async function bootstrapCsrf(): Promise<void> {
  try {
    const response = await fetch(`${API_BASE_URL}/api/auth/v2/csrf`, {
      credentials: 'include',
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.csrf_token) {
        csrfTokenCache = data.csrf_token
        console.debug('CSRF token cached from response body')
      }
    }
  } catch (error) {
    console.warn('Failed to bootstrap CSRF token:', error)
  }
}
