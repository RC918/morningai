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
  StatusBadge
} from '@morningai/shared-ui'
import { 
  Activity,
  AlertTriangle,
  CheckCircle,
  Clock,
  Filter,
  RefreshCw,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { apiClient } from '@/lib/api-client'

const AgentExecutionLogs = () => {
  const { t } = useTranslation()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [logs, setLogs] = useState([])
  const [summary, setSummary] = useState(null)
  const [pagination, setPagination] = useState({ page: 1, page_size: 50, total_items: 0, total_pages: 0 })
  
  const [filters, setFilters] = useState({
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

      const response = await apiClient(`/admin/agent-execution-logs?${params.toString()}`)
      
      if (response.execution_logs) {
        setLogs(response.execution_logs)
        setSummary(response.summary)
        setPagination(prev => ({
          ...prev,
          total_items: response.pagination.total_items,
          total_pages: response.pagination.total_pages
        }))
      }
    } catch (error) {
      console.error('Failed to load execution logs:', error)
      setError(error.message || 'Failed to load execution logs')
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


  const formatDuration = (durationMs) => {
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

  const formatTimestamp = (timestamp) => {
    if (!timestamp) return t('common.na')
    return new Date(timestamp).toLocaleString()
  }

  if (loading && logs.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
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
                <p className="text-sm text-gray-600">{t('governance.executionLogs.summary.totalExecutions')}</p>
                <Activity className="w-5 h-5 text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {summary.total_executions || 0}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.executionLogs.summary.successRate')}</p>
                <CheckCircle className="w-5 h-5 text-green-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {summary.success_rate ? `${(summary.success_rate * 100).toFixed(1)}%` : t('common.na')}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.executionLogs.summary.avgDuration')}</p>
                <Clock className="w-5 h-5 text-purple-600" />
              </div>
              <p className="text-3xl font-bold text-gray-900">
                {formatDuration(summary.avg_duration_ms)}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between mb-2">
                <p className="text-sm text-gray-600">{t('governance.executionLogs.summary.statusBreakdown')}</p>
                <Filter className="w-5 h-5 text-orange-600" />
              </div>
              <div className="space-y-1">
                {summary.status_counts && Object.entries(summary.status_counts).map(([status, count]) => (
                  <div key={status} className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">{t(`governance.executionLogs.statuses.${status}`)}</span>
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
              <label className="text-sm font-medium text-gray-700 mb-1 block">
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
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                {t('governance.executionLogs.filters.agentId')}
              </label>
              <Input
                value={filters.agent_id}
                onChange={(e) => setFilters(prev => ({ ...prev, agent_id: e.target.value }))}
                placeholder={t('governance.executionLogs.filters.agentIdPlaceholder')}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                {t('governance.executionLogs.filters.taskType')}
              </label>
              <Input
                value={filters.task_type}
                onChange={(e) => setFilters(prev => ({ ...prev, task_type: e.target.value }))}
                placeholder={t('governance.executionLogs.filters.taskTypePlaceholder')}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
                {t('governance.executionLogs.filters.startDate')}
              </label>
              <Input
                type="date"
                value={filters.start_date}
                onChange={(e) => setFilters(prev => ({ ...prev, start_date: e.target.value }))}
              />
            </div>

            <div>
              <label className="text-sm font-medium text-gray-700 mb-1 block">
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

      {/* Execution Logs Table */}
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
          {logs.length === 0 ? (
            <p className="text-center text-gray-500 py-8">{t('governance.executionLogs.noLogs')}</p>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div key={log.task_id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <StatusBadge status={log.status} showIcon>
                          {t(`governance.executionLogs.statuses.${log.status}`)}
                        </StatusBadge>
                        <span className="text-sm font-mono text-gray-600">
                          {log.task_id?.substring(0, 12)}...
                        </span>
                        {log.task_type && (
                          <Badge variant="outline" className="text-xs">
                            {log.task_type}
                          </Badge>
                        )}
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                        {log.agent && (
                          <div>
                            <p className="text-gray-600">{t('governance.executionLogs.columns.agent')}</p>
                            <p className="font-medium">{log.agent.agent_type || t('common.na')}</p>
                            {log.agent.reputation_score !== undefined && (
                              <p className="text-xs text-gray-500">
                                {t('governance.agents.reputation')}: {log.agent.reputation_score}
                              </p>
                            )}
                          </div>
                        )}
                        
                        {log.tenant_id && (
                          <div>
                            <p className="text-gray-600">{t('governance.executionLogs.columns.tenant')}</p>
                            <p className="font-medium font-mono text-xs">{log.tenant_id.substring(0, 12)}...</p>
                          </div>
                        )}
                        
                        <div>
                          <p className="text-gray-600">{t('governance.executionLogs.columns.duration')}</p>
                          <p className="font-medium">{formatDuration(log.duration_ms)}</p>
                        </div>
                        
                        <div>
                          <p className="text-gray-600">{t('governance.executionLogs.details.createdAt')}</p>
                          <p className="font-medium text-xs">{formatTimestamp(log.timestamps?.created_at)}</p>
                        </div>
                      </div>

                      {log.error_message && (
                        <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-800">
                          <p className="font-semibold">{t('governance.executionLogs.details.errorMessage')}:</p>
                          <p className="text-xs mt-1">{log.error_message}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Pagination */}
          {pagination.total_pages > 1 && (
            <div className="flex items-center justify-between mt-6 pt-4 border-t">
              <p className="text-sm text-gray-600">
                {t('governance.executionLogs.pagination.showing', {
                  start: (pagination.page - 1) * pagination.page_size + 1,
                  end: Math.min(pagination.page * pagination.page_size, pagination.total_items),
                  total: pagination.total_items
                })}
              </p>
              <div className="flex items-center gap-2">
                <Button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page - 1 }))}
                  disabled={pagination.page === 1}
                  variant="outline"
                  size="sm"
                >
                  <ChevronLeft className="w-4 h-4 mr-1" />
                  {t('governance.executionLogs.pagination.previous')}
                </Button>
                <span className="text-sm text-gray-600">
                  {t('governance.executionLogs.pagination.page', {
                    current: pagination.page,
                    total: pagination.total_pages
                  })}
                </span>
                <Button
                  onClick={() => setPagination(prev => ({ ...prev, page: prev.page + 1 }))}
                  disabled={pagination.page === pagination.total_pages}
                  variant="outline"
                  size="sm"
                >
                  {t('governance.executionLogs.pagination.next')}
                  <ChevronRight className="w-4 h-4 ml-1" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default AgentExecutionLogs
