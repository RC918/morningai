import { useState, useCallback, useRef, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { AppleButton } from '@morningai/shared-ui'
import { 
  Send,
  Loader2,
  MessageSquare,
  Sparkles,
  ChevronUp,
  ChevronDown
} from 'lucide-react'

/**
 * SessionCommandInput - Quick command input for sending instructions to running sessions
 * 
 * Features:
 * - Send quick commands/instructions to running sessions
 * - Expandable input area for longer messages
 * - Command history navigation
 * - Loading state while command is being processed
 * - Keyboard shortcuts (Enter to send, Shift+Enter for newline)
 * 
 * Issue: #1823 - Interactive UI/UX - Session Features
 * Requirement: "產生指令或快速回答" (Quick command/response)
 */

const QUICK_COMMANDS = [
  { id: 'continue', label: 'Continue', icon: Sparkles },
  { id: 'explain', label: 'Explain current step', icon: MessageSquare },
  { id: 'skip', label: 'Skip this task', icon: ChevronDown },
  { id: 'retry', label: 'Retry last action', icon: ChevronUp }
]

const MAX_COMMAND_HISTORY = 50
const STORAGE_KEY_PREFIX = 'sessionCommandHistory'

const getStorageKey = (sessionId) => `${STORAGE_KEY_PREFIX}:${sessionId}`

const loadCommandHistory = (sessionId) => {
  try {
    const stored = localStorage.getItem(getStorageKey(sessionId))
    if (stored) {
      const parsed = JSON.parse(stored)
      if (Array.isArray(parsed)) {
        return parsed.slice(0, MAX_COMMAND_HISTORY)
      }
    }
  } catch (error) {
    console.error('Failed to load command history from localStorage:', error)
  }
  return []
}

const saveCommandHistory = (sessionId, history) => {
  try {
    const trimmed = history.slice(0, MAX_COMMAND_HISTORY)
    localStorage.setItem(getStorageKey(sessionId), JSON.stringify(trimmed))
  } catch (error) {
    console.error('Failed to save command history to localStorage:', error)
  }
}

const SessionCommandInput = ({
  sessionId,
  sessionStatus,
  onSendCommand,
  disabled = false,
  className = ''
}) => {
  const { t } = useTranslation()
  const [command, setCommand] = useState('')
  const [isExpanded, setIsExpanded] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [commandHistory, setCommandHistory] = useState(() => loadCommandHistory(sessionId))
  const [historyIndex, setHistoryIndex] = useState(-1)
  const textareaRef = useRef(null)

  const isDisabled = disabled || sessionStatus === 'completed' || sessionStatus === 'failed' || sessionStatus === 'cancelled'

  useEffect(() => {
    setCommandHistory(loadCommandHistory(sessionId))
    setHistoryIndex(-1)
  }, [sessionId])

  useEffect(() => {
    saveCommandHistory(sessionId, commandHistory)
  }, [sessionId, commandHistory])

  useEffect(() => {
    if (textareaRef.current && isExpanded) {
      textareaRef.current.focus()
    }
  }, [isExpanded])

  const handleSendCommand = useCallback(async () => {
    if (!command.trim() || isSending || isDisabled) return

    const trimmedCommand = command.trim()
    setIsSending(true)

    try {
      await onSendCommand({
        sessionId,
        command: trimmedCommand,
        timestamp: new Date().toISOString()
      })

      setCommandHistory(prev => [trimmedCommand, ...prev.slice(0, MAX_COMMAND_HISTORY - 1)])
      setCommand('')
      setHistoryIndex(-1)
      setIsExpanded(false)
    } catch (error) {
      console.error('Failed to send command:', error)
    } finally {
      setIsSending(false)
    }
  }, [command, isSending, isDisabled, sessionId, onSendCommand])

  const handleQuickCommand = useCallback(async (quickCommand) => {
    if (isSending || isDisabled) return

    setIsSending(true)

    try {
      await onSendCommand({
        sessionId,
        command: quickCommand.id,
        type: 'quick_command',
        timestamp: new Date().toISOString()
      })
    } catch (error) {
      console.error('Failed to send quick command:', error)
    } finally {
      setIsSending(false)
    }
  }, [isSending, isDisabled, sessionId, onSendCommand])

  const handleKeyDown = useCallback((e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendCommand()
    } else if (e.key === 'ArrowUp' && !command && commandHistory.length > 0) {
      e.preventDefault()
      const newIndex = Math.min(historyIndex + 1, commandHistory.length - 1)
      setHistoryIndex(newIndex)
      setCommand(commandHistory[newIndex])
    } else if (e.key === 'ArrowDown' && historyIndex >= 0) {
      e.preventDefault()
      const newIndex = historyIndex - 1
      setHistoryIndex(newIndex)
      setCommand(newIndex >= 0 ? commandHistory[newIndex] : '')
    } else if (e.key === 'Escape') {
      setIsExpanded(false)
      setCommand('')
      setHistoryIndex(-1)
    }
  }, [command, commandHistory, historyIndex, handleSendCommand])

  const handleInputChange = useCallback((e) => {
    setCommand(e.target.value)
    setHistoryIndex(-1)
  }, [])

  const toggleExpanded = useCallback(() => {
    setIsExpanded(prev => !prev)
  }, [])

  if (isDisabled) {
    return null
  }

  return (
    <div className={`border-t border-[var(--border)] bg-[var(--surface)] ${className}`}>
      {/* Quick Commands */}
      <div className="px-4 py-2 flex items-center gap-2 overflow-x-auto">
        <span className="text-xs text-[var(--text-secondary)] whitespace-nowrap">
          {t('sessions.command.quickActions', 'Quick actions:')}
        </span>
        {QUICK_COMMANDS.map((qc) => {
          const Icon = qc.icon
          return (
            <button
              key={qc.id}
              onClick={() => handleQuickCommand(qc)}
              disabled={isSending}
              className="flex items-center gap-1 px-2 py-1 text-xs rounded-full border border-[var(--border)] bg-[var(--surface-muted)] text-[var(--text-secondary)] hover:border-primary-300 hover:text-primary-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed whitespace-nowrap"
              aria-label={t(`sessions.command.quick.${qc.id}`, qc.label)}
            >
              <Icon className="w-3 h-3" />
              <span>{t(`sessions.command.quick.${qc.id}`, qc.label)}</span>
            </button>
          )
        })}
      </div>

      {/* Command Input */}
      <div className="px-4 pb-3">
        <div className="flex items-end gap-2">
          <div className="flex-1 relative">
            {isExpanded ? (
              <textarea
                ref={textareaRef}
                value={command}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                placeholder={t('sessions.command.placeholder', 'Type a command or instruction...')}
                rows={3}
                disabled={isSending}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none disabled:opacity-50"
                aria-label={t('sessions.command.inputLabel', 'Command input')}
              />
            ) : (
              <input
                type="text"
                value={command}
                onChange={handleInputChange}
                onKeyDown={handleKeyDown}
                onFocus={() => setIsExpanded(true)}
                placeholder={t('sessions.command.placeholder', 'Type a command or instruction...')}
                disabled={isSending}
                className="w-full px-3 py-2 rounded-lg border border-[var(--border)] bg-[var(--surface)] text-[var(--text-primary)] placeholder:text-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 disabled:opacity-50"
                aria-label={t('sessions.command.inputLabel', 'Command input')}
              />
            )}
            {isExpanded && (
              <button
                onClick={toggleExpanded}
                className="absolute top-2 right-2 p-1 text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                aria-label={t('sessions.command.collapse', 'Collapse input')}
              >
                <ChevronDown className="w-4 h-4" />
              </button>
            )}
          </div>
          <AppleButton
            variant="default"
            size="sm"
            haptic="medium"
            onClick={handleSendCommand}
            disabled={!command.trim() || isSending}
            aria-label={t('sessions.command.send', 'Send command')}
          >
            {isSending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </AppleButton>
        </div>
        {isExpanded && (
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {t('sessions.command.hint', 'Press Enter to send, Shift+Enter for new line, Esc to cancel')}
          </p>
        )}
      </div>
    </div>
  )
}

export default SessionCommandInput
