import { useState, useEffect } from 'react'
import { 
  CheckCircle, 
  XCircle, 
  AlertTriangle, 
  Clock,
  Wifi,
  WifiOff
} from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import config from '../config'

const CloudStatus = () => {
  const [cloudStatus, setCloudStatus] = useState({})
  const [loading, setLoading] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(null)

  useEffect(() => {
    const fetchCloudStatus = async () => {
      try {
        const response = await fetch(`${config.apiBaseUrl}/api/cloud/status`)
        if (response.ok) {
          const data = await response.json()
          setCloudStatus(data.services)
          setLastUpdate(new Date(data.timestamp))
        }
      } catch (error) {
        console.error('Failed to fetch cloud status:', error)
      } finally {
        setLoading(false)
      }
    }

    fetchCloudStatus()
    const interval = setInterval(fetchCloudStatus, 30000) // Update every 30 seconds

    return () => clearInterval(interval)
  }, [])

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy': return <CheckCircle className="w-5 h-5 text-green-500" />
      case 'unhealthy': return <XCircle className="w-5 h-5 text-red-500" />
      case 'not_configured': return <AlertTriangle className="w-5 h-5 text-yellow-500" />
      case 'error': return <WifiOff className="w-5 h-5 text-red-500" />
      default: return <Clock className="w-5 h-5 text-gray-500" />
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return 'bg-green-100 text-green-800'
      case 'unhealthy': return 'bg-red-100 text-red-800'
      case 'not_configured': return 'bg-yellow-100 text-yellow-800'
      case 'error': return 'bg-red-100 text-red-800'
      default: return 'bg-gray-100 text-gray-800'
    }
  }

  const getStatusText = (status) => {
    switch (status) {
      case 'healthy': return '正常'
      case 'unhealthy': return '異常'
      case 'not_configured': return '未配置'
      case 'error': return '錯誤'
      default: return '未知'
    }
  }

  const serviceNames = {
    sentry: 'Sentry (錯誤追蹤)',
    cloudflare: 'Cloudflare (CDN)',
    upstash: 'Upstash (Redis)',
    vercel: 'Vercel (前端部署)',
    render: 'Render (後端部署)',
    supabase: 'Supabase (數據庫)'
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>雲端服務狀態</CardTitle>
          <CardDescription>檢查中...</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center space-x-2">
          <Wifi className="w-5 h-5" />
          <span>雲端服務狀態</span>
        </CardTitle>
        <CardDescription>
          監控所有集成的雲端服務健康狀態
          {lastUpdate && (
            <span className="block text-xs text-gray-500 mt-1">
              最後更新: {lastUpdate.toLocaleString()}
            </span>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(cloudStatus).map(([service, status]) => (
            <div key={service} className="flex items-center justify-between p-3 border rounded-lg">
              <div className="flex items-center space-x-3">
                {getStatusIcon(status.status)}
                <div>
                  <h4 className="font-medium">{serviceNames[service] || service}</h4>
                  {status.response_time && (
                    <p className="text-xs text-gray-500">
                      響應時間: {(status.response_time * 1000).toFixed(0)}ms
                    </p>
                  )}
                  {status.message && (
                    <p className="text-xs text-gray-500">{status.message}</p>
                  )}
                </div>
              </div>
              <Badge className={getStatusColor(status.status)}>
                {getStatusText(status.status)}
              </Badge>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

export default CloudStatus
