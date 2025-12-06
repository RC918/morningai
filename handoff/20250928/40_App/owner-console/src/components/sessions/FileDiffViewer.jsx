import { useState, useCallback, useMemo } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge } from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  FileCode,
  ChevronDown,
  ChevronRight,
  Copy,
  Check,
  ExternalLink,
  Maximize2,
  Minimize2
} from 'lucide-react'

/**
 * FileDiffViewer - Display file diffs with syntax highlighting
 * 
 * Features:
 * - Show unified diff view
 * - Line-by-line additions/deletions highlighting
 * - Expandable/collapsible sections
 * - Copy diff to clipboard
 * - Link to external IDE/editor
 * 
 * Issue: #1823
 * Phase: M5 - Meta Agent
 */

const FileDiffViewer = ({ 
  filePath = '',
  oldContent = '',
  newContent = '',
  diffLines = [],
  language = 'javascript',
  ideUrl = null,
  additions = 0,
  deletions = 0
}) => {
  const { t } = useTranslation()
  const [isExpanded, setIsExpanded] = useState(true)
  const [isFullScreen, setIsFullScreen] = useState(false)
  const [copied, setCopied] = useState(false)

  const handleCopy = useCallback(async () => {
    const diffText = diffLines.map(line => {
      if (line.type === 'addition') return `+ ${line.content}`
      if (line.type === 'deletion') return `- ${line.content}`
      return `  ${line.content}`
    }).join('\n')
    
    try {
      await navigator.clipboard.writeText(diffText)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy diff:', err)
    }
  }, [diffLines])

  const getLineClass = useCallback((type) => {
    switch (type) {
      case 'addition':
        return 'bg-growth-10 text-growth-dark'
      case 'deletion':
        return 'bg-energy-10 text-energy-dark line-through'
      case 'context':
      default:
        return 'bg-transparent text-[var(--text-secondary)]'
    }
  }, [])

  const getLinePrefix = useCallback((type) => {
    switch (type) {
      case 'addition':
        return '+'
      case 'deletion':
        return '-'
      default:
        return ' '
    }
  }, [])

  const stats = useMemo(() => ({
    additions: additions || diffLines.filter(l => l.type === 'addition').length,
    deletions: deletions || diffLines.filter(l => l.type === 'deletion').length
  }), [additions, deletions, diffLines])

  if (diffLines.length === 0) {
    return (
      <div className="text-center py-8">
        <FileCode className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
        <p className="text-sm text-[var(--text-secondary)]">
          {t('sessions.diff.noChanges', 'No changes to display')}
        </p>
      </div>
    )
  }

  return (
    <div className={`border border-[var(--border)] rounded-lg overflow-hidden ${
      isFullScreen ? 'fixed inset-4 z-50 bg-[var(--surface)]' : ''
    }`}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 bg-[var(--surface-elevated)] border-b border-[var(--border)]">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="p-1 hover:bg-[var(--surface)] rounded"
          >
            {isExpanded ? (
              <ChevronDown className="w-4 h-4 text-neutral-400" />
            ) : (
              <ChevronRight className="w-4 h-4 text-neutral-400" />
            )}
          </button>
          <FileCode className="w-4 h-4 text-neutral-500" />
          <span className="text-sm font-mono text-[var(--text-primary)]">
            {filePath}
          </span>
          <Badge variant="secondary" className="text-xs">
            {language}
          </Badge>
        </div>
        
        <div className="flex items-center gap-2">
          <span className="text-xs text-growth">+{stats.additions}</span>
          <span className="text-xs text-energy">-{stats.deletions}</span>
          
          <AppleButton
            variant="ghost"
            size="sm"
            haptic="light"
            onClick={handleCopy}
            className="ml-2"
          >
            {copied ? (
              <Check className="w-4 h-4 text-growth" />
            ) : (
              <Copy className="w-4 h-4" />
            )}
          </AppleButton>
          
          {ideUrl && (
            <AppleButton
              variant="ghost"
              size="sm"
              haptic="light"
              onClick={() => window.open(ideUrl, '_blank')}
            >
              <ExternalLink className="w-4 h-4" />
            </AppleButton>
          )}
          
          <AppleButton
            variant="ghost"
            size="sm"
            haptic="light"
            onClick={() => setIsFullScreen(!isFullScreen)}
          >
            {isFullScreen ? (
              <Minimize2 className="w-4 h-4" />
            ) : (
              <Maximize2 className="w-4 h-4" />
            )}
          </AppleButton>
        </div>
      </div>

      {/* Diff Content */}
      {isExpanded && (
        <div className={`overflow-auto ${isFullScreen ? 'h-[calc(100%-60px)]' : 'max-h-96'}`}>
          <table className="w-full text-xs font-mono">
            <tbody>
              {diffLines.map((line) => (
                <tr key={`${line.oldLineNumber || 'new'}-${line.newLineNumber || 'old'}-${line.type}`} className={getLineClass(line.type)}>
                  {/* Old Line Number */}
                  <td className="w-12 px-2 py-1 text-right text-neutral-400 select-none border-r border-[var(--border)] bg-[var(--surface-elevated)]">
                    {line.type !== 'addition' ? line.oldLineNumber : ''}
                  </td>
                  {/* New Line Number */}
                  <td className="w-12 px-2 py-1 text-right text-neutral-400 select-none border-r border-[var(--border)] bg-[var(--surface-elevated)]">
                    {line.type !== 'deletion' ? line.newLineNumber : ''}
                  </td>
                  {/* Prefix */}
                  <td className="w-6 px-1 py-1 text-center select-none">
                    <span className={line.type === 'addition' ? 'text-growth' : line.type === 'deletion' ? 'text-energy' : 'text-neutral-400'}>
                      {getLinePrefix(line.type)}
                    </span>
                  </td>
                  {/* Content */}
                  <td className="px-2 py-1 whitespace-pre">
                    {line.content}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Fullscreen Overlay Background */}
      {isFullScreen && (
        <button
          type="button"
          className="fixed inset-0 bg-black/50 -z-10 cursor-default"
          onClick={() => setIsFullScreen(false)}
          aria-label="Close fullscreen"
        />
      )}
    </div>
  )
}

export default FileDiffViewer
