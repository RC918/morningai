const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
const USE_COOKIE_AUTH = import.meta.env.VITE_USE_COOKIE_AUTH === 'true'

function getCsrfToken() {
  const match = document.cookie.match(/csrf_token=([^;]+)/)
  return match ? match[1] : null
}

export const customFetch = async (options) => {
  const { url, ...fetchOptions } = options
  
  const fullUrl = url.startsWith('http') ? url : `${API_BASE_URL}${url}`
  
  const config = {
    headers: {
      'Content-Type': 'application/json',
      ...fetchOptions.headers,
    },
    ...fetchOptions,
  }

  if (USE_COOKIE_AUTH) {
    config.credentials = 'include'
    
    const method = (fetchOptions.method || 'GET').toUpperCase()
    if (['POST', 'PUT', 'PATCH', 'DELETE'].includes(method)) {
      const csrfToken = getCsrfToken()
      if (csrfToken) {
        config.headers['X-CSRF-Token'] = csrfToken
      }
    }
  } else {
    const token = localStorage.getItem('auth_token')
    if (token) {
      config.headers = {
        ...config.headers,
        Authorization: `Bearer ${token}`,
      }
    }
  }

  try {
    const response = await fetch(fullUrl, config)
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error(`API request failed: ${fullUrl}`, error)
    throw error
  }
}
