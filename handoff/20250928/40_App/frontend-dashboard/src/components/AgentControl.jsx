import React, { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Badge } from '@/components/ui/badge'
import { Bot, GitPullRequest, CheckCircle, Clock, XCircle, ExternalLink, RefreshCw } from 'lucide-react'
import apiClient from '@/lib/api'

const AgentControl = () => {
  const [topic, setTopic] = useState('Morning AI Platform')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [checkingStatus, setCheckingStatus] = useState(false)

  const handleGenerateFAQ = async () => {
    setLoading(true)
    setResult(null)
    try {
      const response = await apiClient.request('/agent/faq/generate', {
        method: 'POST',
        body: JSON.stringify({ topic })
      })
      
      setResult(response)
    } catch (error) {
      console.error('Failed to generate FAQ:', error)
      setResult({
        success: false,
        error: error.message,
        message: "Failed to generate FAQ"
      })
    } finally {
      setLoading(false)
    }
  }

  const handleCheckStatus = async () => {
    if (!result?.trace_id) return
    
    setCheckingStatus(true)
    try {
      const response = await apiClient.request(`/agent/faq/check/${result.trace_id}`)
      
      setResult(prev => ({
        ...prev,
        ci_state: response.ci_state,
        ci_details: response.ci_details,
        last_checked: new Date().toISOString()
      }))
    } catch (error) {
      console.error('Failed to check status:', error)
    } finally {
      setCheckingStatus(false)
    }
  }

  const getCIStatusColor = (state) => {
    switch (state) {
      case 'success': return 'bg-green-100 text-green-800'
      case 'pending': return 'bg-yellow-100 text-yellow-800'
      case 'failure': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getCIStatusIcon = (state) => {
    switch (state) {
      case 'success': return <CheckCircle className="w-4 h-4" />
      case 'pending': return <Clock className="w-4 h-4" />
      case 'failure': return <XCircle className="w-4 h-4" />
      default: return <RefreshCw className="w-4 h-4" />
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Agent MVP 控制台</h1>
        <p className="text-gray-600 mt-2">
          測試 FAQ → PR → CI → Merge 自動化流程
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Bot className="w-5 h-5 mr-2" />
            FAQ 生成器
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <label htmlFor="topic-input" className="block text-sm font-medium mb-2">主題</label>
            <Input
              id="topic-input"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="輸入 FAQ 主題..."
              disabled={loading}
            />
          </div>
          
          <Button 
            onClick={handleGenerateFAQ}
            disabled={loading}
            className="w-full"
          >
            {loading ? (
              <>
                <Clock className="w-4 h-4 mr-2 animate-spin" />
                生成中...
              </>
            ) : (
              <>
                <GitPullRequest className="w-4 h-4 mr-2" />
                生成 FAQ 並建立 PR
              </>
            )}
          </Button>

          {result && (
            <div className="mt-4 p-4 border rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center">
                  {result.success ? (
                    <CheckCircle className="w-5 h-5 text-green-500 mr-2" />
                  ) : (
                    <XCircle className="w-5 h-5 text-red-500 mr-2" />
                  )}
                  <Badge variant={result.success ? "default" : "destructive"}>
                    {result.success ? "成功" : "失敗"}
                  </Badge>
                </div>
                
                {result.success && result.trace_id && (
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleCheckStatus}
                    disabled={checkingStatus}
                  >
                    {checkingStatus ? (
                      <Clock className="w-4 h-4 mr-1 animate-spin" />
                    ) : (
                      <RefreshCw className="w-4 h-4 mr-1" />
                    )}
                    檢查狀態
                  </Button>
                )}
              </div>
              
              {result.success ? (
                <div className="space-y-3 text-sm">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                      <p className="font-medium text-gray-700">Trace ID</p>
                      <p className="font-mono text-xs bg-gray-100 p-1 rounded">{result.trace_id}</p>
                    </div>
                    <div>
                      <p className="font-medium text-gray-700">PR Number</p>
                      <p>#{result.pr_number}</p>
                    </div>
                  </div>
                  
                  <div>
                    <p className="font-medium text-gray-700 mb-1">PR URL</p>
                    <a 
                      href={result.pr_url} 
                      target="_blank" 
                      rel="noopener noreferrer" 
                      className="text-blue-600 hover:underline flex items-center"
                    >
                      {result.pr_url}
                      <ExternalLink className="w-3 h-3 ml-1" />
                    </a>
                  </div>

                  {result.ci_state && (
                    <div>
                      <p className="font-medium text-gray-700 mb-2">CI 狀態</p>
                      <div className="flex items-center space-x-2">
                        <Badge className={getCIStatusColor(result.ci_state)}>
                          {getCIStatusIcon(result.ci_state)}
                          <span className="ml-1">
                            {result.ci_state === 'success' ? '通過' :
                             result.ci_state === 'pending' ? '進行中' :
                             result.ci_state === 'failure' ? '失敗' : '未知'}
                          </span>
                        </Badge>
                      </div>
                      
                      {result.ci_details && result.ci_details.length > 0 && (
                        <div className="mt-2">
                          <p className="text-xs text-gray-600 mb-1">詳細狀態:</p>
                          <div className="space-y-1">
                            {result.ci_details.map((detail, index) => (
                              <p key={index} className="text-xs font-mono bg-gray-50 p-1 rounded">
                                {detail}
                              </p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {result.last_checked && (
                    <p className="text-xs text-gray-500">
                      最後檢查: {new Date(result.last_checked).toLocaleString()}
                    </p>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <p className="text-sm text-red-600 font-medium">{result.message}</p>
                  {result.error && (
                    <p className="text-xs text-gray-600 font-mono bg-red-50 p-2 rounded">
                      {result.error}
                    </p>
                  )}
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>工作流程說明</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-3 text-sm">
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">1</div>
              <p>Agent 根據主題生成 FAQ 內容</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">2</div>
              <p>自動建立新分支並提交變更</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">3</div>
              <p>建立 Pull Request 並附上 Trace ID</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">4</div>
              <p>CI 系統自動執行檢查</p>
            </div>
            <div className="flex items-center space-x-3">
              <div className="w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-medium">5</div>
              <p>通過檢查後可手動或自動合併</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default AgentControl
