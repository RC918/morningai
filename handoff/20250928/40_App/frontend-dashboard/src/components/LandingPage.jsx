import { useRef, useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, useInView } from 'framer-motion'
import { Chrome, Apple as AppleIcon, Github } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import AppleHero from './AppleHero'
import { LanguageSwitcher } from './LanguageSwitcher'
import { DarkModeToggle } from './DarkModeToggle'

const LandingPage = ({ onNavigateToLogin, onSSOLogin }) => {
  const { t } = useTranslation()
  const ssoRef = useRef(null)
  const featuresRef = useRef(null)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)
  
  const ssoInView = useInView(ssoRef, { once: true, margin: "-100px" })
  const featuresInView = useInView(featuresRef, { once: true, margin: "-100px" })

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)
    
    const handleChange = (e) => setPrefersReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handleChange)
    
    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

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
      <header className="fixed top-0 left-0 right-0 z-40 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800">
        <nav className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <img 
              src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
              alt="Morning AI" 
              className="w-10 h-10 rounded-lg"
              style={{ width: '40px', height: '40px', maxWidth: '40px', maxHeight: '40px' }}
            />
            <span className="text-xl font-bold text-gray-900 dark:text-white">
              {t('app.name')}
            </span>
          </div>
          
          <div className="flex items-center gap-4">
            <DarkModeToggle variant="compact" />
            <LanguageSwitcher variant="compact" />
            <Button
              variant="ghost"
              onClick={onNavigateToLogin}
              className="text-gray-600 dark:text-gray-600"
            >
              {t('landing.nav.login')}
            </Button>
            <Button
              className="bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-gray-900"
              onClick={handleGetStarted}
            >
              {t('landing.nav.getStarted')}
            </Button>
          </div>
        </nav>
      </header>

      <main className="pt-16">
        <AppleHero
          onGetStarted={handleGetStarted}
          onLearnMore={handleLearnMore}
        />

        <section
          id="sso-login"
          ref={ssoRef}
          className="py-20 bg-white dark:bg-gray-900"
        >
          <div className="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              className="text-center mb-12"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
              animate={ssoInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                {t('landing.sso.title')}
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-600">
                {t('landing.sso.subtitle')}
              </p>
            </motion.div>

            <motion.div
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 30 }}
              animate={ssoInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 30 }}
              transition={{ duration: 0.6, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
            >
              <Card className="border-gray-200 dark:border-gray-700">
                <CardContent className="p-8 space-y-4">
                  <motion.div
                    whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
                    whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
                  >
                    <Button
                      size="lg"
                      variant="outline"
                      className="w-full justify-start gap-3 h-14 text-base"
                      onClick={() => handleSSOLogin('google')}
                    >
                      <Chrome className="w-5 h-5" />
                      {t('landing.sso.google')}
                    </Button>
                  </motion.div>

                  <motion.div
                    whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
                    whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
                  >
                    <Button
                      size="lg"
                      variant="outline"
                      className="w-full justify-start gap-3 h-14 text-base"
                      onClick={() => handleSSOLogin('apple')}
                    >
                      <AppleIcon className="w-5 h-5" />
                      {t('landing.sso.apple')}
                    </Button>
                  </motion.div>

                  <motion.div
                    whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
                    whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
                  >
                    <Button
                      size="lg"
                      variant="outline"
                      className="w-full justify-start gap-3 h-14 text-base"
                      onClick={() => handleSSOLogin('github')}
                    >
                      <Github className="w-5 h-5" />
                      {t('landing.sso.github')}
                    </Button>
                  </motion.div>

                  <div className="relative my-6">
                    <div className="absolute inset-0 flex items-center">
                      <div className="w-full border-t border-gray-300 dark:border-gray-600" />
                    </div>
                    <div className="relative flex justify-center text-sm">
                      <span className="px-4 bg-white dark:bg-gray-900 text-gray-600 dark:text-gray-600">
                        {t('landing.sso.or')}
                      </span>
                    </div>
                  </div>

                  <motion.div
                    whileHover={prefersReducedMotion ? {} : { scale: 1.02 }}
                    whileTap={prefersReducedMotion ? {} : { scale: 0.98 }}
                  >
                    <Button
                      size="lg"
                      variant="ghost"
                      className="w-full h-14 text-base"
                      onClick={onNavigateToLogin}
                    >
                      {t('landing.sso.emailLogin')}
                    </Button>
                  </motion.div>
                </CardContent>
              </Card>

              <p className="text-center text-sm text-gray-600 dark:text-gray-600 mt-6">
                {t('landing.sso.terms')}
              </p>
            </motion.div>
          </div>
        </section>

        <section
          id="features"
          ref={featuresRef}
          className="py-20 bg-gray-50 dark:bg-gray-800/50"
        >
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <motion.div
              className="text-center mb-16"
              initial={prefersReducedMotion ? {} : { opacity: 0, y: 20 }}
              animate={featuresInView ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 }}
              transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
            >
              <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 dark:text-white mb-4">
                {t('landing.features.title')}
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-600 max-w-2xl mx-auto">
                {t('landing.features.subtitle')}
              </p>
            </motion.div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {[
                {
                  title: t('landing.features.realtime.title'),
                  description: t('landing.features.realtime.description')
                },
                {
                  title: t('landing.features.intelligent.title'),
                  description: t('landing.features.intelligent.description')
                },
                {
                  title: t('landing.features.secure.title'),
                  description: t('landing.features.secure.description')
                }
              ].map((feature, index) => (
                <motion.div
                  key={index}
                  className="text-center"
                  initial={prefersReducedMotion ? {} : { opacity: 0, y: 30, scale: 0.95 }}
                  animate={featuresInView ? { opacity: 1, y: 0, scale: 1 } : { opacity: 0, y: 30, scale: 0.95 }}
                  transition={{
                    duration: 0.5,
                    delay: index * 0.1,
                    ease: [0.22, 1, 0.36, 1]
                  }}
                  whileHover={prefersReducedMotion ? {} : { y: -8 }}
                >
                  <Card className="h-full border-gray-200 dark:border-gray-700">
                    <CardContent className="p-8">
                      <motion.div
                        className="w-12 h-12 mx-auto rounded-lg bg-gray-900 dark:bg-white flex items-center justify-center mb-4"
                        whileHover={prefersReducedMotion ? {} : { rotate: 360 }}
                        transition={{ duration: 0.6 }}
                      >
                        <div className="w-6 h-6 bg-white dark:bg-gray-900 rounded-full" />
                      </motion.div>
                      <h3 className="text-xl font-semibold text-gray-900 dark:text-white mb-2">
                        {feature.title}
                      </h3>
                      <p className="text-gray-600 dark:text-gray-600">
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
              <div className="flex items-center gap-3">
                <img 
                  src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                  alt="Morning AI" 
                  className="w-10 h-10 rounded-lg shadow-sm"
                  style={{ width: '40px', height: '40px', maxWidth: '40px', maxHeight: '40px' }}
                />
                <span className="text-lg font-bold text-gray-900 dark:text-white">
                  {t('app.name')}
                </span>
              </div>
              
              <div className="text-center md:text-right">
                <p className="text-sm text-gray-600 dark:text-gray-600">
                  {t('app.copyright')}
                </p>
                <p className="text-sm text-gray-600 dark:text-gray-600 mt-1">
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
