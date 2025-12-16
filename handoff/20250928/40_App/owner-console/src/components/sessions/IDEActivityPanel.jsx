import { useState, useCallback, useMemo, useEffect, useRef } from 'react'
import { useTranslation } from 'react-i18next'
import { Badge, SectionCard } from '@morningai/shared-ui'
import { AppleButton } from '@/components/apple/apple-button'
import { 
  FileCode,
  FolderOpen,
  ExternalLink,
  Eye,
  Clock,
  Edit3,
  FileText,
  ChevronRight,
  Activity,
  Monitor
} from 'lucide-react'

/**
 * IDEActivityPanel - Real-time IDE activity display for session monitoring
 * 
 * Features:
 * - Show currently active file being edited
 * - Display recent file changes with timestamps
 * - Visual feedback for new file activity (highlight animation)
 * - "Open in IDE" button when IDE URL is available
 * - File navigation/selection
 * 
 * Issue: #2241 - Real-time IDE sync UI for session task execution
 * Phase: M5 - Meta Agent
 */

const IDEActivityPanel = ({ 
  ideActivity = {},
  onFileSelect = null,
  className = ''
}) => {
  const { t } = useTranslation()
  const [selectedFile, setSelectedFile] = useState(null)
  const [highlightedFiles, setHighlightedFiles] = useState(new Set())
  const prevFilesRef = useRef([])

  const { 
    activeFile = null, 
    recentFiles = [], 
    ideUrl = null,
    hasIdeSession = false 
  } = ideActivity

  // Detect newly added files and highlight them
  useEffect(() => {
    const prevPaths = new Set(prevFilesRef.current.map(f => f.path))
    const newFiles = recentFiles.filter(f => !prevPaths.has(f.path))
    
    if (newFiles.length > 0) {
      const newPaths = new Set(newFiles.map(f => f.path))
      setHighlightedFiles(newPaths)
      
      // Remove highlight after animation
      const timer = setTimeout(() => {
        setHighlightedFiles(new Set())
      }, 2000)
      
      return () => clearTimeout(timer)
    }
    
    prevFilesRef.current = recentFiles
  }, [recentFiles])

  const handleFileClick = useCallback((file) => {
    setSelectedFile(file.path)
    if (onFileSelect) {
      onFileSelect(file)
    }
  }, [onFileSelect])

  const handleOpenIDE = useCallback(() => {
    if (ideUrl) {
      window.open(ideUrl, '_blank', 'noopener,noreferrer')
    }
  }, [ideUrl])

  const formatTimestamp = useCallback((timestamp) => {
    if (!timestamp) return ''
    try {
      const date = new Date(timestamp)
      const now = new Date()
      const diffMs = now - date
      const diffMins = Math.floor(diffMs / 60000)
      
      if (diffMins < 1) return t('sessions.ide.justNow', 'just now')
      if (diffMins < 60) return t('sessions.ide.minsAgo', '{{mins}}m ago', { mins: diffMins })
      
      const diffHours = Math.floor(diffMins / 60)
      if (diffHours < 24) return t('sessions.ide.hoursAgo', '{{hours}}h ago', { hours: diffHours })
      
      return date.toLocaleDateString()
    } catch {
      return ''
    }
  }, [t])

  const getFileIcon = useCallback((file) => {
    const ext = file.path?.split('.').pop()?.toLowerCase()
    
    // Return appropriate icon based on file extension
    switch (ext) {
      case 'py':
      case 'js':
      case 'jsx':
      case 'ts':
      case 'tsx':
        return <FileCode className="w-4 h-4 text-[var(--accent)]" />
      case 'json':
      case 'yaml':
      case 'yml':
        return <FileText className="w-4 h-4 text-amber-500" />
      case 'md':
        return <FileText className="w-4 h-4 text-neutral-500" />
      default:
        return <FileText className="w-4 h-4 text-neutral-400" />
    }
  }, [])

  const getActionBadge = useCallback((action) => {
    switch (action) {
      case 'modified':
        return (
          <Badge variant="secondary" className="text-xs bg-growth-10 text-growth-dark">
            {t('sessions.ide.modified', 'modified')}
          </Badge>
        )
      case 'created':
        return (
          <Badge variant="secondary" className="text-xs bg-[var(--accent-10)] text-[var(--accent)]">
            {t('sessions.ide.created', 'created')}
          </Badge>
        )
      case 'read':
        return (
          <Badge variant="secondary" className="text-xs bg-neutral-100 text-neutral-600">
            {t('sessions.ide.read', 'read')}
          </Badge>
        )
      default:
        return null
    }
  }, [t])

  const getFileName = useCallback((path) => {
    if (!path) return ''
    const parts = path.split('/')
    return parts[parts.length - 1]
  }, [])

  const getFilePath = useCallback((path) => {
    if (!path) return ''
    const parts = path.split('/')
    if (parts.length <= 1) return ''
    return parts.slice(0, -1).join('/')
  }, [])

  // Empty state when no IDE activity
  if (!activeFile && recentFiles.length === 0) {
    return (
      <SectionCard className={className}>
        <div className="text-center py-8">
          <Monitor className="w-12 h-12 text-neutral-300 mx-auto mb-3" />
          <p className="text-sm text-[var(--text-secondary)]">
            {t('sessions.ide.noActivity', 'No IDE activity yet')}
          </p>
          <p className="text-xs text-neutral-400 mt-1">
            {t('sessions.ide.noActivityHint', 'File changes will appear here as the agent works')}
          </p>
        </div>
      </SectionCard>
    )
  }

  return (
    <SectionCard className={className}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Activity className="w-5 h-5 text-[var(--accent)]" />
          <h3 className="text-sm font-semibold text-[var(--text-primary)]">
            {t('sessions.ide.title', 'IDE Activity')}
          </h3>
          {hasIdeSession && (
            <Badge variant="secondary" className="text-xs bg-growth-10 text-growth-dark">
              {t('sessions.ide.live', 'Live')}
            </Badge>
          )}
        </div>
        
        {ideUrl && (
          <AppleButton
            variant="secondary"
            size="sm"
            haptic="light"
            onClick={handleOpenIDE}
            className="gap-1"
          >
            <ExternalLink className="w-3.5 h-3.5" />
            {t('sessions.ide.openIDE', 'Open IDE')}
          </AppleButton>
        )}
      </div>

      {/* Active File */}
      {activeFile && (
        <div className="mb-4 p-3 bg-[var(--surface-elevated)] rounded-lg border border-[var(--border)]">
          <div className="flex items-center gap-2 mb-1">
            <Eye className="w-4 h-4 text-[var(--accent)]" />
            <span className="text-xs font-medium text-[var(--text-secondary)]">
              {t('sessions.ide.currentlyEditing', 'Currently Editing')}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <FileCode className="w-4 h-4 text-[var(--accent)]" />
            <span className="text-sm font-mono text-[var(--text-primary)] truncate">
              {activeFile}
            </span>
          </div>
        </div>
      )}

      {/* Recent Files */}
      {recentFiles.length > 0 && (
        <div>
          <div className="flex items-center gap-2 mb-2">
            <FolderOpen className="w-4 h-4 text-neutral-500" />
            <span className="text-xs font-medium text-[var(--text-secondary)]">
              {t('sessions.ide.recentFiles', 'Recent Files')} ({recentFiles.length})
            </span>
          </div>
          
          <div className="space-y-1 max-h-64 overflow-y-auto">
            {recentFiles.map((file, index) => {
              const isHighlighted = highlightedFiles.has(file.path)
              const isSelected = selectedFile === file.path
              
              return (
                <button
                  key={`${file.path}-${index}`}
                  type="button"
                  onClick={() => handleFileClick(file)}
                  className={`
                    w-full flex items-center gap-2 p-2 rounded-md text-left
                    transition-all duration-200
                    ${isSelected 
                      ? 'bg-[var(--accent-10)] border border-[var(--accent)]' 
                      : 'hover:bg-[var(--surface-elevated)] border border-transparent'
                    }
                    ${isHighlighted ? 'animate-pulse bg-growth-10' : ''}
                  `}
                >
                  {getFileIcon(file)}
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono text-[var(--text-primary)] truncate">
                        {getFileName(file.path)}
                      </span>
                      {getActionBadge(file.action)}
                    </div>
                    {getFilePath(file.path) && (
                      <span className="text-xs text-neutral-400 truncate block">
                        {getFilePath(file.path)}
                      </span>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-1 text-xs text-neutral-400">
                    <Clock className="w-3 h-3" />
                    {formatTimestamp(file.timestamp)}
                  </div>
                  
                  <ChevronRight className="w-4 h-4 text-neutral-300" />
                </button>
              )
            })}
          </div>
        </div>
      )}

      {/* IDE Session Info */}
      {hasIdeSession && !ideUrl && (
        <div className="mt-4 p-2 bg-amber-50 rounded-md border border-amber-200">
          <p className="text-xs text-amber-700">
            {t('sessions.ide.noPublicUrl', 'IDE session is active but no public URL is configured')}
          </p>
        </div>
      )}
    </SectionCard>
  )
}

export default IDEActivityPanel
