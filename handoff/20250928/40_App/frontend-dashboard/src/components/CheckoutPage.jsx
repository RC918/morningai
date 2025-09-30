import React, { useState, useEffect, useCallback } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Separator } from '@/components/ui/separator'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group'
import { Skeleton } from '@/components/ui/skeleton'
import { 
  CreditCard, 
  Shield, 
  Check, 
  Star,
  Zap,
  Users,
  Clock,
  DollarSign,
  Settings
} from 'lucide-react'
import { colors, spacing, typography } from '@/lib/design-tokens'
import apiClient from '@/lib/api'

const CheckoutPage = () => {
  const [loading, setLoading] = useState(true)
  const [checkoutData, setCheckoutData] = useState(null)
  const [selectedPlan, setSelectedPlan] = useState('pro')
  const [selectedPayment, setSelectedPayment] = useState('credit_card')
  const [discountCode, setDiscountCode] = useState('')
  const [useMockData, setUseMockData] = useState(import.meta.env.VITE_USE_MOCK === 'true')
  const [billingPlans, setBillingPlans] = useState([])

  const loadBillingPlans = async () => {
    try {
      return await apiClient.getBillingPlans()
    } catch (error) {
      console.error('Failed to load billing plans:', error)
      return []
    }
  }

  const loadCheckoutData = useCallback(async () => {
    try {
      const plans = await loadBillingPlans()
      setBillingPlans(plans)
      
      if (useMockData) {
        const data = await apiClient.request('/checkout/mock')
        setCheckoutData(data)
      } else {
        const mockData = await apiClient.request('/checkout/mock')
        
        setCheckoutData({
          ...mockData,
          pricing_tiers: plans.map(plan => ({
            id: plan.id,
            name: plan.name,
            price: plan.price,
            billing: plan.interval,
            currency: plan.currency,
            popular: plan.id === 'pro',
            features: getFeaturesByPlan(plan.id)
          }))
        })
      }
      setLoading(false)
    } catch (error) {
      console.error('Failed to load checkout data:', error)
      setUseMockData(true)
      setLoading(false)
    }
  }, [useMockData])

  useEffect(() => {
    loadCheckoutData()
  }, [useMockData, loadCheckoutData])

  const getFeaturesByPlan = (planId) => {
    const features = {
      starter: [
        '基礎 AI 助手功能',
        '每月 100 次查詢',
        '標準客服支援',
        '基礎報表功能'
      ],
      pro: [
        '進階 AI 助手功能',
        '每月 1000 次查詢',
        '優先客服支援',
        '進階報表與分析',
        '自訂工作流程',
        'API 存取權限'
      ],
      enterprise: [
        '完整 AI 助手功能',
        '無限制查詢',
        '專屬客服經理',
        '完整報表與分析',
        '自訂工作流程',
        '完整 API 存取',
        '單點登入 (SSO)',
        '專屬部署選項'
      ]
    }
    return features[planId] || features.starter
  }

  const handleCheckout = async () => {
    try {
      const result = await apiClient.createCheckoutSession({
        plan_id: selectedPlan,
        payment_method: selectedPayment,
        discount_code: discountCode
      })
      
      if (result.success && result.checkout_session) {
        console.log('Checkout successful:', result)
        window.location.href = result.checkout_session.payment_url
      } else if (result.redirect_url) {
        window.location.href = result.redirect_url
      }
    } catch (error) {
      console.error('Checkout failed:', error)
      alert('結帳失敗，請稍後再試')
    }
  }

  const getPlanIcon = (planId) => {
    switch (planId) {
      case 'starter': return <Zap className="w-6 h-6" />
      case 'basic': return <Zap className="w-6 h-6" />
      case 'pro': return <Star className="w-6 h-6" />
      case 'enterprise': return <Users className="w-6 h-6" />
      default: return <Zap className="w-6 h-6" />
    }
  }

  const getPaymentIcon = (methodId) => {
    switch (methodId) {
      case 'credit_card': return <CreditCard className="w-5 h-5" />
      case 'paypal': return <DollarSign className="w-5 h-5" />
      case 'stripe': return <Shield className="w-5 h-5" />
      default: return <CreditCard className="w-5 h-5" />
    }
  }

  if (loading) {
    return (
      <div className="p-6 max-w-6xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2 space-y-6">
            <Skeleton className="h-8 w-48" aria-busy="true" />
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-64" aria-busy="true" />
              ))}
            </div>
          </div>
          <div>
            <Skeleton className="h-96" aria-busy="true" />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 max-w-6xl mx-auto">
      <div className="mb-8">
        <div className="flex justify-between items-center mb-4">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">選擇您的方案</h1>
            <p className="text-gray-600">升級到 Morning AI Pro，解鎖更多強大功能</p>
          </div>
          <div className="flex items-center space-x-2">
            <Settings className="w-4 h-4" />
            <Label htmlFor="mock-toggle" className="text-sm">使用測試資料</Label>
            <input
              id="mock-toggle"
              type="checkbox"
              checked={useMockData}
              onChange={(e) => setUseMockData(e.target.checked)}
              className="rounded"
              aria-describedby="mock-toggle-description"
            />
            <span id="mock-toggle-description" className="sr-only">
              切換使用測試資料或真實 API 資料
            </span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Pricing Plans */}
        <div className="lg:col-span-2">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
            {checkoutData?.pricing_tiers?.map((plan) => (
              <Card 
                key={plan.id}
                className={`relative cursor-pointer transition-all ${
                  selectedPlan === plan.id 
                    ? 'ring-2 ring-blue-500 shadow-lg' 
                    : 'hover:shadow-md'
                } ${plan.popular ? 'border-blue-500' : ''}`}
                onClick={() => setSelectedPlan(plan.id)}
              >
                {plan.popular && (
                  <Badge className="absolute -top-2 left-1/2 transform -translate-x-1/2 bg-blue-500">
                    最受歡迎
                  </Badge>
                )}
                <CardHeader className="text-center pb-4">
                  <div className="flex justify-center mb-2">
                    {getPlanIcon(plan.id)}
                  </div>
                  <CardTitle className="text-xl">{plan.name}</CardTitle>
                  <div className="text-3xl font-bold">
                    ${plan.price}
                    <span className="text-sm font-normal text-gray-500">/{plan.billing}</span>
                  </div>
                </CardHeader>
                <CardContent>
                  <ul className="space-y-2">
                    {plan.features.map((feature, index) => (
                      <li key={index} className="flex items-center text-sm">
                        <Check className="w-4 h-4 text-green-500 mr-2 flex-shrink-0" />
                        {feature}
                      </li>
                    ))}
                  </ul>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Payment Methods */}
          <Card>
            <CardHeader>
              <CardTitle>付款方式</CardTitle>
              <CardDescription>選擇您偏好的付款方式</CardDescription>
            </CardHeader>
            <CardContent>
              <RadioGroup value={selectedPayment} onValueChange={setSelectedPayment}>
                {checkoutData?.payment_methods?.map((method) => (
                  <div key={method.id} className="flex items-center space-x-2 p-3 border rounded-lg">
                    <RadioGroupItem value={method.id} id={method.id} />
                    <Label htmlFor={method.id} className="flex items-center cursor-pointer flex-1">
                      {getPaymentIcon(method.id)}
                      <span className="ml-2">{method.name}</span>
                      {!method.enabled && (
                        <Badge variant="secondary" className="ml-auto">即將推出</Badge>
                      )}
                    </Label>
                  </div>
                ))}
              </RadioGroup>
            </CardContent>
          </Card>
        </div>

        {/* Order Summary */}
        <div>
          <Card className="sticky top-6">
            <CardHeader>
              <CardTitle>訂單摘要</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {selectedPlan && checkoutData?.pricing_tiers && (
                <>
                  <div className="flex justify-between">
                    <span>方案</span>
                    <span className="font-medium">
                      {checkoutData.pricing_tiers.find(p => p.id === selectedPlan)?.name}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span>價格</span>
                    <span className="font-medium">
                      ${checkoutData.pricing_tiers.find(p => p.id === selectedPlan)?.price}/月
                    </span>
                  </div>
                  
                  <Separator />
                  
                  <div className="space-y-2">
                    <Label htmlFor="discount">優惠代碼</Label>
                    <div className="flex space-x-2">
                      <Input
                        id="discount"
                        placeholder="輸入優惠代碼"
                        value={discountCode}
                        onChange={(e) => setDiscountCode(e.target.value)}
                      />
                      <Button variant="outline" size="sm" aria-label="套用優惠代碼">
                        套用
                      </Button>
                    </div>
                  </div>
                  
                  {checkoutData?.discounts?.length > 0 && (
                    <div className="text-sm text-green-600">
                      <Clock className="w-4 h-4 inline mr-1" />
                      可用優惠：{checkoutData.discounts[0].code} (-{checkoutData.discounts[0].discount}%)
                    </div>
                  )}
                  
                  <Separator />
                  
                  <div className="flex justify-between text-lg font-bold">
                    <span>總計</span>
                    <span>
                      ${checkoutData.pricing_tiers.find(p => p.id === selectedPlan)?.price}/月
                    </span>
                  </div>
                  
                  <Button 
                    className="w-full" 
                    size="lg"
                    onClick={handleCheckout}
                    aria-label="進行安全結帳流程"
                  >
                    <Shield className="w-4 h-4 mr-2" aria-hidden="true" />
                    安全結帳
                  </Button>
                  
                  <div className="text-xs text-gray-500 text-center">
                    <Shield className="w-3 h-3 inline mr-1" />
                    您的付款資訊受到 256 位元 SSL 加密保護
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

export default CheckoutPage
