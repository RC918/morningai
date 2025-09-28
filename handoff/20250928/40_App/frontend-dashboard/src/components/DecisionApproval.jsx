import { useState, useEffect } from 'react'
import { 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle, 
  TrendingUp, 
  DollarSign,
  Zap,
  Info
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'

const DecisionApproval = () => {
  const { toast } = useToast()
  const [pendingDecisions, setPendingDecisions] = useState([
    {
      id: 'decision_001',
      timestamp: '2024-01-01T14:30:00Z',
      strategy: {
        name: 'CPU優化策略',
        description: '當CPU使用率超過85%時自動擴容並優化緩存配置',
        actions: [
          { type: 'scale_up', description: '增加2個計算實例', estimated_time: '3分鐘' },
          { type: 'optimize_cache', description: '調整緩存TTL為300秒', estimated_time: '30秒' }
        ]
      },
      trigger: {
        type: 'high_cpu_usage',
        value: 92,
        threshold: 85,
        duration: '5分鐘'
      },
      predicted_impact: {
        cpu_reduction: 25,
        response_time_improvement: 30,
        cost_increase: 18.50,
        confidence: 0.87
      },
      risk_assessment: {
        level: 'low',
        factors: ['已測試策略', '可回滾', '低影響範圍']
      },
      priority: 'high',
      auto_approve_in: 300 // 5分鐘後自動批准
    },
    {
      id: 'decision_002',
      timestamp: '2024-01-01T14:25:00Z',
      strategy: {
        name: '數據庫連接池優化',
        description: '調整數據庫連接池大小以應對高並發',
        actions: [
          { type: 'adjust_connection_pool', description: '將連接池從50增加到80', estimated_time: '1分鐘' }
        ]
      },
      trigger: {
        type: 'database_connection_exhaustion',
        value: 48,
        threshold: 45,
        duration: '2分鐘'
      },
      predicted_impact: {
        database_performance: 20,
        response_time_improvement: 15,
        cost_increase: 5.20,
        confidence: 0.92
      },
      risk_assessment: {
        level: 'very_low',
        factors: ['常規操作', '即時生效', '可動態調整']
      },
      priority: 'medium',
      auto_approve_in: 600
    },
    {
      id: 'decision_003',
      timestamp: '2024-01-01T14:20:00Z',
      strategy: {
        name: '緊急故障轉移',
        description: '檢測到主服務異常，建議切換到備用服務',
        actions: [
          { type: 'failover', description: '切換到備用數據中心', estimated_time: '2分鐘' },
          { type: 'notify_team', description: '通知運維團隊', estimated_time: '即時' }
        ]
      },
      trigger: {
        type: 'service_failure',
        value: 'primary_service_down',
        threshold: 'availability_below_99',
        duration: '30秒'
      },
      predicted_impact: {
        availability_restoration: 99.9,
        user_impact_reduction: 80,
        cost_increase: 50.00,
        confidence: 0.95
      },
      risk_assessment: {
        level: 'medium',
        factors: ['緊急操作', '影響用戶', '需要監控']
      },
      priority: 'critical',
      auto_approve_in: 120 // 2分鐘後自動批准
    }
  ])

  const [selectedDecision, setSelectedDecision] = useState(null)
  const [approvalComment, setApprovalComment] = useState('')

  useEffect(() => {
    // 模擬自動倒計時
    const interval = setInterval(() => {
      setPendingDecisions(prev => 
        prev.map(decision => ({
          ...decision,
          auto_approve_in: Math.max(0, decision.auto_approve_in - 1)
        }))
      )
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  const handleApprove = async (decisionId, comment = '') => {
    try {
      // 模擬API調用
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setPendingDecisions(prev => 
        prev.filter(d => d.id !== decisionId)
      )
      
      toast({
        title: "決策已批准",
        description: "策略將立即執行",
        variant: "default"
      })
      
      setSelectedDecision(null)
      setApprovalComment('')
    } catch (error) {
      toast({
        title: "批准失敗",
        description: "請稍後重試",
        variant: "destructive"
      })
    }
  }

  const handleReject = async (decisionId, comment) => {
    if (!comment.trim()) {
      toast({
        title: "請提供拒絕理由",
        description: "拒絕決策時必須說明原因",
        variant: "destructive"
      })
      return
    }

    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      setPendingDecisions(prev => 
        prev.filter(d => d.id !== decisionId)
      )
      
      toast({
        title: "決策已拒絕",
        description: "系統將尋找替代方案",
        variant: "default"
      })
      
      setSelectedDecision(null)
      setApprovalComment('')
    } catch (error) {
      toast({
        title: "拒絕失敗",
        description: "請稍後重試",
        variant: "destructive"
      })
    }
  }

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200'
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200'
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'low': return 'bg-green-100 text-green-800 border-green-200'
      default: return 'bg-gray-100 text-gray-800 border-gray-200'
    }
  }

  const getRiskColor = (level) => {
    switch (level) {
      case 'very_low': return 'text-green-600'
      case 'low': return 'text-green-500'
      case 'medium': return 'text-yellow-500'
      case 'high': return 'text-red-500'
      case 'very_high': return 'text-red-600'
      default: return 'text-gray-500'
    }
  }

  const formatTimeRemaining = (seconds) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
  }

  return (
    <div className="p-6 space-y-6">
      {/* 頁面標題 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">決策審批中心</h1>
        <p className="text-gray-600 mt-2">
          審核AI系統提出的決策建議，確保系統安全穩定運行
        </p>
      </div>

      {/* 統計摘要 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">待審批</p>
                <p className="text-2xl font-bold">{pendingDecisions.length}</p>
              </div>
              <Clock className="w-8 h-8 text-orange-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">緊急決策</p>
                <p className="text-2xl font-bold text-red-600">
                  {pendingDecisions.filter(d => d.priority === 'critical').length}
                </p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">平均信心度</p>
                <p className="text-2xl font-bold text-green-600">
                  {Math.round(pendingDecisions.reduce((acc, d) => acc + d.predicted_impact.confidence, 0) / pendingDecisions.length * 100)}%
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-green-500" />
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-600">預計成本</p>
                <p className="text-2xl font-bold text-blue-600">
                  ${pendingDecisions.reduce((acc, d) => acc + d.predicted_impact.cost_increase, 0).toFixed(2)}
                </p>
              </div>
              <DollarSign className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* 待審批決策列表 */}
      <div className="space-y-4">
        {pendingDecisions.length === 0 ? (
          <Card>
            <CardContent className="p-8 text-center">
              <CheckCircle className="w-16 h-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">沒有待審批的決策</h3>
              <p className="text-gray-600">所有決策都已處理完畢，系統運行正常</p>
            </CardContent>
          </Card>
        ) : (
          pendingDecisions.map((decision) => (
            <Card key={decision.id} className="border-l-4 border-l-orange-400">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <CardTitle className="text-lg">{decision.strategy.name}</CardTitle>
                      <Badge className={getPriorityColor(decision.priority)}>
                        {decision.priority === 'critical' ? '緊急' :
                         decision.priority === 'high' ? '高' :
                         decision.priority === 'medium' ? '中' : '低'}
                      </Badge>
                    </div>
                    <CardDescription>{decision.strategy.description}</CardDescription>
                    <p className="text-sm text-gray-500 mt-2">
                      觸發時間: {new Date(decision.timestamp).toLocaleString()}
                    </p>
                  </div>
                  
                  <div className="text-right">
                    <div className="text-sm text-gray-600 mb-2">
                      自動批准倒計時
                    </div>
                    <div className="text-lg font-mono text-orange-600">
                      {formatTimeRemaining(decision.auto_approve_in)}
                    </div>
                    <Progress 
                      value={(300 - decision.auto_approve_in) / 300 * 100} 
                      className="w-20 mt-2"
                    />
                  </div>
                </div>
              </CardHeader>
              
              <CardContent>
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  {/* 觸發條件 */}
                  <div>
                    <h4 className="font-medium mb-2">觸發條件</h4>
                    <div className="text-sm space-y-1">
                      <p><span className="text-gray-600">類型:</span> {decision.trigger.type}</p>
                      <p><span className="text-gray-600">當前值:</span> {decision.trigger.value}</p>
                      <p><span className="text-gray-600">閾值:</span> {decision.trigger.threshold}</p>
                      <p><span className="text-gray-600">持續時間:</span> {decision.trigger.duration}</p>
                    </div>
                  </div>
                  
                  {/* 預期影響 */}
                  <div>
                    <h4 className="font-medium mb-2">預期影響</h4>
                    <div className="text-sm space-y-1">
                      {Object.entries(decision.predicted_impact).map(([key, value]) => (
                        <p key={key}>
                          <span className="text-gray-600">
                            {key === 'confidence' ? '信心度' :
                             key === 'cost_increase' ? '成本增加' :
                             key === 'cpu_reduction' ? 'CPU降低' :
                             key === 'response_time_improvement' ? '響應時間改善' :
                             key}:
                          </span>{' '}
                          {key === 'cost_increase' ? `$${value}` :
                           key === 'confidence' ? `${Math.round(value * 100)}%` :
                           typeof value === 'number' ? `${value}%` : value}
                        </p>
                      ))}
                    </div>
                  </div>
                  
                  {/* 風險評估 */}
                  <div>
                    <h4 className="font-medium mb-2">風險評估</h4>
                    <div className="text-sm">
                      <p className="mb-2">
                        <span className="text-gray-600">風險等級:</span>{' '}
                        <span className={getRiskColor(decision.risk_assessment.level)}>
                          {decision.risk_assessment.level === 'very_low' ? '極低' :
                           decision.risk_assessment.level === 'low' ? '低' :
                           decision.risk_assessment.level === 'medium' ? '中' :
                           decision.risk_assessment.level === 'high' ? '高' : '極高'}
                        </span>
                      </p>
                      <div className="space-y-1">
                        {decision.risk_assessment.factors.map((factor, index) => (
                          <p key={index} className="text-gray-600">• {factor}</p>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>
                
                {/* 執行步驟 */}
                <div className="mt-4">
                  <h4 className="font-medium mb-2">執行步驟</h4>
                  <div className="space-y-2">
                    {decision.strategy.actions.map((action, index) => (
                      <div key={index} className="flex items-center space-x-3 p-2 bg-gray-50 rounded">
                        <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-medium">
                          {index + 1}
                        </div>
                        <div className="flex-1">
                          <p className="text-sm font-medium">{action.description}</p>
                          <p className="text-xs text-gray-500">預計耗時: {action.estimated_time}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
                
                {/* 操作按鈕 */}
                <div className="flex items-center justify-end space-x-3 mt-6">
                  <Dialog>
                    <DialogTrigger asChild>
                      <Button variant="outline" onClick={() => setSelectedDecision(decision)}>
                        <Info className="w-4 h-4 mr-2" />
                        詳細信息
                      </Button>
                    </DialogTrigger>
                    <DialogContent className="max-w-2xl">
                      <DialogHeader>
                        <DialogTitle>{decision.strategy.name}</DialogTitle>
                        <DialogDescription>
                          決策詳細信息和審批操作
                        </DialogDescription>
                      </DialogHeader>
                      
                      <div className="space-y-4">
                        <div>
                          <Label htmlFor="comment">審批意見 (可選)</Label>
                          <Textarea
                            id="comment"
                            placeholder="請輸入審批意見或備註..."
                            value={approvalComment}
                            onChange={(e) => setApprovalComment(e.target.value)}
                            className="mt-2"
                          />
                        </div>
                        
                        <div className="flex items-center justify-end space-x-3">
                          <Button
                            variant="outline"
                            onClick={() => handleReject(decision.id, approvalComment)}
                          >
                            <XCircle className="w-4 h-4 mr-2" />
                            拒絕
                          </Button>
                          <Button
                            onClick={() => handleApprove(decision.id, approvalComment)}
                          >
                            <CheckCircle className="w-4 h-4 mr-2" />
                            批准執行
                          </Button>
                        </div>
                      </div>
                    </DialogContent>
                  </Dialog>
                  
                  <Button
                    variant="outline"
                    onClick={() => handleReject(decision.id, '手動拒絕')}
                  >
                    <XCircle className="w-4 h-4 mr-2" />
                    拒絕
                  </Button>
                  
                  <Button
                    onClick={() => handleApprove(decision.id)}
                  >
                    <CheckCircle className="w-4 h-4 mr-2" />
                    批准
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>
    </div>
  )
}

export default DecisionApproval

