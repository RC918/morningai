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
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.error?.message || `HTTP error! status: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error(`API request failed: ${fullUrl}`, error)
    throw error
  }
}
