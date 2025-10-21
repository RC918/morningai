import React, { useEffect } from 'react'
import { useTranslation } from 'react-i18next'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, ArrowLeft, Download, Mail } from 'lucide-react'
import { useNavigate, useSearchParams } from 'react-router-dom'

const CheckoutSuccess = () => {
  const { t } = useTranslation()
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
          <CardTitle className="text-2xl text-green-700">{t('checkoutSuccess.title')}</CardTitle>
        </CardHeader>
        <CardContent className="space-y-6 text-center">
          <div>
            <p className="text-gray-600 mb-2">{t('checkoutSuccess.thankYou')}</p>
            <Badge className="bg-blue-100 text-blue-800">
              {t('checkoutSuccess.planActivated', { plan: planName })}
            </Badge>
          </div>

          {sessionId && (
            <div className="bg-gray-50 p-4 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">{t('checkoutSuccess.orderId')}</p>
              <p className="font-mono text-sm">{sessionId}</p>
            </div>
          )}

          <div className="space-y-3">
            <p className="text-sm text-gray-600">
              {t('checkoutSuccess.emailSent')}
            </p>
            
            <div className="flex flex-col sm:flex-row gap-3">
              <Button 
                onClick={() => navigate('/dashboard')}
                className="flex-1"
                aria-label={t('checkoutSuccess.getStartedAria')}
              >
                <ArrowLeft className="w-4 h-4 mr-2" aria-hidden="true" />
                {t('checkoutSuccess.getStarted')}
              </Button>
              
              <Button 
                variant="outline" 
                onClick={() => window.open('/api/billing/invoice/' + sessionId, '_blank')}
                className="flex-1"
                aria-label={t('checkoutSuccess.downloadInvoiceAria')}
              >
                <Download className="w-4 h-4 mr-2" aria-hidden="true" />
                {t('checkoutSuccess.downloadInvoice')}
              </Button>
            </div>
          </div>

          <div className="text-xs text-gray-500 pt-4 border-t">
            <Mail className="w-3 h-3 inline mr-1" aria-hidden="true" />
            {t('checkoutSuccess.support')}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default CheckoutSuccess
