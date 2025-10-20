import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import {
  Zap, Shield, TrendingUp, Users, CheckCircle, ArrowRight,
  BarChart3, Cpu, Clock, DollarSign
} from 'lucide-react'

const LandingPage = ({ onGetStarted }) => {
  const navigate = useNavigate()

  const handleGetStarted = () => {
    if (onGetStarted) {
      onGetStarted()
    } else {
      navigate('/login')
    }
  }

  const features = [
    {
      icon: <Zap className="w-6 h-6" />,
      title: 'AI 驅動自動化',
      description: '智能決策引擎自動優化系統性能與資源配置'
    },
    {
      icon: <Shield className="w-6 h-6" />,
      title: '人機協作審批',
      description: '關鍵決策需人工審批，確保安全可控'
    },
    {
      icon: <TrendingUp className="w-6 h-6" />,
      title: '實時性能監控',
      description: '全方位監控系統指標，即時發現並解決問題'
    },
    {
      icon: <DollarSign className="w-6 h-6" />,
      title: '成本優化',
      description: '智能分析資源使用，降低運營成本'
    }
  ]

  const benefits = [
    '提升系統性能 15-30%',
    '降低運營成本 20-40%',
    '減少人工干預 60%',
    '7x24 自動化運維'
  ]

  return (
    <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center">
              <Cpu className="w-8 h-8 text-blue-600" />
              <span className="ml-2 text-xl font-bold text-gray-900">MorningAI</span>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                variant="ghost"
                onClick={() => navigate('/login')}
                className="text-gray-700 hover:text-gray-900"
              >
                登入
              </Button>
              <Button
                onClick={handleGetStarted}
                className="bg-blue-600 hover:bg-blue-700 text-white"
              >
                開始使用
                <ArrowRight className="ml-2 w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </nav>

      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            AI 驅動的智能運維平台
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-3xl mx-auto">
            讓 AI 自動優化您的系統性能、降低成本、提升效率。
            人機協作，安全可控，7x24 小時不間斷運維。
          </p>
          <div className="flex justify-center space-x-4">
            <Button
              size="lg"
              onClick={handleGetStarted}
              className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-6 text-lg"
            >
              免費試用
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              onClick={() => {
                document.getElementById('features')?.scrollIntoView({ behavior: 'smooth' })
              }}
              className="px-8 py-6 text-lg"
            >
              了解更多
            </Button>
          </div>
        </div>

        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          {benefits.map((benefit, index) => (
            <div key={index} className="flex items-center justify-center space-x-2">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-gray-700 font-medium">{benefit}</span>
            </div>
          ))}
        </div>
      </section>

      <section id="features" className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">核心功能</h2>
            <p className="text-xl text-gray-600">
              全方位的 AI 驅動自動化解決方案
            </p>
          </div>

          <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
            {features.map((feature, index) => (
              <div
                key={index}
                className="p-6 border border-gray-200 rounded-lg hover:shadow-lg transition-shadow"
              >
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center text-blue-600 mb-4">
                  {feature.icon}
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">
                  {feature.description}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="bg-blue-600 py-20">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            準備好開始了嗎？
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            立即體驗 AI 驅動的智能運維，提升系統性能，降低運營成本
          </p>
          <Button
            size="lg"
            onClick={handleGetStarted}
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-6 text-lg"
          >
            免費試用 30 天
            <ArrowRight className="ml-2 w-5 h-5" />
          </Button>
        </div>
      </section>

      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid md:grid-cols-3 gap-8">
            <div>
              <div className="flex items-center mb-4">
                <Cpu className="w-6 h-6 text-blue-500" />
                <span className="ml-2 text-lg font-bold text-white">MorningAI</span>
              </div>
              <p className="text-sm">
                AI 驅動的智能運維平台
              </p>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">產品</h4>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white">功能介紹</a></li>
                <li><button onClick={() => navigate('/checkout')} className="hover:text-white text-left">定價方案</button></li>
                <li><button onClick={() => {}} className="hover:text-white text-left">客戶案例</button></li>
              </ul>
            </div>
            <div>
              <h4 className="text-white font-semibold mb-4">支援</h4>
              <ul className="space-y-2 text-sm">
                <li><button onClick={() => {}} className="hover:text-white text-left">文檔</button></li>
                <li><button onClick={() => {}} className="hover:text-white text-left">聯絡我們</button></li>
                <li><button onClick={() => {}} className="hover:text-white text-left">隱私政策</button></li>
              </ul>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-gray-800 text-center text-sm">
            <p>&copy; 2025 MorningAI. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  )
}

export default LandingPage
