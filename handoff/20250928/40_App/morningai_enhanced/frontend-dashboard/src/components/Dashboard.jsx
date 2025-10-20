import { useState, useEffect, useCallback } from 'react'
import { useTranslation } from 'react-i18next'
import { DndProvider, useDrag, useDrop } from 'react-dnd'
import { HTML5Backend } from 'react-dnd-html5-backend'
import { motion, AnimatePresence } from 'framer-motion'
import { 
  Activity, TrendingUp, TrendingDown, AlertTriangle, CheckCircle,
  Clock, DollarSign, Cpu, MemoryStick, Zap, Settings, Download,
  Plus, Trash2, Edit3, FileText, Grid3X3
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
import apiClient from '@/lib/api'
import { safeInterval } from '@/utils/safeInterval'

const DraggableWidget = ({ widget, index, moveWidget, onRemove, isEditMode }) => {
  const { t } = useTranslation()
  
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
    <motion.div
      ref={(node) => drag(drop(node))}
      className={`relative ${isDragging ? 'opacity-50' : ''} ${isEditMode ? 'cursor-move' : ''}`}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.9 }}
      transition={{ duration: 0.3 }}
      whileHover={isEditMode ? { scale: 1.02 } : {}}
    >
      {isEditMode && (
        <Button
          variant="destructive"
          size="sm"
          className="absolute top-2 right-2 z-10"
          onClick={() => onRemove(index)}
          aria-label={t('dashboard.removeWidget')}
        >
          <Trash2 className="w-4 h-4" aria-hidden="true" />
        </Button>
      )}
      {widget.component}
    </motion.div>
  )
}

const Dashboard = () => {
  const { t } = useTranslation()
  
  const [isLoading, setIsLoading] = useState(true)
  const [isEditMode, setIsEditMode] = useState(false)
  const [showReportCenter, setShowReportCenter] = useState(false)
  const [availableWidgets, setAvailableWidgets] = useState([])
  const [dashboardLayout, setDashboardLayout] = useState([])
  const [dashboardData, setDashboardData] = useState({})
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
      strategy: 'CPU Optimization Strategy',
      status: 'executed',
      impact: '+15% Performance Improvement',
      confidence: 0.87
    },
    {
      id: 2,
      timestamp: '2024-01-01T14:15:00Z',
      strategy: 'Cache Optimization',
      status: 'pending',
      impact: 'Expected +20% Response Speed',
      confidence: 0.92
    },
    {
      id: 3,
      timestamp: '2024-01-01T14:00:00Z',
      strategy: 'Auto Scaling',
      status: 'executed',
      impact: 'Processing Capacity +50%',
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
    // 模擬實時數據更新
    const stop = safeInterval(() => {
      setSystemMetrics(prev => ({
        ...prev,
        cpu_usage: Math.max(50, Math.min(90, prev.cpu_usage + (Math.random() - 0.5) * 10)),
        memory_usage: Math.max(40, Math.min(85, prev.memory_usage + (Math.random() - 0.5) * 8)),
        response_time: Math.max(100, Math.min(300, prev.response_time + (Math.random() - 0.5) * 20))
      }))
      
      if (!isEditMode) {
        loadDashboardData()
      }
    }, 5000)

    return stop
  }, [isEditMode, loadDashboardData])


  const saveDashboardLayout = async () => {
    try {
      await apiClient.request('/dashboard/layouts', {
        method: 'POST',
        body: JSON.stringify({
          user_id: 'default',
          layout: { widgets: dashboardLayout.map(w => ({ id: w.id, position: w.position })) }
        })
      })
    } catch (error) {
      console.error('Failed to save dashboard layout:', error)
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
          {showReportCenter ? t('reportCenter.title') : t('dashboard.title')}
        </h1>
        <p className="text-gray-600 mt-2">
          {showReportCenter ? t('reportCenter.description') : t('dashboard.description')}
        </p>
      </div>
      <div className="flex space-x-2">
        <Button
          variant={showReportCenter ? "default" : "outline"}
          onClick={() => setShowReportCenter(!showReportCenter)}
        >
          <FileText className="w-4 h-4 mr-2" />
          {t('reportCenter.title')}
        </Button>
        {!showReportCenter && (
          <Button
            variant={isEditMode ? "default" : "outline"}
            onClick={() => {
              setIsEditMode(!isEditMode)
              if (isEditMode) saveDashboardLayout()
            }}
          >
            <Settings className="w-4 h-4 mr-2" />
            {isEditMode ? t('dashboard.finishEditing') : t('dashboard.customize')}
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
          <span>{t('dashboard.addWidget')}</span>
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t('dashboard.selectWidget')}</DialogTitle>
        </DialogHeader>
        <div className="grid grid-cols-2 gap-3 max-h-96 overflow-y-auto">
          {availableWidgets.map((widget) => (
            <Button
              key={widget.id}
              variant="outline"
              className="h-20 flex-col"
              onClick={() => {
                addWidget(widget.id)
                document.querySelector('[data-state="open"]')?.click()
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

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="p-4 sm:p-6 space-y-4 sm:space-y-6">
        <DashboardToolbar />

        {/* Customizable Dashboard Widgets */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
          <AnimatePresence mode="popLayout">
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
          </AnimatePresence>
          
          {isEditMode && (
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.3 }}
            >
              <WidgetAddDialog />
            </motion.div>
          )}
        </div>

        {/* Performance Charts - Always visible */}
        {!isEditMode && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
            <Card>
              <CardHeader>
                <CardTitle>{t('metrics.performanceTrend')}</CardTitle>
                <CardDescription>{t('metrics.performanceDescription')}</CardDescription>
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
                      name={t('metrics.memoryUsage') + ' (%)'}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>{t('metrics.responseTimeTrend')}</CardTitle>
                <CardDescription>{t('metrics.responseTimeDescription')}</CardDescription>
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
                      name={t('metrics.responseTime') + ' (ms)'}
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
              <CardTitle>{t('decisions.title')}</CardTitle>
              <CardDescription>{t('decisions.description')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {recentDecisions.map((decision, index) => (
                  <motion.div 
                    key={decision.id} 
                    className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow"
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: index * 0.1 }}
                    whileHover={{ scale: 1.01 }}
                  >
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
                        {t(`decisions.status.${decision.status}`)}
                      </Badge>
                      <p className="text-sm text-gray-600 mt-1">
                        {t('decisions.confidence')}: {(decision.confidence * 100).toFixed(0)}%
                      </p>
                    </div>
                  </motion.div>
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
              <h3 className="text-lg font-medium mb-2">{t('dashboard.customize')}</h3>
              <p className="text-gray-600 mb-4">
                {t('dashboard.editInstructions')}
              </p>
              <div className="flex justify-center space-x-2">
                <Button onClick={() => setDashboardLayout(getDefaultWidgets())}>
                  {t('dashboard.resetLayout')}
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

