import { useState, useEffect, useCallback } from 'react'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { 
  Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Clock, DollarSign, Cpu, MemoryStick, Zap, Settings, Download,
  Plus, Trash2, Edit3, FileText, Grid3X3, Loader2, Save
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { WidgetLibrary, getWidgetComponent } from './WidgetLibrary'
import ReportCenter from './ReportCenter'
import { DashboardSkeleton } from '@/components/feedback/ContentSkeleton'
import LiveRegion from '@/components/LiveRegion'
import apiClient from '@/lib/api'
import { safeInterval } from '@/lib/safeInterval'

const DraggableWidget = ({ widget, index, moveWidget, onRemove, isEditMode }) => {
  const [{ isDragging }, drag] = useDrag({
    type: 'widget',
    item: { index },
    collect: (monitor) => ({
      isDragging: monitor.isDragging(),
    }),
  })

  const [, drop] = useDrop({
    accept: 'widget',
    hover: (draggedItem) => {
      if (draggedItem.index !== index) {
        moveWidget(draggedItem.index, index)
        draggedItem.index = index
      }
    },
  })

  return (
    <div
      ref={(node) => drag(drop(node))}
      className={`relative ${isDragging ? 'opacity-50' : ''} ${isEditMode ? 'cursor-move' : ''}`}
    >
      {isEditMode && (
        <Button
          variant="destructive"
          size="sm"
          className="absolute top-2 right-2 z-10"
          onClick={() => onRemove(index)}
          aria-label="移除小工具"
        >
          <Trash2 className="w-4 h-4" aria-hidden="true" />
        </Button>
      )}
      {widget.component}
    </div>
  )
}

const Dashboard = () => {
  const [isLoading, setIsLoading] = useState(true)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showReportCenter, setShowReportCenter] = useState(false)
  const [availableWidgets, setAvailableWidgets] = useState([])
  const [dashboardLayout, setDashboardLayout] = useState([])
  const [dashboardData, setDashboardData] = useState({})
  const [saveStatus, setSaveStatus] = useState('idle')
  const [systemMetrics, setSystemMetrics] = useState({
    cpu_usage: 72,
    memory_usage: 68,
    response_time: 145,
    error_rate: 0.02,
    active_strategies: 12,
    pending_approvals: 3,
    cost_today: 45.67,
    cost_saved: 123.45
  })

  const [recentDecisions, setRecentDecisions] = useState([
    {
      id: 1,
      timestamp: '2024-01-01T14:30:00Z',
      strategy: 'CPU優化策略',
      status: 'executed',
      impact: '+15% 性能提升',
      confidence: 0.87
    },
    {
      id: 2,
      timestamp: '2024-01-01T14:15:00Z',
      strategy: '緩存優化',
      status: 'pending',
      impact: '預計 +20% 響應速度',
      confidence: 0.92
    },
    {
      id: 3,
      timestamp: '2024-01-01T14:00:00Z',
      strategy: '自動擴容',
      status: 'executed',
      impact: '處理能力 +50%',
      confidence: 0.78
    }
  ])

  const [performanceData, setPerformanceData] = useState([
    { time: '12:00', cpu: 65, memory: 60, response_time: 120 },
    { time: '12:30', cpu: 70, memory: 65, response_time: 135 },
    { time: '13:00', cpu: 75, memory: 70, response_time: 150 },
    { time: '13:30', cpu: 72, memory: 68, response_time: 145 },
    { time: '14:00', cpu: 68, memory: 65, response_time: 130 },
    { time: '14:30', cpu: 72, memory: 68, response_time: 145 }
  ])


  const loadDashboardLayout = useCallback(async () => {
    try {
      const layout = await apiClient.request('/dashboard/layouts?user_id=default')
      if (layout.widgets) {
        setDashboardLayout(layout.widgets.map(widget => ({
          ...widget,
          component: null
        })))
      } else {
        setDashboardLayout(getDefaultWidgets())
      }
    } catch (error) {
      console.error('Failed to load dashboard layout:', error)
      setDashboardLayout(getDefaultWidgets())
    }
  }, [])

  const loadAvailableWidgets = useCallback(async () => {
    try {
      const response = await apiClient.getDashboardWidgets()
      setAvailableWidgets(response.widgets || [])
    } catch (error) {
      console.error('Failed to load available widgets:', error)
    }
  }, [])

  const loadDashboardData = useCallback(async () => {
    try {
      const data = await apiClient.getDashboardData()
      setDashboardData(data)
    } catch (error) {
      console.error('Failed to load dashboard data:', error)
    }
  }, [])

  useEffect(() => {
    const initializeDashboard = async () => {
      setIsLoading(true)
      await loadDashboardLayout()
      await loadAvailableWidgets()
      await loadDashboardData()
      setIsLoading(false)
    }
    initializeDashboard()
  }, [loadDashboardLayout, loadAvailableWidgets, loadDashboardData])

  useEffect(() => {
    // 模擬實時數據更新 - 使用 safeInterval
    const cleanup = safeInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        cpu_usage: Math.max(50, Math.min(90, prev.cpu_usage + (Math.random() - 0.5) * 10)),
        memory_usage: Math.max(40, Math.min(85, prev.memory_usage + (Math.random() - 0.5) * 8)),
        response_time: Math.max(100, Math.min(300, prev.response_time + (Math.random() - 0.5) * 20))
      }))
      
      if (!isEditMode) {
        loadDashboardData()
      }
    }, 5000, 120)

    return cleanup
  }, [isEditMode, loadDashboardData])


  const saveDashboardLayout = async () => {
    setSaveStatus('saving')
    try {
      await apiClient.request('/dashboard/layouts', {
        method: 'POST',
        body: JSON.stringify({
          user_id: 'default',
          layout: { widgets: dashboardLayout.map(w => ({ id: w.id, position: w.position })) }
        })
      })
      setSaveStatus('success')
      setTimeout(() => setSaveStatus('idle'), 2000)
    } catch (error) {
      console.error('Failed to save dashboard layout:', error)
      setSaveStatus('error')
      setTimeout(() => setSaveStatus('idle'), 3000)
    }
  }

  const getDefaultWidgets = () => [
    { id: 'cpu_usage', position: { x: 0, y: 0, w: 6, h: 4 } },
    { id: 'memory_usage', position: { x: 6, y: 0, w: 6, h: 4 } },
    { id: 'response_time', position: { x: 0, y: 4, w: 6, h: 4 } },
    { id: 'error_rate', position: { x: 6, y: 4, w: 6, h: 4 } },
    { id: 'active_strategies', position: { x: 0, y: 8, w: 4, h: 3 } },
    { id: 'pending_approvals', position: { x: 4, y: 8, w: 4, h: 3 } },
    { id: 'task_execution', position: { x: 8, y: 8, w: 4, h: 6 } }
  ]

  const moveWidget = useCallback((dragIndex, hoverIndex) => {
    setDashboardLayout(prev => {
      const newLayout = [...prev]
      const draggedWidget = newLayout[dragIndex]
      newLayout.splice(dragIndex, 1)
      newLayout.splice(hoverIndex, 0, draggedWidget)
      return newLayout
    })
  }, [])

  const removeWidget = useCallback((index) => {
    setDashboardLayout(prev => prev.filter((_, i) => i !== index))
  }, [])

  const addWidget = (widgetId) => {
    const newWidget = {
      id: widgetId,
      position: { x: 0, y: 0, w: 6, h: 4 }
    }
    setDashboardLayout(prev => [...prev, newWidget])
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'executed': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'failed': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusIcon = (status) => {
    switch (status) {
      case 'executed': return <CheckCircle className="w-4 h-4" />
      case 'pending': return <Clock className="w-4 h-4" />
      case 'failed': return <AlertTriangle className="w-4 h-4" />
      default: return <Activity className="w-4 h-4" />
    }
  }

  const DashboardToolbar = () => (
    <div className="flex justify-between items-center mb-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">
          {showReportCenter ? '報表中心' : '自助儀表板'}
        </h1>
        <div className="flex items-center gap-3 mt-2">
          <p className="text-gray-600">
            {showReportCenter ? '生成和管理系統報表' : '可自訂的系統監控與任務追蹤'}
          </p>
          {saveStatus === 'saving' && (
            <div className="flex items-center text-blue-600 text-sm">
              <Loader2 className="w-4 h-4 mr-1 animate-spin" aria-hidden="true" />
              <span>儲存中...</span>
            </div>
          )}
          {saveStatus === 'success' && (
            <div className="flex items-center text-green-600 text-sm" role="status" aria-live="polite">
              <CheckCircle className="w-4 h-4 mr-1" aria-hidden="true" />
              <span>已儲存</span>
            </div>
          )}
          {saveStatus === 'error' && (
            <div className="flex items-center text-red-600 text-sm" role="alert" aria-live="assertive">
              <AlertTriangle className="w-4 h-4 mr-1" aria-hidden="true" />
              <span>儲存失敗</span>
            </div>
          )}
        </div>
      </div>
      <div className="flex space-x-2">
        <Button
          variant={showReportCenter ? "default" : "outline"}
          onClick={() => setShowReportCenter(!showReportCenter)}
        >
          <FileText className="w-4 h-4 mr-2" />
          報表中心
        </Button>
        {!showReportCenter && (
          <Button
            variant={isEditMode ? "default" : "outline"}
            onClick={() => {
              setIsEditMode(!isEditMode)
              if (isEditMode) saveDashboardLayout()
            }}
            disabled={saveStatus === 'saving'}
          >
            {saveStatus === 'saving' ? (
              <Loader2 className="w-4 h-4 mr-2 animate-spin" aria-hidden="true" />
            ) : (
              <Settings className="w-4 h-4 mr-2" />
            )}
            {isEditMode ? '完成編輯' : '自訂儀表板'}
          </Button>
        )}
      </div>
    </div>
  )

  const WidgetAddDialog = () => (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" className="w-full h-32 border-dashed">
          <Plus className="w-8 h-8 mb-2" />
          <span>添加組件</span>
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>選擇組件</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto">
          {availableWidgets.map((widget) => (
            <Button
              key={widget.id}
              variant="outline"
              className="h-20 flex-col"
              onClick={() => {
                addWidget(widget.id)
                document.querySelector('[data-state="open"]')?.click() // Close dialog
              }}
            >
              <Grid3X3 className="w-6 h-6 mb-2" />
              <span className="text-xs">{widget.name}</span>
            </Button>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )

  if (isLoading) {
    return <DashboardSkeleton />
  }

  if (showReportCenter) {
    return (
      <DndProvider backend={HTML5Backend}>
        <div className="p-6 space-y-6">
          <DashboardToolbar />
          <ReportCenter />
        </div>
      </DndProvider>
    )
  }

  const getSaveStatusMessage = () => {
    switch (saveStatus) {
      case 'saving':
        return '正在儲存儀表板配置...'
      case 'success':
        return '儀表板配置已成功儲存'
      case 'error':
        return '儲存儀表板配置時發生錯誤'
      default:
        return ''
    }
  }

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="p-6 space-y-6">
        <LiveRegion 
          message={getSaveStatusMessage()}
          politeness={saveStatus === 'error' ? 'assertive' : 'polite'}
        />
        <DashboardToolbar />

        {/* Customizable Dashboard Widgets */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {dashboardLayout.map((widget, index) => {
            const WidgetComponent = getWidgetComponent(widget.id)
            const widgetWithComponent = {
              ...widget,
              component: <WidgetComponent data={dashboardData} />
            }
            
            return (
              <DraggableWidget
                key={`${widget.id}-${index}`}
                widget={widgetWithComponent}
                index={index}
                moveWidget={moveWidget}
                onRemove={removeWidget}
                isEditMode={isEditMode}
              />
            )
          })}
          
          {isEditMode && (
            <WidgetAddDialog />
          )}
        </div>

        {/* Performance Charts - Always visible */}
        {!isEditMode && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 性能趨勢圖 */}
            <Card>
              <CardHeader>
                <CardTitle>性能趨勢</CardTitle>
                <CardDescription>過去6小時的系統性能指標</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="cpu" 
                      stroke="#3b82f6" 
                      strokeWidth={2}
                      name="CPU (%)"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="memory" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      name="內存 (%)"
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* 響應時間圖 */}
            <Card>
              <CardHeader>
                <CardTitle>響應時間趨勢</CardTitle>
                <CardDescription>系統響應時間變化</CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Area 
                      type="monotone" 
                      dataKey="response_time" 
                      stroke="#f59e0b" 
                      fill="#fef3c7"
                      name="響應時間 (ms)"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recent Decisions - Always visible when not in edit mode */}
        {!isEditMode && (
          <Card>
            <CardHeader>
              <CardTitle>最近決策</CardTitle>
              <CardDescription>AI系統最近執行的決策和策略</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentDecisions.map((decision) => (
                  <div key={decision.id} className="flex items-center justify-between p-4 border rounded-lg">
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full ${getStatusColor(decision.status)}`}>
                        {getStatusIcon(decision.status)}
                      </div>
                      <div>
                        <h4 className="font-medium">{decision.strategy}</h4>
                        <p className="text-sm text-gray-600">{decision.impact}</p>
                        <p className="text-xs text-gray-400">
                          {new Date(decision.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className={getStatusColor(decision.status)}>
                        {decision.status === 'executed' ? '已執行' : 
                         decision.status === 'pending' ? '待審批' : '失敗'}
                      </Badge>
                      <p className="text-sm text-gray-600 mt-1">
                        信心度: {(decision.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Edit Mode Instructions */}
        {isEditMode && (
          <Card className="border-dashed border-2">
            <CardContent className="p-6 text-center">
              <Edit3 className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <h3 className="text-lg font-medium mb-2">自訂儀表板</h3>
              <p className="text-gray-600 mb-4">
                拖拽組件重新排列，點擊垃圾桶圖標刪除組件，或添加新的組件
              </p>
              <div className="flex justify-center space-x-2">
                <Button onClick={() => setDashboardLayout(getDefaultWidgets())}>
                  重置為預設布局
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DndProvider>
  )
}

export default Dashboard

