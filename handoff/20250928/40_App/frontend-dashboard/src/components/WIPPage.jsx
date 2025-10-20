import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, ArrowLeft, Target } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'

const WIPPage = ({ 
  title = "功能開發中", 
  description = "此功能正在積極開發中，敬請期待！",
  redirectSeconds = 3,
  milestones = []
}) => {
  const navigate = useNavigate()
  const [countdown, setCountdown] = useState(redirectSeconds)

  useEffect(() => {
    let n = 0, id
    const step = () => {
      setCountdown(prev => {
        if (prev <= 1) {
          navigate('/dashboard')
          return 0
        }
        return prev - 1
      })
      if (++n >= 120) {
        clearInterval(id)
      }
    }
    const vis = () => {
      if (document.hidden) {
        clearInterval(id)
      } else {
        id = setInterval(step, 1000)
      }
    }
    document.addEventListener("visibilitychange", vis)
    vis()

    return () => {
      clearInterval(id)
      document.removeEventListener("visibilitychange", vis)
    }
  }, [navigate])

  const defaultMilestones = [
    { name: "需求分析", completed: true, date: "已完成" },
    { name: "UI/UX 設計", completed: true, date: "已完成" },
    { name: "後端 API", completed: false, date: "開發中" },
    { name: "前端實作", completed: false, date: "規劃中" },
    { name: "測試驗證", completed: false, date: "待開始" }
  ]

  const displayMilestones = milestones.length > 0 ? milestones : defaultMilestones
  const completedCount = displayMilestones.filter(m => m.completed).length
  const progressPercentage = (completedCount / displayMilestones.length) * 100

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
      <Card className="w-full max-w-2xl">
        <CardHeader className="text-center">
          <div className="mx-auto w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <Clock className="w-8 h-8 text-blue-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-gray-900">{title}</CardTitle>
          <CardDescription className="text-lg text-gray-600 mt-2">
            {description}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="text-center">
            <div className="text-sm text-gray-500 mb-2">
              {countdown} 秒後自動返回儀表板
            </div>
            <Progress value={((redirectSeconds - countdown) / redirectSeconds) * 100} className="w-full" />
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">開發進度</h3>
            </div>
            
            <div className="space-y-3">
              {displayMilestones.map((milestone, index) => (
                <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                  <div className="flex items-center gap-3">
                    <div className={`w-3 h-3 rounded-full ${
                      milestone.completed ? 'bg-green-500' : 'bg-gray-300'
                    }`} />
                    <span className={`font-medium ${
                      milestone.completed ? 'text-gray-900' : 'text-gray-500'
                    }`}>
                      {milestone.name}
                    </span>
                  </div>
                  <span className={`text-sm ${
                    milestone.completed ? 'text-green-600' : 'text-gray-500'
                  }`}>
                    {milestone.date}
                  </span>
                </div>
              ))}
            </div>
            
            <div className="mt-4">
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>整體進度</span>
                <span>{Math.round(progressPercentage)}%</span>
              </div>
              <Progress value={progressPercentage} className="w-full" />
            </div>
          </div>

          <div className="flex justify-center pt-4">
            <Button 
              onClick={() => navigate('/dashboard')} 
              className="flex items-center gap-2"
              aria-label="立即返回儀表板"
            >
              <ArrowLeft className="w-4 h-4" />
              立即返回儀表板
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default WIPPage
