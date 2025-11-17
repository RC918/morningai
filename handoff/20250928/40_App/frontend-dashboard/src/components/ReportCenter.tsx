import React, { useState, useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@morningai/shared-ui'
import { AppleButton } from '@/components/ui/apple-button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@morningai/shared-ui'
import { Badge } from '@morningai/shared-ui'
import { Label } from '@morningai/shared-ui'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@morningai/shared-ui'
import { 
  Download, FileText, Calendar, Clock, CheckCircle, 
  AlertCircle, Loader2, BarChart3, TrendingUp 
} from 'lucide-react'
import apiClient from '@/lib/api'

type KnownReportType = 'performance' | 'task_tracking' | 'resilience' | 'financial'
type KnownReportFormat = 'pdf' | 'csv' | 'json'
type KnownReportStatus = 'completed' | 'failed' | 'generating' | 'pending'

type ReportType = KnownReportType | (string & {})
type ReportFormat = KnownReportFormat | (string & {})
type ReportStatus = KnownReportStatus | (string & {})

interface ReportTemplate {
  id: string
  name: string
  description: string
  metrics: string[]
}

interface ReportHistoryItem {
  id: number
  name: string
  type: ReportType
  generated_at: string
  format: ReportFormat
  status: ReportStatus
  file_path?: string | null
}

const ReportCenter = (): React.ReactElement => {
  const { t } = useTranslation()
  const [reportType, setReportType] = useState<string>('performance')
  const [timeRange, setTimeRange] = useState<string>('24h')
  const [isGenerating, setIsGenerating] = useState<boolean>(false)
  const [reportHistory, setReportHistory] = useState<ReportHistoryItem[]>([])
  const [reportTemplates, setReportTemplates] = useState<ReportTemplate[]>([])

  useEffect(() => {
    loadReportTemplates()
    loadReportHistory()
  }, [])

  const loadReportTemplates = async (): Promise<void> => {
    try {
      const templates: ReportTemplate[] = await apiClient.getReportTemplates()
      setReportTemplates(templates)
    } catch (error) {
      console.error('Failed to load report templates:', error)
    }
  }

  const loadReportHistory = async (): Promise<void> => {
    try {
      const history: ReportHistoryItem[] = await apiClient.getReportHistory()
      setReportHistory(history)
    } catch (error) {
      console.error('Failed to load report history:', error)
      setReportHistory([
        {
          id: 1,
          name: t('reportCenter.history.systemPerformance'),
          type: 'performance',
          generated_at: '2024-01-01T14:30:00Z',
          format: 'PDF',
          status: 'completed'
        },
        {
          id: 2,
          name: t('reportCenter.history.taskTracking'),
          type: 'task_tracking',
          generated_at: '2024-01-01T12:00:00Z',
          format: 'CSV',
          status: 'completed'
        },
        {
          id: 3,
          name: t('reportCenter.history.resilience'),
          type: 'resilience',
          generated_at: '2024-01-01T10:15:00Z',
          format: 'PDF',
          status: 'completed'
        }
      ])
    }
  }

  const generateReport = async (format: string): Promise<void> => {
    setIsGenerating(true)
    try {
      // TODO: Backend returns file download for pdf/csv, JSON for json.
      // apiClient.request() currently assumes all responses are JSON, which fails for binary responses.
      // Need: 1) Add blob/binary response support to apiClient
      //       2) Implement proper file download handling in UI
      //       3) Define discriminated union type based on format parameter
      // Backend reference: handoff/20250928/40_App/api-backend/src/main.py:547-586
      const result: unknown = await apiClient.generateReport({
        type: reportType,
        time_range: timeRange,
        format: format
      })

      if (result && typeof result === 'object' && 'success' in result && 'download_url' in result) {
        const typedResult = result as { success?: boolean; download_url?: string }
        if (typedResult.success && typedResult.download_url) {
          window.open(typedResult.download_url, '_blank')
          setTimeout(loadReportHistory, 1000)
        }
      } else {
        console.log('Report data:', result)
      }
    } catch (error) {
      console.error('Report generation failed:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const getStatusIcon = (status: ReportStatus | string): React.ReactElement => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-success-600" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-error-600" />
      case 'generating':
        return <Loader2 className="w-4 h-4 text-info-600 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-neutral-600" />
    }
  }

  const getStatusColor = (status: ReportStatus | string): string => {
    switch (status) {
      case 'completed':
        return 'bg-success-100 text-success-800'
      case 'failed':
        return 'bg-error-100 text-error-800'
      case 'generating':
        return 'bg-info-100 text-info-800'
      default:
        return 'bg-neutral-100 text-neutral-800'
    }
  }

  const getReportTypeIcon = (type: ReportType | string): React.ReactElement => {
    switch (type) {
      case 'performance':
        return <TrendingUp className="w-4 h-4" />
      case 'task_tracking':
        return <CheckCircle className="w-4 h-4" />
      case 'resilience':
        return <BarChart3 className="w-4 h-4" />
      default:
        return <FileText className="w-4 h-4" />
    }
  }

  const selectedTemplate: ReportTemplate | undefined = reportTemplates.find((t: ReportTemplate) => t.id === reportType)

  return (
    <div className="space-y-6">
      {/* Report Generation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            {t('reportCenter.generation.title')}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <Label htmlFor="report-type" className="text-sm font-medium">{t('reportCenter.generation.reportType')}</Label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger id="report-type">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {reportTemplates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      {getReportTypeIcon(template.id)}
                      {template.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label htmlFor="time-range" className="text-sm font-medium">{t('reportCenter.generation.timeRange')}</Label>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger id="time-range">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">{t('reportCenter.timeRanges.1h')}</SelectItem>
                  <SelectItem value="24h">{t('reportCenter.timeRanges.24h')}</SelectItem>
                  <SelectItem value="7d">{t('reportCenter.timeRanges.7d')}</SelectItem>
                  <SelectItem value="30d">{t('reportCenter.timeRanges.30d')}</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {selectedTemplate && (
            <div className="p-3 bg-neutral-50 rounded-lg">
              <p className="text-sm text-neutral-600 mb-2">{selectedTemplate.description}</p>
              <div className="flex flex-wrap gap-1">
                {selectedTemplate.metrics.map((metric: string, index: number) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {metric}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex space-x-2">
            <AppleButton 
              onClick={() => generateReport('pdf')} 
              disabled={isGenerating}
              className="flex-1"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              {t('reportCenter.generation.generatePDF')}
            </AppleButton>
            <AppleButton 
              variant="outline" 
              onClick={() => generateReport('csv')} 
              disabled={isGenerating}
              className="flex-1"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              {t('reportCenter.generation.exportCSV')}
            </AppleButton>
          </div>
        </CardContent>
      </Card>

      {/* Report History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            {t('reportCenter.history.title')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {reportHistory.map((report: ReportHistoryItem) => (
              <div key={report.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(report.status)}
                  <div>
                    <h4 className="font-medium">{report.name}</h4>
                    <p className="text-sm text-neutral-600">
                      {new Date(report.generated_at).toLocaleString()} • {report.format}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(report.status)}>
                    {report.status === 'completed' ? t('reportCenter.status.completed') : 
                     report.status === 'failed' ? t('reportCenter.status.failed') : 
                     report.status === 'generating' ? t('reportCenter.status.generating') : t('reportCenter.status.unknown')}
                  </Badge>
                  {report.status === 'completed' && (
                    <AppleButton variant="outline" size="sm">
                      <Download className="w-4 h-4" />
                    </AppleButton>
                  )}
                </div>
              </div>
            ))}
            {reportHistory.length === 0 && (
              <div className="text-center py-8 text-neutral-600">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>{t('reportCenter.history.empty')}</p>
                <p className="text-sm">{t('reportCenter.history.emptyHint')}</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>{t('reportCenter.quickActions.title')}</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <AppleButton 
              variant="outline" 
              className="h-20 flex-col"
              onClick={() => {
                setReportType('performance')
                setTimeRange('24h')
                generateReport('pdf')
              }}
              disabled={isGenerating}
            >
              <TrendingUp className="w-6 h-6 mb-2" />
              <span className="text-xs">{t('reportCenter.quickActions.dailyPerformance')}</span>
            </AppleButton>
            <AppleButton 
              variant="outline" 
              className="h-20 flex-col"
              onClick={() => {
                setReportType('task_tracking')
                setTimeRange('7d')
                generateReport('csv')
              }}
              disabled={isGenerating}
            >
              <CheckCircle className="w-6 h-6 mb-2" />
              <span className="text-xs">{t('reportCenter.quickActions.weeklyTasks')}</span>
            </AppleButton>
            <AppleButton 
              variant="outline" 
              className="h-20 flex-col"
              onClick={() => {
                setReportType('resilience')
                setTimeRange('30d')
                generateReport('pdf')
              }}
              disabled={isGenerating}
            >
              <BarChart3 className="w-6 h-6 mb-2" />
              <span className="text-xs">{t('reportCenter.quickActions.monthlyResilience')}</span>
            </AppleButton>
            <AppleButton 
              variant="outline" 
              className="h-20 flex-col"
              onClick={() => {
                setReportType('financial')
                setTimeRange('30d')
                generateReport('pdf')
              }}
              disabled={isGenerating}
            >
              <FileText className="w-6 h-6 mb-2" />
              <span className="text-xs">{t('reportCenter.quickActions.monthlyCost')}</span>
            </AppleButton>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ReportCenter
