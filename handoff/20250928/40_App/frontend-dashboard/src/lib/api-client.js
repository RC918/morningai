const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'https://morningai-backend-v2.onrender.com'

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

  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers = {
      ...config.headers,
      Authorization: `Bearer ${token}`,
    }
  }

  try {
    const response = await fetch(fullUrl, config)
    
    if (!response.ok) {
      if (response.status === 401) {
        console.warn(`Authentication failed: ${fullUrl}`)
        localStorage.removeItem('auth_token')
        
        window.dispatchEvent(new CustomEvent('auth-error', {
          detail: { url: fullUrl, message: 'Authentication required' }
        }))
        
        if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/auth')) {
          const returnUrl = encodeURIComponent(window.location.pathname + window.location.search)
          window.location.href = `/login?returnUrl=${returnUrl}`
        }
      }
      
      const errorData = await response.json().catch(() => ({}))
      const error = new Error(errorData.error?.message || `HTTP error! status: ${response.status}`)
      error.status = response.status
      throw error
    }
    
    return await response.json()
  } catch (error) {
    console.error(`API request failed: ${fullUrl}`, error)
    throw error
  }
}
