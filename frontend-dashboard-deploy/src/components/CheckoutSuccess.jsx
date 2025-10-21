import React, { useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, ArrowLeft, Download, Mail } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const CheckoutSuccess = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const sessionId = searchParams.get('session_id')
  const planName = searchParams.get('plan') || 'Pro'

  useEffect(() => {
    if (window.gtag) {
      window.gtag('event', 'purchase', {
        transaction_id: sessionId,
        value: 0,
        currency: 'USD'
      })
    }
  }, [sessionId])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center pb-4">
          <div className="flex justify-center mb-4">
            <CheckCircle className="w-16 h-16 text-green-500" aria-hidden="true" />
          </div>
          <CardTitle className="text-2xl text-green-700">付款成功！</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 text-center">
          <div>
            <p className="text-gray-600 mb-2">感謝您選擇 Morning AI</p>
            <Badge className="bg-blue-100 text-blue-800">
              {planName} 方案已啟用
            </Badge>
          </div>

          {sessionId && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">訂單編號</p>
              <p className="font-mono text-sm">{sessionId}</p>
            </div>
          )}

          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              確認郵件已發送至您的信箱，包含詳細的訂閱資訊和發票。
            </p>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={() => navigate('/dashboard')}
                className="flex-1"
                aria-label="前往儀表板開始使用"
              >
                <ArrowLeft className="w-4 h-4 mr-2" aria-hidden="true" />
                開始使用
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => window.open('/api/billing/invoice/' + sessionId, '_blank')}
                className="flex-1"
                aria-label="下載發票"
              >
                <Download className="w-4 h-4 mr-2" aria-hidden="true" />
                下載發票
              </Button>
            </div>
          </div>

          <div className="text-xs text-gray-500 pt-4 border-t">
            <Mail className="w-3 h-3 inline mr-1" aria-hidden="true" />
            如有任何問題，請聯繫客服：support@morningai.com
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CheckoutSuccess
