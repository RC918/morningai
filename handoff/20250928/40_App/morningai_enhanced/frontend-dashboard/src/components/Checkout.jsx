import React, { useState, useEffect } from 'react'
import { Check, CreditCard, Sparkles, ArrowRight, ArrowLeft } from 'lucide-react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import mockData from '@/mocks/checkout.json'

const Checkout = () => {
  const [plans, setPlans] = useState([])
  const [currentStep, setCurrentStep] = useState(1)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    cardNumber: '',
    expiry: '',
    cvv: ''
  })
  const [errors, setErrors] = useState({})
  const [isProcessing, setIsProcessing] = useState(false)

  useEffect(() => {
    setPlans(mockData.plans)
  }, [])

  const handlePlanSelect = (plan) => {
    setSelectedPlan(plan)
    if (plan.price === 0) {
      setCurrentStep(3)
    } else {
      setCurrentStep(2)
    }
  }

  const handleInputChange = (field, value) => {
    setFormData({ ...formData, [field]: value })
    if (errors[field]) {
      setErrors({ ...errors, [field]: '' })
    }
  }

  const validateForm = () => {
    const newErrors = {}
    if (!formData.name.trim()) newErrors.name = '請輸入姓名'
    if (!formData.email.trim()) newErrors.email = '請輸入電子郵件'
    else if (!/\S+@\S+\.\S+/.test(formData.email)) newErrors.email = '電子郵件格式不正確'
    if (!formData.cardNumber.trim()) newErrors.cardNumber = '請輸入卡號'
    else if (formData.cardNumber.replace(/\s/g, '').length !== 16) newErrors.cardNumber = '卡號必須為 16 位數字'
    if (!formData.expiry.trim()) newErrors.expiry = '請輸入有效期限'
    if (!formData.cvv.trim()) newErrors.cvv = '請輸入 CVV'
    else if (formData.cvv.length !== 3) newErrors.cvv = 'CVV 必須為 3 位數字'
    
    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!validateForm()) return

    setIsProcessing(true)
    await new Promise(resolve => setTimeout(resolve, 2000))
    setIsProcessing(false)
    setCurrentStep(3)
  }

  const formatCardNumber = (value) => {
    const v = value.replace(/\s+/g, '').replace(/[^0-9]/gi, '')
    const matches = v.match(/\d{4,16}/g)
    const match = (matches && matches[0]) || ''
    const parts = []
    for (let i = 0, len = match.length; i < len; i += 4) {
      parts.push(match.substring(i, i + 4))
    }
    return parts.length ? parts.join(' ') : value
  }

  const StepIndicator = ({ step, title, active, completed }) => (
    <div className="flex items-center">
      <div className={`w-8 h-8 rounded-full flex items-center justify-center font-medium transition-all duration-[var(--duration-normal)] ${
        completed ? 'bg-[var(--color-success-500)] text-white' :
        active ? 'bg-[var(--color-primary-500)] text-white' :
        'bg-gray-200 text-gray-500'
      }`}>
        {completed ? <Check className="w-5 h-5" /> : step}
      </div>
      <span className={`ml-2 text-sm font-medium hidden sm:inline ${
        active ? 'text-gray-900' : 'text-gray-500'
      }`}>
        {title}
      </span>
    </div>
  )

  return (
    <div className="min-h-screen bg-[var(--color-background-base)] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">選擇您的方案</h1>
          <p className="text-gray-600">開始使用 Morning AI，提升您的工作效率</p>
        </div>

        <div className="flex items-center justify-center gap-4 mb-8">
          <StepIndicator step={1} title="選擇方案" active={currentStep === 1} completed={currentStep > 1} />
          <div className="w-12 h-0.5 bg-gray-300" />
          <StepIndicator step={2} title="付款資訊" active={currentStep === 2} completed={currentStep > 2} />
          <div className="w-12 h-0.5 bg-gray-300" />
          <StepIndicator step={3} title="完成" active={currentStep === 3} completed={false} />
        </div>

        {currentStep === 1 && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {plans.map((plan) => (
              <Card
                key={plan.id}
                className={`relative cursor-pointer transition-all duration-[var(--duration-normal)] hover:shadow-xl ${
                  plan.popular ? 'border-[var(--color-primary-500)] border-2 shadow-lg' : 'border-gray-200'
                }`}
                onClick={() => handlePlanSelect(plan)}
              >
                {plan.popular && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2">
                    <Badge className="bg-[var(--color-primary-500)] text-white px-4 py-1">
                      最受歡迎
                    </Badge>
                  </div>
                )}
                <CardHeader className="text-center pb-4">
                  <CardTitle className="text-2xl">{plan.name}</CardTitle>
                  <div className="mt-4">
                    <span className="text-5xl font-bold text-gray-900">${plan.price}</span>
                    <span className="text-gray-500 ml-2">/ {plan.interval === 'month' ? '月' : '年'}</span>
                  </div>
                  {plan.trial && (
                    <Badge variant="outline" className="mt-3 border-[var(--color-accent-purple-500)] text-[var(--color-accent-purple-500)]">
                      <Sparkles className="w-3 h-3 mr-1" />
                      {plan.trialDays} 天免費試用
                    </Badge>
                  )}
                </CardHeader>
                <CardContent>
                  <ul className="space-y-3 mb-6">
                    {plan.features.map((feature, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <Check className="w-5 h-5 text-[var(--color-success-500)] mt-0.5 flex-shrink-0" />
                        <span className="text-gray-700">{feature}</span>
                      </li>
                    ))}
                  </ul>
                  <Button
                    className={`w-full transition-colors duration-[var(--duration-fast)] ${
                      plan.popular
                        ? 'bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)]'
                        : 'bg-gray-600 hover:bg-gray-700'
                    }`}
                  >
                    選擇 {plan.name}
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        {currentStep === 2 && selectedPlan && (
          <div className="max-w-2xl mx-auto">
            <Card className="border-none shadow-xl">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div>
                    <CardTitle>付款資訊</CardTitle>
                    <CardDescription>安全加密，保護您的隱私</CardDescription>
                  </div>
                  <CreditCard className="w-8 h-8 text-[var(--color-primary-500)]" />
                </div>
              </CardHeader>
              <CardContent>
                <div className="mb-6 p-4 bg-gray-50 rounded-lg">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="font-medium text-gray-900">{selectedPlan.name} 方案</p>
                      <p className="text-sm text-gray-600">
                        {selectedPlan.trial && `${selectedPlan.trialDays} 天免費試用後 `}
                        ${selectedPlan.price}/{selectedPlan.interval === 'month' ? '月' : '年'}
                      </p>
                    </div>
                    <p className="text-2xl font-bold text-gray-900">${selectedPlan.price}</p>
                  </div>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                  <div>
                    <Label htmlFor="name">姓名</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="張三"
                      className={errors.name ? 'border-red-500' : ''}
                    />
                    {errors.name && <p className="text-sm text-red-600 mt-1">{errors.name}</p>}
                  </div>

                  <div>
                    <Label htmlFor="email">電子郵件</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="your@email.com"
                      className={errors.email ? 'border-red-500' : ''}
                    />
                    {errors.email && <p className="text-sm text-red-600 mt-1">{errors.email}</p>}
                  </div>

                  <div>
                    <Label htmlFor="cardNumber">信用卡號</Label>
                    <Input
                      id="cardNumber"
                      value={formData.cardNumber}
                      onChange={(e) => handleInputChange('cardNumber', formatCardNumber(e.target.value))}
                      placeholder="1234 5678 9012 3456"
                      maxLength={19}
                      className={errors.cardNumber ? 'border-red-500' : ''}
                    />
                    {errors.cardNumber && <p className="text-sm text-red-600 mt-1">{errors.cardNumber}</p>}
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="expiry">有效期限</Label>
                      <Input
                        id="expiry"
                        value={formData.expiry}
                        onChange={(e) => handleInputChange('expiry', e.target.value)}
                        placeholder="MM/YY"
                        maxLength={5}
                        className={errors.expiry ? 'border-red-500' : ''}
                      />
                      {errors.expiry && <p className="text-sm text-red-600 mt-1">{errors.expiry}</p>}
                    </div>
                    <div>
                      <Label htmlFor="cvv">CVV</Label>
                      <Input
                        id="cvv"
                        value={formData.cvv}
                        onChange={(e) => handleInputChange('cvv', e.target.value.replace(/\D/g, ''))}
                        placeholder="123"
                        maxLength={3}
                        className={errors.cvv ? 'border-red-500' : ''}
                      />
                      {errors.cvv && <p className="text-sm text-red-600 mt-1">{errors.cvv}</p>}
                    </div>
                  </div>

                  <Alert className="bg-blue-50 border-blue-200">
                    <AlertDescription className="text-sm text-gray-700">
                      您的付款資訊已透過業界標準 SSL 加密技術保護
                    </AlertDescription>
                  </Alert>

                  <div className="flex gap-3 pt-4">
                    <Button
                      type="button"
                      variant="outline"
                      onClick={() => setCurrentStep(1)}
                      className="flex-1"
                    >
                      <ArrowLeft className="w-4 h-4 mr-2" />
                      返回
                    </Button>
                    <Button
                      type="submit"
                      disabled={isProcessing}
                      className="flex-1 bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)]"
                    >
                      {isProcessing ? '處理中...' : `確認付款 $${selectedPlan.price}`}
                      {!isProcessing && <ArrowRight className="w-4 h-4 ml-2" />}
                    </Button>
                  </div>
                </form>
              </CardContent>
            </Card>
          </div>
        )}

        {currentStep === 3 && (
          <div className="max-w-2xl mx-auto">
            <Card className="border-none shadow-xl text-center">
              <CardContent className="pt-12 pb-12">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <Check className="w-10 h-10 text-[var(--color-success-500)]" />
                </div>
                <h2 className="text-3xl font-bold text-gray-900 mb-4">訂閱成功！</h2>
                <p className="text-gray-600 mb-8">
                  {selectedPlan?.trial
                    ? `您的 ${selectedPlan.trialDays} 天免費試用已開始`
                    : '歡迎加入 Morning AI'}
                </p>
                <div className="bg-gray-50 rounded-lg p-6 mb-8">
                  <h3 className="font-medium text-gray-900 mb-4">接下來的步驟</h3>
                  <ul className="space-y-3 text-left">
                    <li className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-[var(--color-primary-500)] text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium">
                        1
                      </div>
                      <span className="text-gray-700">設置您的個人資料和偏好</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-[var(--color-primary-500)] text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium">
                        2
                      </div>
                      <span className="text-gray-700">啟動您的第一個 AI Agent</span>
                    </li>
                    <li className="flex items-start gap-3">
                      <div className="w-6 h-6 bg-[var(--color-primary-500)] text-white rounded-full flex items-center justify-center flex-shrink-0 text-sm font-medium">
                        3
                      </div>
                      <span className="text-gray-700">探索自動化工作流程</span>
                    </li>
                  </ul>
                </div>
                <div className="flex gap-3">
                  <Button
                    variant="outline"
                    onClick={() => window.location.href = '/settings'}
                    className="flex-1"
                  >
                    前往設定
                  </Button>
                  <Button
                    onClick={() => window.location.href = '/'}
                    className="flex-1 bg-[var(--color-primary-500)] hover:bg-[var(--color-primary-600)]"
                  >
                    開始使用
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}

export default Checkout
