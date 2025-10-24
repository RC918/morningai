import { Check, Loader2, AlertCircle, XCircle } from 'lucide-react'
import { Button } from '@/components/ui/button'

const formatRelativeTime = (date) => {
  const now = new Date()
  const diff = Math.floor((now - date) / 1000)
  
  if (diff < 60) return `${diff}秒前`
  if (diff < 3600) return `${Math.floor(diff / 60)}分鐘前`
  if (diff < 86400) return `${Math.floor(diff / 3600)}小時前`
  return `${Math.floor(diff / 86400)}天前`
}

export const SaveStatusIndicator = ({ status, lastSaved, error, onRetry }) => {
  const statusConfig = {
    saved: {
      icon: Check,
      text: lastSaved ? `已保存 · ${formatRelativeTime(lastSaved)}` : '已保存',
      className: 'text-success-600',
      iconClassName: 'text-success-600'
    },
    saving: {
      icon: Loader2,
      text: '保存中...',
      className: 'text-gray-600',
      iconClassName: 'text-gray-600 animate-spin'
    },
    unsaved: {
      icon: AlertCircle,
      text: '有未保存的變更',
      className: 'text-warning-600',
      iconClassName: 'text-warning-600'
    },
    error: {
      icon: XCircle,
      text: error || '保存失敗',
      className: 'text-error-600',
      iconClassName: 'text-error-600',
      action: { label: '重試', onClick: onRetry }
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
        <Button
          variant="ghost"
          size="sm"
          onClick={config.action.onClick}
          aria-label="重試保存"
        >
          {config.action.label}
        </Button>
      )}
    </div>
  )
}

export default SaveStatusIndicator
