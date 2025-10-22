import { useTranslation } from 'react-i18next'
import { ArrowRight, Sparkles, TrendingUp, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'

const AppleHero = ({ onGetStarted, onLearnMore }) => {
  const { t } = useTranslation()

  const features = [
    {
      icon: Sparkles,
      title: t('landing.hero.features.ai.title'),
      description: t('landing.hero.features.ai.description')
    },
    {
      icon: TrendingUp,
      title: t('landing.hero.features.analytics.title'),
      description: t('landing.hero.features.analytics.description')
    },
    {
      icon: Shield,
      title: t('landing.hero.features.security.title'),
      description: t('landing.hero.features.security.description')
    }
  ]

  return (
    <section
      className="relative min-h-screen flex items-center justify-center bg-white dark:bg-gray-900"
      aria-label={t('landing.hero.ariaLabel')}
    >
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <div className="text-center space-y-8">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm font-medium">
            <Sparkles className="w-4 h-4" />
            {t('landing.hero.badge')}
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 dark:text-white">
            {t('landing.hero.title.line1')}
            <br />
            {t('landing.hero.title.line2')}
          </h1>

          <p className="text-xl sm:text-2xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto">
            {t('landing.hero.subtitle')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Button
              size="lg"
              className="bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-gray-900 px-8 py-6 text-lg"
              onClick={onGetStarted}
            >
              {t('landing.hero.cta.primary')}
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="px-8 py-6 text-lg border-gray-300 dark:border-gray-700"
              onClick={onLearnMore}
            >
              {t('landing.hero.cta.secondary')}
            </Button>
          </div>
        </div>

        <div className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <div
                key={index}
                className="p-6 text-center"
              >
                <div className="w-12 h-12 mx-auto rounded-lg bg-gray-900 dark:bg-white flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-white dark:text-gray-900" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default AppleHero
