const getEnabledFeatures = () => {
  const featuresEnv = import.meta.env.VITE_FEATURES || 'dashboard,checkout,settings'
  return featuresEnv.split(',').map(feature => feature.trim())
}

export const isFeatureEnabled = (feature) => {
  const enabledFeatures = getEnabledFeatures()
  return enabledFeatures.includes(feature)
}

export const getAvailableFeatures = () => {
  return getEnabledFeatures()
}

export const AVAILABLE_FEATURES = {
  DASHBOARD: 'dashboard',
  STRATEGIES: 'strategies', 
  APPROVALS: 'approvals',
  HISTORY: 'history',
  COSTS: 'costs',
  SETTINGS: 'settings',
  CHECKOUT: 'checkout'
}
