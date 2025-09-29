const config = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000',
  appName: import.meta.env.VITE_APP_NAME || 'Morning AI',
  appVersion: import.meta.env.VITE_APP_VERSION || '1.0.0'
}

export default config
