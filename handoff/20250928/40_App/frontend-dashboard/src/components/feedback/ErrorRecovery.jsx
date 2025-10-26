import { AppleButton } from '@/components/ui/apple-button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { getErrorMessage } from '@/lib/errorMessages'
import * as Icons from 'lucide-react'
import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

export const ErrorRecovery = ({ error, onRetry, onDismiss, className = '' }) => {
  const { t } = useTranslation()
  const errorInfo = getErrorMessage(error)
  const Icon = Icons[errorInfo.icon] || Icons.AlertCircle
  
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className={className}
    >
      <Card className="max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <Icon className="w-8 h-8 text-red-600" />
          </div>
          <CardTitle>{errorInfo.title}</CardTitle>
          <CardDescription>{errorInfo.description}</CardDescription>
        </CardHeader>
        
        <CardContent>
          <div className="flex gap-3 justify-center">
            {onRetry && (
              <AppleButton onClick={onRetry}>
                {errorInfo.action}
              </AppleButton>
            )}
            {onDismiss && (
              <AppleButton variant="outline" onClick={onDismiss}>
                {t('feedback.close')}
              </AppleButton>
            )}
          </div>
          
          {error?.requestId && (
            <p className="text-xs text-gray-600 mt-4 text-center">
              {t('feedback.errorId', { id: error.requestId })}
            </p>
          )}
        </CardContent>
      </Card>
    </motion.div>
  )
}

export default ErrorRecovery
