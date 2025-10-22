import i18n from '@/i18n/config'

export const ERROR_MESSAGES = {
  NETWORK_ERROR: {
    get title() { return i18n.t('errors.networkError.title') },
    get description() { return i18n.t('errors.networkError.description') },
    get action() { return i18n.t('errors.networkError.action') },
    icon: 'WifiOff'
  },
  
  UNAUTHORIZED: {
    get title() { return i18n.t('errors.unauthorized.title') },
    get description() { return i18n.t('errors.unauthorized.description') },
    get action() { return i18n.t('errors.unauthorized.action') },
    icon: 'Lock'
  },
  
  FORBIDDEN: {
    get title() { return i18n.t('errors.forbidden.title') },
    get description() { return i18n.t('errors.forbidden.description') },
    get action() { return i18n.t('errors.forbidden.action') },
    icon: 'ShieldAlert'
  },
  
  NOT_FOUND: {
    get title() { return i18n.t('errors.notFound.title') },
    get description() { return i18n.t('errors.notFound.description') },
    get action() { return i18n.t('errors.notFound.action') },
    icon: 'FileQuestion'
  },
  
  VALIDATION_ERROR: {
    get title() { return i18n.t('errors.validationError.title') },
    get description() { return i18n.t('errors.validationError.description') },
    get action() { return i18n.t('errors.validationError.action') },
    icon: 'AlertCircle'
  },
  
  SERVER_ERROR: {
    get title() { return i18n.t('errors.serverError.title') },
    get description() { return i18n.t('errors.serverError.description') },
    get action() { return i18n.t('errors.serverError.action') },
    icon: 'Server'
  },
  
  TIMEOUT_ERROR: {
    get title() { return i18n.t('errors.timeoutError.title') },
    get description() { return i18n.t('errors.timeoutError.description') },
    get action() { return i18n.t('errors.timeoutError.action') },
    icon: 'Clock'
  },
  
  RATE_LIMIT: {
    get title() { return i18n.t('errors.rateLimit.title') },
    get description() { return i18n.t('errors.rateLimit.description') },
    get action() { return i18n.t('errors.rateLimit.action') },
    icon: 'AlertTriangle'
  },
  
  UNKNOWN_ERROR: {
    get title() { return i18n.t('errors.unknownError.title') },
    get description() { return i18n.t('errors.unknownError.description') },
    get action() { return i18n.t('errors.unknownError.action') },
    icon: 'AlertCircle'
  }
}

export const getErrorMessage = (error) => {
  if (!navigator.onLine) {
    return ERROR_MESSAGES.NETWORK_ERROR
  }
  
  if (!error || !error.status) {
    return ERROR_MESSAGES.UNKNOWN_ERROR
  }
  
  const status = error.status
  
  if (status === 401) {
    return ERROR_MESSAGES.UNAUTHORIZED
  }
  
  if (status === 403) {
    return ERROR_MESSAGES.FORBIDDEN
  }
  
  if (status === 404) {
    return ERROR_MESSAGES.NOT_FOUND
  }
  
  if (status === 422 || (status >= 400 && status < 500)) {
    return ERROR_MESSAGES.VALIDATION_ERROR
  }
  
  if (status === 429) {
    return ERROR_MESSAGES.RATE_LIMIT
  }
  
  if (status === 504 || status === 408) {
    return ERROR_MESSAGES.TIMEOUT_ERROR
  }
  
  if (status >= 500) {
    return ERROR_MESSAGES.SERVER_ERROR
  }
  
  return ERROR_MESSAGES.UNKNOWN_ERROR
}

export const getErrorTitle = (error) => {
  return getErrorMessage(error).title
}

export const getErrorDescription = (error) => {
  return getErrorMessage(error).description
}

export const getErrorAction = (error) => {
  return getErrorMessage(error).action
}

export const getErrorIcon = (error) => {
  return getErrorMessage(error).icon
}

export default {
  ERROR_MESSAGES,
  getErrorMessage,
  getErrorTitle,
  getErrorDescription,
  getErrorAction,
  getErrorIcon
}
