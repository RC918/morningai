import i18n from '@/i18n/config'

export const ERROR_MESSAGES = {
  NETWORK_ERROR: {
    titleKey: 'errors.networkError.title',
    descriptionKey: 'errors.networkError.description',
    actionKey: 'errors.networkError.action',
    icon: 'WifiOff'
  },
  
  UNAUTHORIZED: {
    titleKey: 'errors.unauthorized.title',
    descriptionKey: 'errors.unauthorized.description',
    actionKey: 'errors.unauthorized.action',
    icon: 'Lock'
  },
  
  FORBIDDEN: {
    titleKey: 'errors.forbidden.title',
    descriptionKey: 'errors.forbidden.description',
    actionKey: 'errors.forbidden.action',
    icon: 'ShieldAlert'
  },
  
  NOT_FOUND: {
    titleKey: 'errors.notFound.title',
    descriptionKey: 'errors.notFound.description',
    actionKey: 'errors.notFound.action',
    icon: 'FileQuestion'
  },
  
  VALIDATION_ERROR: {
    titleKey: 'errors.validationError.title',
    descriptionKey: 'errors.validationError.description',
    actionKey: 'errors.validationError.action',
    icon: 'AlertCircle'
  },
  
  SERVER_ERROR: {
    titleKey: 'errors.serverError.title',
    descriptionKey: 'errors.serverError.description',
    actionKey: 'errors.serverError.action',
    icon: 'Server'
  },
  
  TIMEOUT_ERROR: {
    titleKey: 'errors.timeoutError.title',
    descriptionKey: 'errors.timeoutError.description',
    actionKey: 'errors.timeoutError.action',
    icon: 'Clock'
  },
  
  RATE_LIMIT: {
    titleKey: 'errors.rateLimit.title',
    descriptionKey: 'errors.rateLimit.description',
    actionKey: 'errors.rateLimit.action',
    icon: 'AlertTriangle'
  },
  
  UNKNOWN_ERROR: {
    titleKey: 'errors.unknownError.title',
    descriptionKey: 'errors.unknownError.description',
    actionKey: 'errors.unknownError.action',
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
  const message = getErrorMessage(error)
  return i18n.t(message.titleKey)
}

export const getErrorDescription = (error) => {
  const message = getErrorMessage(error)
  return i18n.t(message.descriptionKey)
}

export const getErrorAction = (error) => {
  const message = getErrorMessage(error)
  return i18n.t(message.actionKey)
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
