import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { 
  Download, FileText, Calendar, Clock, CheckCircle, 
  AlertCircle, Loader2, BarChart3, TrendingUp 
} from 'lucide-react'

const ReportCenter = () => {
  const [reportType, setReportType] = useState('performance')
  const [timeRange, setTimeRange] = useState('24h')
  const [isGenerating, setIsGenerating] = useState(false)
  const [reportHistory, setReportHistory] = useState([])
  const [reportTemplates, setReportTemplates] = useState([])

  useEffect(() => {
    loadReportTemplates()
    loadReportHistory()
  }, [])

  const loadReportTemplates = async () => {
    try {
      const response = await fetch('/api/reports/templates')
      const templates = await response.json()
      setReportTemplates(templates)
    } catch (error) {
      console.error('Failed to load report templates:', error)
    }
  }

  const loadReportHistory = async () => {
    try {
      const response = await fetch('/api/reports/history')
      const history = await response.json()
      setReportHistory(history)
    } catch (error) {
      console.error('Failed to load report history:', error)
      setReportHistory([
        {
          id: 1,
          name: '系統性能報告',
          type: 'performance',
          generated_at: '2024-01-01T14:30:00Z',
          format: 'PDF',
          status: 'completed'
        },
        {
          id: 2,
          name: '任務追蹤報告',
          type: 'task_tracking',
          generated_at: '2024-01-01T12:00:00Z',
          format: 'CSV',
          status: 'completed'
        },
        {
          id: 3,
          name: '韌性模式報告',
          type: 'resilience',
          generated_at: '2024-01-01T10:15:00Z',
          format: 'PDF',
          status: 'completed'
        }
      ])
    }
  }

  const generateReport = async (format) => {
    setIsGenerating(true)
    try {
      const response = await fetch('/api/reports/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: reportType,
          time_range: timeRange,
          format: format
        })
      })

      if (format === 'pdf' || format === 'csv') {
        const blob = await response.blob()
        const url = window.URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `report_${reportType}_${timeRange}.${format}`
        document.body.appendChild(a)
        a.click()
        window.URL.revokeObjectURL(url)
        document.body.removeChild(a)
        
        setTimeout(loadReportHistory, 1000)
      } else {
        const data = await response.json()
        console.log('Report data:', data)
      }
    } catch (error) {
      console.error('Report generation failed:', error)
    } finally {
      setIsGenerating(false)
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-red-600" />
      case 'generating':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />
      default:
        return <Clock className="w-4 h-4 text-gray-600" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-green-100 text-green-800'
      case 'failed':
        return 'bg-red-100 text-red-800'
      case 'generating':
        return 'bg-blue-100 text-blue-800'
      default:
        return 'bg-gray-100 text-gray-800'
    }
  }

  const getReportTypeIcon = (type) => {
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

  const selectedTemplate = reportTemplates.find(t => t.id === reportType)

  return (
    <div className="space-y-6">
      {/* Report Generation */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <FileText className="w-5 h-5 mr-2" />
            報表生成
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-sm font-medium">報表類型</label>
              <Select value={reportType} onValueChange={setReportType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {reportTemplates.map((template) => (
                    <SelectItem key={template.id} value={template.id}>
                      <div className="flex items-center">
                        {getReportTypeIcon(template.id)}
                        <span className="ml-2">{template.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="text-sm font-medium">時間範圍</label>
              <Select value={timeRange} onValueChange={setTimeRange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1h">過去1小時</SelectItem>
                  <SelectItem value="24h">過去24小時</SelectItem>
                  <SelectItem value="7d">過去7天</SelectItem>
                  <SelectItem value="30d">過去30天</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>

          {selectedTemplate && (
            <div className="p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-2">{selectedTemplate.description}</p>
              <div className="flex flex-wrap gap-1">
                {selectedTemplate.metrics.map((metric, index) => (
                  <Badge key={index} variant="outline" className="text-xs">
                    {metric}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          <div className="flex space-x-2">
            <Button 
              onClick={() => generateReport('pdf')} 
              disabled={isGenerating}
              className="flex-1"
            >
              {isGenerating ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <Download className="w-4 h-4 mr-2" />
              )}
              生成 PDF
            </Button>
            <Button 
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
              導出 CSV
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Report History */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Calendar className="w-5 h-5 mr-2" />
            報表歷史
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {reportHistory.map((report) => (
              <div key={report.id} className="flex items-center justify-between p-3 border rounded-lg">
                <div className="flex items-center space-x-3">
                  {getStatusIcon(report.status)}
                  <div>
                    <h4 className="font-medium">{report.name}</h4>
                    <p className="text-sm text-gray-600">
                      {new Date(report.generated_at).toLocaleString()} • {report.format}
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <Badge className={getStatusColor(report.status)}>
                    {report.status === 'completed' ? '已完成' : 
                     report.status === 'failed' ? '失敗' : 
                     report.status === 'generating' ? '生成中' : '未知'}
                  </Badge>
                  {report.status === 'completed' && (
                    <Button variant="outline" size="sm">
                      <Download className="w-4 h-4" />
                    </Button>
                  )}
                </div>
              </div>
            ))}
            {reportHistory.length === 0 && (
              <div className="text-center py-8 text-gray-500">
                <FileText className="w-12 h-12 mx-auto mb-4 opacity-50" />
                <p>尚無報表歷史記錄</p>
                <p className="text-sm">生成第一份報表開始使用</p>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button 
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
              <span className="text-xs">日性能報告</span>
            </Button>
            <Button 
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
              <span className="text-xs">週任務報告</span>
            </Button>
            <Button 
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
              <span className="text-xs">月韌性報告</span>
            </Button>
            <Button 
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
              <span className="text-xs">月成本報告</span>
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default ReportCenter
