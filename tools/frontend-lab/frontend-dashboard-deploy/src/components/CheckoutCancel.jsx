import React from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { XCircle, ArrowLeft, RefreshCw, MessageCircle } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const CheckoutCancel = () => {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const reason = searchParams.get('reason') || 'user_cancelled'

  const getReasonMessage = (reason) => {
    switch (reason) {
      case 'payment_failed':
        return '付款處理失敗，請檢查您的付款資訊'
      case 'session_expired':
        return '付款會話已過期，請重新開始'
      case 'user_cancelled':
      default:
        return '您已取消付款流程'
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-6">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center pb-4">
          <div className="flex justify-center mb-4">
            <XCircle className="w-16 h-16 text-orange-500" aria-hidden="true" />
          </div>
          <CardTitle className="text-2xl text-orange-700">付款已取消</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 text-center">
          <div>
            <p className="text-gray-600 mb-4">
              {getReasonMessage(reason)}
            </p>
            <p className="text-sm text-gray-500">
              您的帳戶未被收費，可以隨時重新嘗試升級。
            </p>
          </div>

          <div className="space-y-3">
            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={() => navigate('/checkout')}
                className="flex-1"
                aria-label="重新選擇方案"
              >
                <RefreshCw className="w-4 h-4 mr-2" aria-hidden="true" />
                重新選擇方案
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => navigate('/dashboard')}
                className="flex-1"
                aria-label="返回儀表板"
              >
                <ArrowLeft className="w-4 h-4 mr-2" aria-hidden="true" />
                返回儀表板
              </Button>
            </div>
          </div>

          <div className="text-xs text-gray-500 pt-4 border-t">
            <MessageCircle className="w-3 h-3 inline mr-1" aria-hidden="true" />
            需要協助？聯繫客服：support@morningai.com
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CheckoutCancel
