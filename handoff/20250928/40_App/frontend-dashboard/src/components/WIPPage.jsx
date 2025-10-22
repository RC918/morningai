import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Clock, ArrowLeft, Target } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { safeInterval } from '@/lib/safeInterval'
import { useTranslation } from 'react-i18next'

const WIPPage = ({ 
  title, 
  description,
  redirectSeconds = 3,
  milestones = []
}) => {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [countdown, setCountdown] = useState(redirectSeconds)

  useEffect(() => {
    const cleanup = safeInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          navigate('/dashboard')
          return 0
        }
        return prev - 1
      })
    }, 1000, 120)

    return cleanup
  }, [navigate])

  const defaultMilestones = [
    { name: t('wip.milestones.requirementAnalysis'), completed: true, date: t('wip.milestones.completed') },
    { name: t('wip.milestones.uiuxDesign'), completed: true, date: t('wip.milestones.completed') },
    { name: t('wip.milestones.backendApi'), completed: false, date: t('wip.milestones.inProgress') },
    { name: t('wip.milestones.frontendImplementation'), completed: false, date: t('wip.milestones.planned') },
    { name: t('wip.milestones.testing'), completed: false, date: t('wip.milestones.pending') }
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
          <CardTitle className="text-2xl font-bold text-gray-900">{title || t('wip.title')}</CardTitle>
          <CardDescription className="text-lg text-gray-600 mt-2">
            {description || t('wip.description')}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="text-center">
            <div className="text-sm text-gray-500 mb-2">
              {t('wip.autoRedirect', { countdown })}
            </div>
            <Progress value={((redirectSeconds - countdown) / redirectSeconds) * 100} className="w-full" />
          </div>

          <div className="space-y-4">
            <div className="flex items-center gap-2 mb-3">
              <Target className="w-5 h-5 text-blue-600" />
              <h3 className="font-semibold text-gray-900">{t('wip.developmentProgress')}</h3>
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
                <span>{t('wip.overallProgress')}</span>
                <span>{Math.round(progressPercentage)}%</span>
              </div>
              <Progress value={progressPercentage} className="w-full" />
            </div>
          </div>

          <div className="flex justify-center pt-4">
            <Button 
              onClick={() => navigate('/dashboard')} 
              className="flex items-center gap-2"
              aria-label={t('wip.returnAriaLabel')}
            >
              <ArrowLeft className="w-4 h-4" />
              {t('wip.returnButton')}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

export default WIPPage
