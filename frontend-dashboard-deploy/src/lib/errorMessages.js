export const ERROR_MESSAGES = {
  NETWORK_ERROR: {
    title: '網路連線問題',
    description: '無法連接到伺服器，請檢查您的網路連線',
    action: '重試',
    icon: 'WifiOff'
  },
  
  UNAUTHORIZED: {
    title: '未授權訪問',
    description: '您的登入已過期，請重新登入',
    action: '重新登入',
    icon: 'Lock'
  },
  
  FORBIDDEN: {
    title: '權限不足',
    description: '您沒有權限執行此操作',
    action: '返回',
    icon: 'ShieldAlert'
  },
  
  NOT_FOUND: {
    title: '找不到資源',
    description: '您請求的資源不存在或已被移除',
    action: '返回首頁',
    icon: 'FileQuestion'
  },
  
  VALIDATION_ERROR: {
    title: '資料驗證失敗',
    description: '請檢查您輸入的資料是否正確',
    action: '返回修改',
    icon: 'AlertCircle'
  },
  
  SERVER_ERROR: {
    title: '伺服器錯誤',
    description: '伺服器暫時無法處理您的請求，我們正在處理',
    action: '稍後重試',
    icon: 'Server'
  },
  
  TIMEOUT_ERROR: {
    title: '請求超時',
    description: '伺服器響應時間過長，請稍後再試',
    action: '重試',
    icon: 'Clock'
  },
  
  RATE_LIMIT: {
    title: '請求過於頻繁',
    description: '您的請求次數已達上限，請稍後再試',
    action: '稍後重試',
    icon: 'AlertTriangle'
  },
  
  UNKNOWN_ERROR: {
    title: '發生錯誤',
    description: '發生未知錯誤，請稍後再試',
    action: '重試',
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
