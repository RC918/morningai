import { Check, Loader2, AlertCircle, XCircle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import { AppleButton } from '@/components/ui/apple-button'

const formatRelativeTime = (date, t) => {
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  
  if (diff < 60) return t('dashboard.saveStatus.timeAgo.seconds', { count: diff })
  if (diff < 3600) return t('dashboard.saveStatus.timeAgo.minutes', { count: Math.floor(diff / 60) })
  if (diff < 86400) return t('dashboard.saveStatus.timeAgo.hours', { count: Math.floor(diff / 3600) })
  return t('dashboard.saveStatus.timeAgo.days', { count: Math.floor(diff / 86400) })
}

export const SaveStatusIndicator = ({ status, lastSaved, error, onRetry }) => {
  const { t } = useTranslation()
  
  const statusConfig = {
    saved: {
      icon: Check,
      text: lastSaved 
        ? t('dashboard.saveStatus.savedWithTime', { time: formatRelativeTime(lastSaved, t) })
        : t('dashboard.saveStatus.saved'),
      className: 'text-success-600',
      iconClassName: 'text-success-600'
    },
    saving: {
      icon: Loader2,
      text: t('dashboard.saveStatus.saving'),
      className: 'text-gray-600',
      iconClassName: 'text-gray-600 animate-spin'
    },
    unsaved: {
      icon: AlertCircle,
      text: t('dashboard.saveStatus.unsaved'),
      className: 'text-warning-600',
      iconClassName: 'text-warning-600'
    },
    error: {
      icon: XCircle,
      text: error || t('dashboard.saveStatus.error'),
      className: 'text-error-600',
      iconClassName: 'text-error-600',
      action: { label: t('dashboard.saveStatus.retry'), onClick: onRetry }
    }
  }
  
  const config = statusConfig[status] || statusConfig.saved
  const Icon = config.icon
  
  return (
    <div className="flex items-center gap-2" role="status" aria-live="polite">
      <Icon 
        className={`w-4 h-4 ${config.iconClassName}`} 
        aria-hidden="true"
      />
      <span className={`text-sm ${config.className}`}>
        {config.text}
      </span>
      {config.action && (
        <AppleButton
          variant="ghost"
          size="sm"
          onClick={config.action.onClick}
          aria-label={t('dashboard.saveStatus.retryLabel')}
        >
          {config.action.label}
        </AppleButton>
      )}
    </div>
  )
}

export default SaveStatusIndicator
