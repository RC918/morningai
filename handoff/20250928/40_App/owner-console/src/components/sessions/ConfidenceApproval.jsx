import { useState, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  Badge,
  Progress
} from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  AlertTriangle,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  Minus,
  Info,
  ShieldCheck,
  ShieldAlert
} from 'lucide-react'
import { CONFIDENCE_THRESHOLD, validateConfidence } from './constants'

/**
 * ConfidenceApproval - Modal for confidence score approval workflow
 * 
 * Features:
 * - Display confidence score with visual indicator
 * - Show factors affecting confidence
 * - Allow user to approve or request changes
 * - Support for confidence threshold configuration
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const ConfidenceApproval = ({ 
  isOpen = false,
  onClose,
  onApprove,
  onRequestChanges,
  confidence = 0,
  confidenceThreshold = CONFIDENCE_THRESHOLD,
  factors = [],
  sessionTitle = '',
  currentTask = '',
  riskAssessment = null
}) => {
  const { t } = useTranslation()
  const [comment, setComment] = useState('')

  const handleApprove = useCallback(() => {
    onApprove?.({ comment: comment.trim() || null })
    setComment('')
    onClose?.()
  }, [comment, onApprove, onClose])

  const handleRequestChanges = useCallback(() => {
    onRequestChanges?.({ comment: comment.trim() || null })
    setComment('')
    onClose?.()
  }, [comment, onRequestChanges, onClose])

  // Guard clause: validate score to handle null/undefined/NaN/out-of-range values
  const getConfidenceLevel = useCallback((score) => {
    const validScore = validateConfidence(score)
    if (validScore >= 0.9) return { level: 'high', color: 'text-growth', bgColor: 'bg-growth-10', label: t('sessions.confidenceLevel.high', 'High') }
    if (validScore >= 0.7) return { level: 'medium', color: 'text-wisdom', bgColor: 'bg-wisdom-10', label: t('sessions.confidenceLevel.medium', 'Medium') }
    return { level: 'low', color: 'text-energy', bgColor: 'bg-energy-10', label: t('sessions.confidenceLevel.low', 'Low') }
  }, [t])

  const getFactorIcon = useCallback((trend) => {
    switch (trend) {
      case 'positive':
        return <TrendingUp className="w-4 h-4 text-growth" />
      case 'negative':
        return <TrendingDown className="w-4 h-4 text-energy" />
      default:
        return <Minus className="w-4 h-4 text-neutral-400" />
    }
  }, [])

  const getRiskIcon = useCallback((level) => {
    switch (level) {
      case 'high':
        return <ShieldAlert className="w-5 h-5 text-energy" />
      case 'medium':
        return <AlertTriangle className="w-5 h-5 text-wisdom" />
      default:
        return <ShieldCheck className="w-5 h-5 text-growth" />
    }
  }, [])

  const confidenceLevel = getConfidenceLevel(confidence)
  const confidencePercent = Math.round(confidence * 100)
  const meetsThreshold = confidence >= confidenceThreshold

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[500px]">
        <DialogHeader>
          <DialogTitle>
            {t('sessions.confidenceApproval.title', 'Confidence Review')}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {/* Session Info */}
          <div className="p-3 rounded-lg bg-[var(--surface-elevated)] border border-[var(--border)]">
            <p className="text-sm font-medium text-[var(--text-primary)]">{sessionTitle}</p>
            {currentTask && (
              <p className="text-xs text-[var(--text-secondary)] mt-1">
                {t('sessions.confidenceApproval.currentTask', 'Current Task')}: {currentTask}
              </p>
            )}
          </div>

          {/* Confidence Score */}
          <div className={`p-4 rounded-lg ${confidenceLevel.bgColor} border border-[var(--border)]`}>
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm font-medium text-[var(--text-primary)]">
                {t('sessions.confidenceApproval.score', 'Confidence Score')}
              </span>
              <Badge variant={meetsThreshold ? 'success' : 'warning'} className="text-xs">
                {meetsThreshold ? (
                  <>
                    <CheckCircle className="w-3 h-3" />
                    <span>{t('sessions.confidenceApproval.meetsThreshold', 'Meets Threshold')}</span>
                  </>
                ) : (
                  <>
                    <AlertTriangle className="w-3 h-3" />
                    <span>{t('sessions.confidenceApproval.belowThreshold', 'Below Threshold')}</span>
                  </>
                )}
              </Badge>
            </div>
            
            <div className="flex items-center gap-4">
              <div className={`text-3xl font-bold ${confidenceLevel.color}`}>
                {confidencePercent}%
              </div>
              <div className="flex-1">
                <Progress value={confidencePercent} className="h-3" />
                <div className="flex items-center justify-between mt-1">
                  <span className="text-xs text-[var(--text-secondary)]">0%</span>
                  <span className="text-xs text-[var(--text-secondary)]">
                    {t('sessions.confidenceApproval.threshold', 'Threshold')}: {Math.round(confidenceThreshold * 100)}%
                  </span>
                  <span className="text-xs text-[var(--text-secondary)]">100%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Risk Assessment */}
          {riskAssessment && (
            <div className="p-3 rounded-lg border border-[var(--border)]">
              <div className="flex items-start gap-3">
                {getRiskIcon(riskAssessment.level)}
                <div>
                  <p className="text-sm font-medium text-[var(--text-primary)]">
                    {t('sessions.confidenceApproval.riskLevel', 'Risk Level')}: {riskAssessment.level}
                  </p>
                  {riskAssessment.description && (
                    <p className="text-xs text-[var(--text-secondary)] mt-1">
                      {riskAssessment.description}
                    </p>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Confidence Factors */}
          {factors.length > 0 && (
            <div className="border border-[var(--border)] rounded-lg overflow-hidden">
              <div className="px-4 py-2 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
                <h4 className="text-sm font-medium text-[var(--text-primary)]">
                  {t('sessions.confidenceApproval.factors', 'Contributing Factors')}
                </h4>
              </div>
              <div className="divide-y divide-[var(--border)]">
                {factors.map((factor) => (
                  <div key={factor.name || factor.id} className="px-4 py-3 flex items-start gap-3">
                    {getFactorIcon(factor.trend)}
                    <div className="flex-1">
                      <p className="text-sm text-[var(--text-primary)]">{factor.name}</p>
                      {factor.description && (
                        <p className="text-xs text-[var(--text-secondary)] mt-1">
                          {factor.description}
                        </p>
                      )}
                    </div>
                    {factor.impact && (
                      <span className={`text-xs font-medium ${
                        factor.trend === 'positive' ? 'text-growth' : 
                        factor.trend === 'negative' ? 'text-energy' : 'text-neutral-500'
                      }`}>
                        {factor.trend === 'positive' ? '+' : ''}{factor.impact}%
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Info Banner */}
          {!meetsThreshold && (
            <div className="p-3 rounded-lg bg-wisdom-10 border border-wisdom">
              <div className="flex items-start gap-2">
                <Info className="w-4 h-4 text-wisdom flex-shrink-0 mt-1" />
                <p className="text-xs text-wisdom-dark">
                  {t('sessions.confidenceApproval.lowConfidenceWarning', 
                    'The confidence score is below the threshold. Review the factors above and consider requesting changes if needed.'
                  )}
                </p>
              </div>
            </div>
          )}

          {/* Comment */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-[var(--text-primary)]">
              {t('sessions.confidenceApproval.comment', 'Comment')}
              <span className="text-neutral-400 ml-1 text-xs">
                ({t('common.optional', 'optional')})
              </span>
            </label>
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t('sessions.confidenceApproval.commentPlaceholder', 'Add any notes or feedback...')}
              rows={2}
              className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none text-sm"
            />
          </div>
        </div>

        <DialogFooter className="flex items-center justify-end gap-2">
          <AppleButton
            variant="outline"
            size="sm"
            haptic="light"
            onClick={handleRequestChanges}
          >
            <XCircle className="w-4 h-4 mr-1" />
            {t('sessions.confidenceApproval.requestChanges', 'Request Changes')}
          </AppleButton>
          <AppleButton
            variant="default"
            size="sm"
            haptic="medium"
            onClick={handleApprove}
          >
            <CheckCircle className="w-4 h-4 mr-1" />
            {t('sessions.confidenceApproval.approve', 'Approve & Continue')}
          </AppleButton>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default ConfidenceApproval
