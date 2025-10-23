import { lazy, Suspense } from 'react'
import { useTranslation } from 'react-i18next'
import { motion } from 'framer-motion'
import { Brain, Chrome, Apple as AppleIcon, Github } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { LanguageSwitcher } from './LanguageSwitcher'

const AppleHero = lazy(() => import('./AppleHero'))

const LandingPage = ({ onNavigateToLogin, onSSOLogin }) => {
  const { t } = useTranslation()

  const handleGetStarted = () => {
    const ssoSection = document.getElementById('sso-login')
    if (ssoSection) {
      ssoSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const handleLearnMore = () => {
    const featuresSection = document.getElementById('features')
    if (featuresSection) {
      featuresSection.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const handleSSOLogin = (provider) => {
    if (onSSOLogin) {
      onSSOLogin(provider)
    } else {
      console.log(`SSO Login with ${provider}`)
    }
  }

  return (
    <div className="min-h-screen bg-white dark:bg-gray-900">
      <header className="fixed top-0 left-0 right-0 z-50 bg-white/80 dark:bg-gray-900/80 backdrop-blur-md border-b border-gray-200 dark:border-gray-800">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
              <Brain className="w-5 h-5 text-white" />
            </div>
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              {t('app.name')}
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            <LanguageSwitcher variant="compact" />
            <Button
              variant="ghost"
              onClick={onNavigateToLogin}
              className="text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white"
            >
              {t('landing.nav.login')}
            </Button>
            <Button
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white"
              onClick={handleGetStarted}
            >
              {t('landing.nav.getStarted')}
            </Button>
          </div>
        </nav>
      </header>

      <main className="pt-16">
        <Suspense fallback={
          <div className="min-h-screen flex items-center justify-center">
            <div className="animate-pulse text-gray-400">Loading...</div>
          </div>
        }>
          <AppleHero
            onGetStarted={handleGetStarted}
            onLearnMore={handleLearnMore}
          />
        </Suspense>

        <section
          id="sso-login"
          className="py-20 bg-gray-50 dark:bg-gray-800/50"
        >
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-12"
            >
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                {t('landing.sso.title')}
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-300">
                {t('landing.sso.subtitle')}
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6, delay: 0.2 }}
            >
              <Card className="shadow-xl">
                <CardContent className="p-8 space-y-4">
                  <Button
                    size="lg"
                    variant="outline"
                    className="w-full justify-start gap-3 h-14 text-base hover:bg-gray-50 dark:hover:bg-gray-800"
                    onClick={() => handleSSOLogin('google')}
                  >
                    <Chrome className="w-5 h-5 text-blue-500" />
                    {t('landing.sso.google')}
                  </Button>

                  <Button
                    size="lg"
                    variant="outline"
                    className="w-full justify-start gap-3 h-14 text-base hover:bg-gray-50 dark:hover:bg-gray-800"
                    onClick={() => handleSSOLogin('apple')}
                  >
                    <AppleIcon className="w-5 h-5 text-gray-900 dark:text-white" />
                    {t('landing.sso.apple')}
                  </Button>

                  <Button
                    size="lg"
                    variant="outline"
                    className="w-full justify-start gap-3 h-14 text-base hover:bg-gray-50 dark:hover:bg-gray-800"
                    onClick={() => handleSSOLogin('github')}
                  >
                    <Github className="w-5 h-5 text-gray-900 dark:text-white" />
                    {t('landing.sso.github')}
                  </Button>

                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white dark:bg-gray-900 text-gray-500 dark:text-gray-400">
                        {t('landing.sso.or')}
                      </span>
                    </div>
                  </div>

                  <Button
                    size="lg"
                    variant="ghost"
                    className="w-full h-14 text-base text-blue-600 dark:text-blue-400 hover:text-blue-700 dark:hover:text-blue-300 hover:bg-blue-50 dark:hover:bg-blue-950/30"
                    onClick={onNavigateToLogin}
                  >
                    {t('landing.sso.emailLogin')}
                  </Button>
                </CardContent>
              </Card>
            </motion.div>

            <p className="text-center text-sm text-gray-500 dark:text-gray-400 mt-6">
              {t('landing.sso.terms')}
            </p>
          </div>
        </section>

        <section
          id="features"
          className="py-20 bg-white dark:bg-gray-900"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="text-center mb-16"
            >
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                {t('landing.features.title')}
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-300 max-w-2xl mx-auto">
                {t('landing.features.subtitle')}
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              {[
                {
                  title: t('landing.features.realtime.title'),
                  description: t('landing.features.realtime.description'),
                  gradient: 'from-blue-500 to-cyan-500'
                },
                {
                  title: t('landing.features.intelligent.title'),
                  description: t('landing.features.intelligent.description'),
                  gradient: 'from-purple-500 to-pink-500'
                },
                {
                  title: t('landing.features.secure.title'),
                  description: t('landing.features.secure.description'),
                  gradient: 'from-green-500 to-emerald-500'
                },
                {
                  title: t('landing.features.scalable.title'),
                  description: t('landing.features.scalable.description'),
                  gradient: 'from-orange-500 to-red-500'
                },
                {
                  title: t('landing.features.collaborative.title'),
                  description: t('landing.features.collaborative.description'),
                  gradient: 'from-indigo-500 to-blue-500'
                },
                {
                  title: t('landing.features.insights.title'),
                  description: t('landing.features.insights.description'),
                  gradient: 'from-pink-500 to-rose-500'
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.6, delay: index * 0.1 }}
                >
                  <Card className="h-full hover:shadow-lg transition-shadow">
                    <CardContent className="p-6">
                      <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${feature.gradient} flex items-center justify-center mb-4`}>
                        <div className="w-6 h-6 bg-white rounded-full" />
                      </div>
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-300">
                        {feature.description}
                      </p>
                    </CardContent>
                  </Card>
                </motion.div>
              ))}
            </div>
          </div>
        </section>

        <footer className="py-12 bg-gray-50 dark:bg-gray-800/50 border-t border-gray-200 dark:border-gray-700">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex flex-col md:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                  <Brain className="w-5 h-5 text-white" />
                </div>
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {t('app.name')}
                </span>
              </div>
              
              <div className="text-center md:text-right">
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {t('app.copyright')}
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                  {t('app.motto')}
                </p>
              </div>
            </div>
          </div>
        </footer>
      </main>
    </div>
  )
}

export default LandingPage
