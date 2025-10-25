import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { 
  Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Clock, DollarSign, Cpu, MemoryStick, Zap, Settings, Download,
  Plus, Trash2, Edit3, FileText, Grid3X3, Undo2, Redo2
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AppleButton } from '@/components/ui/apple-button'
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, AreaChart, Area } from 'recharts'
import { WidgetLibrary, getWidgetComponent } from './WidgetLibrary'
import ReportCenter from './ReportCenter'
import { DashboardSkeleton } from '@/components/feedback/ContentSkeleton'
import SaveStatusIndicator from './SaveStatusIndicator'
import useUndoRedo from '@/hooks/useUndoRedo'
import apiClient from '@/lib/api'
import { safeInterval } from '@/lib/safeInterval'

const DraggableWidget = ({ widget, index, moveWidget, onRemove, isEditMode, t }) => {
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
      className={`relative transition-all duration-200 ${isDragging ? 'opacity-50 scale-95' : 'hover:shadow-lg'} ${isEditMode ? 'cursor-move' : ''}`}
    >
      {isEditMode && (
        <AppleButton
          variant="destructive"
          size="sm"
          className="absolute top-2 right-2 z-10 shadow-md"
          onClick={() => onRemove(index)}
          aria-label={t('dashboard.removeWidget')}
          haptic="heavy"
        >
          <Trash2 className="w-4 h-4" aria-hidden="true" />
        </AppleButton>
      )}
      {widget.component}
    </div>
  )
}

const Dashboard = () => {
  const { t } = useTranslation()
  const [isLoading, setIsLoading] = useState(true)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showReportCenter, setShowReportCenter] = useState(false)
  const [availableWidgets, setAvailableWidgets] = useState([])
  const [dashboardData, setDashboardData] = useState({})
  const [saveStatus, setSaveStatus] = useState({
    status: 'saved',
    lastSaved: null,
    error: null
  })
  
  const {
    state: dashboardLayout,
    setState: setDashboardLayout,
    undo,
    redo,
    canUndo,
    canRedo
  } = useUndoRedo([])
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
      strategy: t('dashboard.decisions.cpuOptimization'),
      status: 'executed',
      impact: t('dashboard.decisions.performanceIncrease', { percent: 15 }),
      confidence: 0.87
    },
    {
      id: 2,
      timestamp: '2024-01-01T14:15:00Z',
      strategy: t('dashboard.decisions.cacheOptimization'),
      status: 'pending',
      impact: t('dashboard.decisions.expectedResponseSpeed', { percent: 20 }),
      confidence: 0.92
    },
    {
      id: 3,
      timestamp: '2024-01-01T14:00:00Z',
      strategy: t('dashboard.decisions.autoScaling'),
      status: 'executed',
      impact: t('dashboard.decisions.capacityIncrease', { percent: 50 }),
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

  useEffect(() => {
    if (!isEditMode) return

    const handleKeyDown = (e) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'z') {
        e.preventDefault()
        if (e.shiftKey) {
          redo()
        } else {
          undo()
        }
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [isEditMode, undo, redo])


  const saveDashboardLayout = async () => {
    setSaveStatus({ status: 'saving', lastSaved: saveStatus.lastSaved, error: null })
    
    try {
      await apiClient.request('/dashboard/layouts', {
        method: 'POST',
        body: JSON.stringify({
          user_id: 'default',
          layout: { widgets: dashboardLayout.map(w => ({ id: w.id, position: w.position })) }
        })
      })
      setSaveStatus({ status: 'saved', lastSaved: new Date(), error: null })
    } catch (error) {
      console.error('Failed to save dashboard layout:', error)
      setSaveStatus({ 
        status: 'error', 
        lastSaved: saveStatus.lastSaved, 
        error: error.message || '保存失敗'
      })
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
    setSaveStatus(prev => ({ ...prev, status: 'unsaved' }))
  }, [])

  const removeWidget = useCallback((index) => {
    setDashboardLayout(prev => prev.filter((_, i) => i !== index))
    setSaveStatus(prev => ({ ...prev, status: 'unsaved' }))
  }, [])

  const addWidget = (widgetId) => {
    const newWidget = {
      id: widgetId,
      position: { x: 0, y: 0, w: 6, h: 4 }
    }
    setDashboardLayout(prev => [...prev, newWidget])
    setSaveStatus(prev => ({ ...prev, status: 'unsaved' }))
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
        <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
          {showReportCenter ? t('reportCenter.title') : t('dashboard.title')}
        </h1>
        <p className="text-gray-600 dark:text-gray-600 mt-2">
          {showReportCenter ? t('reportCenter.description') : t('dashboard.description')}
        </p>
        {isEditMode && (
          <div className="mt-2">
            <SaveStatusIndicator 
              status={saveStatus.status}
              lastSaved={saveStatus.lastSaved}
              error={saveStatus.error}
              onRetry={saveDashboardLayout}
            />
          </div>
        )}
      </div>
      <div className="flex space-x-2">
        {isEditMode && (
          <>
            <AppleButton
              variant="outline"
              size="sm"
              onClick={undo}
              disabled={!canUndo}
              aria-label={t('dashboard.undo')}
              title={`${t('dashboard.undo')} (Cmd/Ctrl+Z)`}
              haptic="light"
            >
              <Undo2 className="w-4 h-4 mr-2" aria-hidden="true" />
              {t('dashboard.undo')}
            </AppleButton>
            <AppleButton
              variant="outline"
              size="sm"
              onClick={redo}
              disabled={!canRedo}
              aria-label={t('dashboard.redo')}
              title={`${t('dashboard.redo')} (Cmd/Ctrl+Shift+Z)`}
              haptic="light"
            >
              <Redo2 className="w-4 h-4 mr-2" aria-hidden="true" />
              {t('dashboard.redo')}
            </AppleButton>
          </>
        )}
        <AppleButton
          variant={showReportCenter ? "primary" : "outline"}
          onClick={() => setShowReportCenter(!showReportCenter)}
        >
          <FileText className="w-4 h-4 mr-2" />
          {t('reportCenter.title')}
        </AppleButton>
        {!showReportCenter && (
          <AppleButton
            variant={isEditMode ? "primary" : "outline"}
            onClick={() => {
              setIsEditMode(!isEditMode)
              if (isEditMode) saveDashboardLayout()
            }}
          >
            <Settings className="w-4 h-4 mr-2" />
            {isEditMode ? t('dashboard.finishEditing') : t('dashboard.customize')}
          </AppleButton>
        )}
      </div>
    </div>
  )

  const WidgetAddDialog = () => (
    <Dialog>
      <DialogTrigger asChild>
        <AppleButton variant="outline" className="w-full h-32 border-dashed">
          <Plus className="w-8 h-8 mb-2" />
          <span>{t('dashboard.addWidget')}</span>
        </AppleButton>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('dashboard.selectWidget')}</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto">
          {availableWidgets.map((widget) => (
            <AppleButton
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
            </AppleButton>
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

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="p-6 space-y-6">
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
                t={t}
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
            {/* Performance Trend Chart */}
            <Card className="shadow-sm hover:shadow-md transition-shadow duration-200">
              <CardHeader className="pb-4">
                <CardTitle>{t('metrics.performanceTrend')}</CardTitle>
                <CardDescription>{t('metrics.performanceDescription')}</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={performanceData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="time" />
                    <YAxis />
                    <Tooltip />
                    <Line 
                      type="monotone" 
                      dataKey="cpu" 
                      stroke="#007AFF" 
                      strokeWidth={2}
                      name="CPU (%)"
                    />
                    <Line 
                      type="monotone" 
                      dataKey="memory" 
                      stroke="#10b981" 
                      strokeWidth={2}
                      name={t('metrics.memoryUsage')}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Response Time Chart */}
            <Card className="shadow-sm hover:shadow-md transition-shadow duration-200">
              <CardHeader className="pb-4">
                <CardTitle>{t('metrics.responseTimeTrend')}</CardTitle>
                <CardDescription>{t('metrics.responseTimeDescription')}</CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
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
                      name={t('metrics.responseTime')}
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Recent Decisions - Always visible when not in edit mode */}
        {!isEditMode && (
          <Card className="shadow-sm hover:shadow-md transition-shadow duration-200">
            <CardHeader className="pb-4">
              <CardTitle>{t('decisions.title')}</CardTitle>
              <CardDescription>{t('decisions.description')}</CardDescription>
            </CardHeader>
            <CardContent className="pt-0">
              <div className="space-y-3">
                {recentDecisions.map((decision) => (
                  <div key={decision.id} className="flex items-center justify-between p-4 border rounded-lg dark:border-gray-700 hover:border-gray-300 dark:hover:border-gray-600 transition-colors duration-200 shadow-sm">
                    <div className="flex items-center space-x-4">
                      <div className={`p-2 rounded-full ${getStatusColor(decision.status)}`}>
                        {getStatusIcon(decision.status)}
                      </div>
                      <div>
                        <h4 className="font-medium dark:text-white">{decision.strategy}</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-600">{decision.impact}</p>
                        <p className="text-xs text-gray-600 dark:text-gray-600">
                          {new Date(decision.timestamp).toLocaleString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <Badge variant="outline" className={getStatusColor(decision.status)}>
                        {decision.status === 'executed' ? t('decisions.status.executed') : 
                         decision.status === 'pending' ? t('decisions.status.pending') : t('decisions.status.failed')}
                      </Badge>
                      <p className="text-sm text-gray-600 dark:text-gray-600 mt-1">
                        {t('decisions.confidence')}: {(decision.confidence * 100).toFixed(0)}%
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
              <Edit3 className="w-12 h-12 mx-auto mb-4 text-gray-600" />
              <h3 className="text-lg font-medium mb-2 dark:text-white">{t('dashboard.customize')}</h3>
              <p className="text-gray-600 dark:text-gray-600 mb-4">
                {t('dashboard.editInstructions')}
              </p>
              <div className="flex justify-center space-x-2">
                <AppleButton onClick={() => setDashboardLayout(getDefaultWidgets())}>
                  {t('dashboard.resetLayout')}
                </AppleButton>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </DndProvider>
  )
}

export default Dashboard

