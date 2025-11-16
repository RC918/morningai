import { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { 
  Card, 
  CardContent, 
  CardDescription, 
  CardHeader, 
  CardTitle, 
  Badge, 
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Alert,
  AlertDescription,
  AlertTitle,
  StatusBadge,
  StatusBadgeProps,
  Pagination,
  PaginationContent,
  PaginationItem,
  PaginationPrevious,
  PaginationNext,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
  Skeleton
} from '@morningai/shared-ui'
import { 
  Filter,
  RefreshCw,
  Activity,
  CheckCircle,
  Clock,
  AlertTriangle
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

interface ExecutionLogAgent {
  agent_type?: string
  reputation_score?: number
}

interface ExecutionLogTimestamps {
  created_at?: string
  started_at?: string
  completed_at?: string
  updated_at?: string
}

interface ExecutionLog {
  task_id: string
  status: string
  task_type?: string
  agent?: ExecutionLogAgent
  tenant_id?: string
  duration_ms?: number
  timestamps?: ExecutionLogTimestamps
  error_message?: string
}

interface ExecutionSummary {
  total_executions: number
  success_rate?: number
  avg_duration_ms?: number
  status_counts?: Record<string, number>
}

interface PaginationState {
  page: number
  page_size: number
  total_items: number
  total_pages: number
}

interface FiltersState {
  status: string
  agent_id: string
  tenant_id: string
  task_type: string
  start_date: string
  end_date: string
  sort_by: string
  sort_order: string
}

interface ExecutionLogsResponse {
  execution_logs: ExecutionLog[]
  summary: ExecutionSummary
  pagination: {
    total_items: number
    total_pages: number
  }
}

const warnedStatuses = new Set<string>()

/**
 * Normalize backend execution log status to StatusBadge variants
 * Handles common synonyms and case variations
 */
export const normalizeExecutionLogStatus = (
  status: string | undefined
): { normalized: StatusBadgeProps['status']; isKnown: boolean } => {
  if (!status) {
    return { normalized: 'queued', isKnown: false }
  }

  const normalized = status.toLowerCase().trim()

  const statusMap: Record<string, StatusBadgeProps['status']> = {
    'completed': 'completed',
    'success': 'completed',
    'succeeded': 'completed',
    'done': 'completed',
    'finished': 'completed',
    
    'running': 'running',
    'in_progress': 'running',
    'in-progress': 'running',
    'processing': 'running',
    'active': 'running',
    'executing': 'running',
    
    'failed': 'failed',
    'error': 'failed',
    'errored': 'failed',
    'exception': 'failed',
    'crashed': 'failed',
    
    'queued': 'queued',
    'pending': 'queued',
    'waiting': 'queued',
    
    'assigned': 'assigned',
    'scheduled': 'assigned',
    
    'cancelled': 'cancelled',
    'canceled': 'cancelled',
    'aborted': 'cancelled',
    'terminated': 'cancelled',
  }

  const mappedStatus = statusMap[normalized]
  
  if (!mappedStatus) {
    if (!warnedStatuses.has(normalized)) {
      console.warn(`[AgentExecutionLogs] Unknown execution log status: "${status}". Defaulting to "queued". Please add mapping if this is a valid status.`)
      warnedStatuses.add(normalized)
    }
    return { normalized: 'queued', isKnown: false }
  }

  return { normalized: mappedStatus, isKnown: true }
}

const AgentExecutionLogs = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [logs, setLogs] = useState<ExecutionLog[]>([])
  const [summary, setSummary] = useState<ExecutionSummary | null>(null)
  const [pagination, setPagination] = useState<PaginationState>({ 
    page: 1, 
    page_size: 50, 
    total_items: 0, 
    total_pages: 0 
  })
  
  const [filters, setFilters] = useState<FiltersState>({
    status: '',
    agent_id: '',
    tenant_id: '',
    task_type: '',
    start_date: '',
    end_date: '',
    sort_by: 'created_at',
    sort_order: 'desc'
  })

  useEffect(() => {
    loadExecutionLogs()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pagination.page, filters.sort_by, filters.sort_order])

  const loadExecutionLogs = async () => {
    try {
      setLoading(true)
      setError(null)
      
      const params = new URLSearchParams({
        page: pagination.page.toString(),
        page_size: pagination.page_size.toString(),
        sort_by: filters.sort_by,
        sort_order: filters.sort_order
      })
      
      if (filters.status) params.append('status', filters.status)
      if (filters.agent_id) params.append('agent_id', filters.agent_id)
      if (filters.tenant_id) params.append('tenant_id', filters.tenant_id)
      if (filters.task_type) params.append('task_type', filters.task_type)
      if (filters.start_date) params.append('start_date', filters.start_date)
      if (filters.end_date) params.append('end_date', filters.end_date)

      const response = await apiClient(`/admin/agent-execution-logs?${params.toString()}`) as ExecutionLogsResponse
      
      if (response.execution_logs) {
        setLogs(response.execution_logs)
        setSummary(response.summary)
        setPagination(prev => ({
          ...prev,
          total_items: response.pagination.total_items,
          total_pages: response.pagination.total_pages
        }))
      }
    } catch (err) {
      console.error('Failed to load execution logs:', err)
      setError((err as Error).message || 'Failed to load execution logs')
    } finally {
      setLoading(false)
    }
  }

  const handleApplyFilters = () => {
    setPagination(prev => ({ ...prev, page: 1 }))
    loadExecutionLogs()
  }

  const handleClearFilters = () => {
    setFilters({
      status: '',
      agent_id: '',
      tenant_id: '',
      task_type: '',
      start_date: '',
      end_date: '',
      sort_by: 'created_at',
      sort_order: 'desc'
    })
    setPagination(prev => ({ ...prev, page: 1 }))
  }

  const formatDuration = (durationMs: number | undefined): string => {
    if (!durationMs) return t('common.na')
    const seconds = Math.floor(durationMs / 1000)
    const minutes = Math.floor(seconds / 60)
    const hours = Math.floor(minutes / 60)
    
    if (hours > 0) {
      return `${hours}h ${minutes % 60}m`
    } else if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`
    } else {
      return `${seconds}s`
    }
  }

  const formatTimestamp = (timestamp: string | undefined): string => {
    if (!timestamp) return t('common.na')
    return new Date(timestamp).toLocaleString()
  }

  const handlePageChange = (newPage: number) => {
    setPagination(prev => ({ ...prev, page: newPage }))
  }

  const isEmptyValue = (value: any): boolean => {
    if (value == null) return true
    if (Array.isArray(value)) return value.length === 0
    if (typeof value === 'object') return Object.keys(value).length === 0
    return false
  }

  const showSkeleton = loading && logs.length === 0

  if (showSkeleton) {
    return (
      <div className="space-y-6" role="status" aria-live="polite" aria-busy="true" aria-label={t('common.loading')}>
        {/* Summary Statistics Skeleton */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Card key={i}>
              <CardContent className="pt-6">
                <div className="flex items-center justify-between mb-2">
                  <Skeleton className="h-4 w-24" aria-hidden="true" />
                  <Skeleton className="h-5 w-5 rounded-full" aria-hidden="true" />
                </div>
                <Skeleton className="h-9 w-20" aria-hidden="true" />
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filters Skeleton */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-32" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3, 4, 5, 6].map((i) => (
                <div key={i}>
                  <Skeleton className="h-4 w-20 mb-2" aria-hidden="true" />
                  <Skeleton className="h-10 w-full" aria-hidden="true" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Table Skeleton */}
        <Card>
          <CardHeader>
            <Skeleton className="h-6 w-48" aria-hidden="true" />
            <Skeleton className="h-4 w-64 mt-2" aria-hidden="true" />
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="h-6 w-20" aria-hidden="true" />
                  <Skeleton className="h-4 w-32" aria-hidden="true" />
                  <Skeleton className="h-4 w-24" aria-hidden="true" />
                  <Skeleton className="h-4 w-28" aria-hidden="true" />
                  <Skeleton className="h-4 w-32" aria-hidden="true" />
                  <Skeleton className="h-4 w-16" aria-hidden="true" />
                  <Skeleton className="h-4 w-36" aria-hidden="true" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6" aria-busy={loading}>
      {error && (
        <Alert variant="destructive">
          <AlertTriangle className="h-4 w-4" />
          <AlertTitle>{t('common.error')}</AlertTitle>
          <AlertDescription>
            {error}
            <Button 
              onClick={loadExecutionLogs} 
              variant="outline" 
              size="sm" 
              className="ml-4"
              aria-label={t('governance.executionLogs.retryLoad', { defaultValue: 'Retry loading execution logs' })}
            >
              {t('common.retry')}
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Summary Statistics */}
      {summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.totalExecutions')}</p>
                <Activity className="w-5 h-5 text-primary-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                {summary.total_executions || 0}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.successRate')}</p>
                <CheckCircle className="w-5 h-5 text-success-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                {summary.success_rate ? `${(summary.success_rate * 100).toFixed(1)}%` : t('common.na')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.avgDuration')}</p>
                <Clock className="w-5 h-5 text-accent-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-white">
                {formatDuration(summary.avg_duration_ms)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.summary.statusBreakdown')}</p>
                <Filter className="w-5 h-5 text-neutral-600" />
              </div>
              <div className="space-y-1">
                {summary.status_counts && Object.entries(summary.status_counts).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between text-sm">
                    <span className="text-neutral-600 dark:text-neutral-400">{t(`governance.executionLogs.statuses.${status}`)}</span>
                    <span className="font-semibold">{count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-5 h-5" />
            {t('common.filter')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.status')}
              </label>
              <Select 
                value={filters.status} 
                onValueChange={(value) => setFilters(prev => ({ ...prev, status: value }))}
              >
                <SelectTrigger>
                  <SelectValue placeholder={t('governance.executionLogs.filters.allStatuses')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">{t('governance.executionLogs.filters.allStatuses')}</SelectItem>
                  <SelectItem value="queued">{t('governance.executionLogs.statuses.queued')}</SelectItem>
                  <SelectItem value="assigned">{t('governance.executionLogs.statuses.assigned')}</SelectItem>
                  <SelectItem value="running">{t('governance.executionLogs.statuses.running')}</SelectItem>
                  <SelectItem value="completed">{t('governance.executionLogs.statuses.completed')}</SelectItem>
                  <SelectItem value="failed">{t('governance.executionLogs.statuses.failed')}</SelectItem>
                  <SelectItem value="cancelled">{t('governance.executionLogs.statuses.cancelled')}</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.agentId')}
              </label>
              <Input
                value={filters.agent_id}
                onChange={(e) => setFilters(prev => ({ ...prev, agent_id: e.target.value }))}
                placeholder={t('governance.executionLogs.filters.agentIdPlaceholder')}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.taskType')}
              </label>
              <Input
                value={filters.task_type}
                onChange={(e) => setFilters(prev => ({ ...prev, task_type: e.target.value }))}
                placeholder={t('governance.executionLogs.filters.taskTypePlaceholder')}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.startDate')}
              </label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-neutral-700 dark:text-neutral-300 mb-1 block">
                {t('governance.executionLogs.filters.endDate')}
              </label>
              <Input
                type="date"
                value={filters.end_date}
                onChange={(e) => setFilters(prev => ({ ...prev, end_date: e.target.value }))}
              />
            </div>

            <div className="flex items-end gap-2">
              <Button onClick={handleApplyFilters} className="flex-1">
                {t('governance.executionLogs.filters.applyFilters')}
              </Button>
              <Button onClick={handleClearFilters} variant="outline">
                {t('governance.executionLogs.filters.clearFilters')}
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Execution Logs */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>{t('governance.executionLogs.title')}</CardTitle>
              <CardDescription>{t('governance.executionLogs.subtitle')}</CardDescription>
            </div>
            <Button onClick={loadExecutionLogs} variant="outline" size="sm" disabled={loading}>
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              {t('governance.refresh')}
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          {logs.length === 0 && !loading ? (
            <div className="text-center py-8" role="region" aria-labelledby="empty-logs-title">
              <p id="empty-logs-title" className="text-neutral-500">{t('governance.executionLogs.noLogs')}</p>
            </div>
          ) : (
            <>
              {/* Desktop Table View (md and up) */}
              <div className="hidden md:block">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>{t('governance.executionLogs.columns.status')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.taskId')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.taskType')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.agent')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.tenant')}</TableHead>
                      <TableHead>{t('governance.executionLogs.columns.duration')}</TableHead>
                      <TableHead>{t('governance.executionLogs.details.createdAt')}</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {logs.map((log) => {
                      const { normalized: normalizedStatus, isKnown } = normalizeExecutionLogStatus(log.status)
                      return (
                        <TableRow key={log.task_id}>
                          <TableCell>
                            <StatusBadge status={normalizedStatus} showIcon>
                              {isKnown 
                                ? t(`governance.executionLogs.statuses.${normalizedStatus}`)
                                : t('governance.executionLogs.statuses.unknown', { defaultValue: 'Unknown' })
                              }
                            </StatusBadge>
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {log.task_id?.substring(0, 12)}...
                          </TableCell>
                          <TableCell>
                            {log.task_type ? (
                              <Badge variant="outline" className="text-xs">
                                {log.task_type}
                              </Badge>
                            ) : (
                              <span className="text-neutral-400">{t('common.na')}</span>
                            )}
                          </TableCell>
                          <TableCell>
                            {log.agent ? (
                              <div>
                                <p className="font-medium text-sm">{log.agent.agent_type || t('common.na')}</p>
                                {log.agent.reputation_score !== undefined && (
                                  <p className="text-xs text-neutral-500">
                                    {t('governance.agents.reputation')}: {log.agent.reputation_score}
                                  </p>
                                )}
                              </div>
                            ) : (
                              <span className="text-neutral-400">{t('common.na')}</span>
                            )}
                          </TableCell>
                          <TableCell className="font-mono text-xs">
                            {log.tenant_id ? `${log.tenant_id.substring(0, 12)}...` : t('common.na')}
                          </TableCell>
                          <TableCell className="font-medium">
                            {formatDuration(log.duration_ms)}
                          </TableCell>
                          <TableCell className="text-xs">
                            {formatTimestamp(log.timestamps?.created_at)}
                          </TableCell>
                        </TableRow>
                      )
                    })}
                  </TableBody>
                </Table>
              </div>

              {/* Mobile Card View (below md) */}
              <div className="md:hidden space-y-3">
                {logs.map((log) => {
                  const { normalized: normalizedStatus, isKnown } = normalizeExecutionLogStatus(log.status)
                  return (
                    <div key={log.task_id} className="border rounded-lg p-4 hover:bg-neutral-50 dark:hover:bg-neutral-800 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <StatusBadge status={normalizedStatus} showIcon>
                              {isKnown 
                                ? t(`governance.executionLogs.statuses.${normalizedStatus}`)
                                : t('governance.executionLogs.statuses.unknown', { defaultValue: 'Unknown' })
                              }
                            </StatusBadge>
                            <span className="text-sm font-mono text-neutral-600 dark:text-neutral-400">
                              {log.task_id?.substring(0, 12)}...
                            </span>
                            {log.task_type && (
                              <Badge variant="outline" className="text-xs">
                                {log.task_type}
                              </Badge>
                            )}
                          </div>
                          
                          <div className="grid grid-cols-2 gap-4 text-sm">
                            {log.agent && (
                              <div>
                                <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.columns.agent')}</p>
                                <p className="font-medium">{log.agent.agent_type || t('common.na')}</p>
                                {log.agent.reputation_score !== undefined && (
                                  <p className="text-xs text-neutral-500">
                                    {t('governance.agents.reputation')}: {log.agent.reputation_score}
                                  </p>
                                )}
                              </div>
                            )}
                            
                            {log.tenant_id && (
                              <div>
                                <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.columns.tenant')}</p>
                                <p className="font-medium font-mono text-xs">{log.tenant_id.substring(0, 12)}...</p>
                              </div>
                            )}
                            
                            <div>
                              <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.columns.duration')}</p>
                              <p className="font-medium">{formatDuration(log.duration_ms)}</p>
                            </div>
                            
                            <div>
                              <p className="text-neutral-600 dark:text-neutral-400">{t('governance.executionLogs.details.createdAt')}</p>
                              <p className="font-medium text-xs">{formatTimestamp(log.timestamps?.created_at)}</p>
                            </div>
                          </div>

                          {log.error_message && (
                            <div className="mt-3 p-2 bg-error-50 dark:bg-error-900/20 border border-error-200 dark:border-error-800 rounded text-sm text-error-800 dark:text-error-400">
                              <p className="font-semibold">{t('governance.executionLogs.details.errorMessage')}:</p>
                              <p className="text-xs mt-1">{log.error_message}</p>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  )
                })}
              </div>
            </>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <p className="text-sm text-neutral-600 dark:text-neutral-400">
                {t('governance.executionLogs.pagination.showing', {
                  start: (pagination.page - 1) * pagination.page_size + 1,
                  end: Math.min(pagination.page * pagination.page_size, pagination.total_items),
                  total: pagination.total_items
                })}
              </p>
              <Pagination>
                <PaginationContent>
                  <PaginationItem>
                    <PaginationPrevious 
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (pagination.page > 1) {
                          handlePageChange(pagination.page - 1)
                        }
                      }}
                      onKeyDown={(e) => {
                        if (pagination.page === 1 && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault()
                        }
                      }}
                      aria-disabled={pagination.page === 1}
                      tabIndex={pagination.page === 1 ? -1 : 0}
                      className={pagination.page === 1 ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                  <PaginationItem>
                    <span className="text-sm text-neutral-600 dark:text-neutral-400 px-4">
                      {t('governance.executionLogs.pagination.page', {
                        current: pagination.page,
                        total: pagination.total_pages
                      })}
                    </span>
                  </PaginationItem>
                  <PaginationItem>
                    <PaginationNext 
                      href="#"
                      onClick={(e) => {
                        e.preventDefault()
                        if (pagination.page < pagination.total_pages) {
                          handlePageChange(pagination.page + 1)
                        }
                      }}
                      onKeyDown={(e) => {
                        if (pagination.page === pagination.total_pages && (e.key === 'Enter' || e.key === ' ')) {
                          e.preventDefault()
                        }
                      }}
                      aria-disabled={pagination.page === pagination.total_pages}
                      tabIndex={pagination.page === pagination.total_pages ? -1 : 0}
                      className={pagination.page === pagination.total_pages ? 'pointer-events-none opacity-50' : ''}
                    />
                  </PaginationItem>
                </PaginationContent>
              </Pagination>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default AgentExecutionLogs
