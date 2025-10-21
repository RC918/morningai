import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, useScroll, useTransform } from 'framer-motion'
import { ArrowRight, Sparkles, TrendingUp, Shield, Zap } from 'lucide-react'
import { Button } from '@/components/ui/button'

const AppleHero = ({ onGetStarted, onLearnMore }) => {
  const { t } = useTranslation()
  const containerRef = useRef(null)
  const [isVisible, setIsVisible] = useState(false)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)

  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  })

  const y = useTransform(scrollYProgress, [0, 1], ['0%', '50%'])
  const opacity = useTransform(scrollYProgress, [0, 0.5, 1], [1, 0.5, 0])

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)

    const handleChange = (e) => setPrefersReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handleChange)

    return () => mediaQuery.removeEventListener('change', handleChange)
  }, [])

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        setIsVisible(entry.isIntersecting)
      },
      { threshold: 0.1 }
    )

    const currentRef = containerRef.current
    if (currentRef) {
      observer.observe(currentRef)
    }

    return () => {
      if (currentRef) {
        observer.unobserve(currentRef)
      }
    }
  }, [])

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
    },
    {
      icon: Zap,
      title: t('landing.hero.features.performance.title'),
      description: t('landing.hero.features.performance.description')
    }
  ]

  const animationProps = prefersReducedMotion
    ? {}
    : {
        initial: { opacity: 0, y: 20 },
        animate: isVisible ? { opacity: 1, y: 0 } : { opacity: 0, y: 20 },
        transition: { duration: 0.6, ease: [0.22, 1, 0.36, 1] }
      }

  const staggerChildren = prefersReducedMotion
    ? {}
    : {
        animate: isVisible ? "visible" : "hidden",
        variants: {
          visible: {
            transition: {
              staggerChildren: 0.1
            }
          }
        }
      }

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-b from-white via-blue-50/30 to-white dark:from-gray-900 dark:via-blue-950/20 dark:to-gray-900 isolate"
      aria-label={t('landing.hero.ariaLabel')}
    >
      {!prefersReducedMotion && isVisible && (
        <motion.div
          className="absolute inset-0 pointer-events-none overflow-hidden"
          style={{ y, opacity }}
        >
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl -z-10" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl -z-10" />
        </motion.div>
      )}

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          className="text-center space-y-8"
          {...animationProps}
        >
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 text-sm font-medium"
            {...animationProps}
          >
            <Sparkles className="w-4 h-4" />
            {t('landing.hero.badge')}
          </motion.div>

          <motion.h1
            className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight"
            {...animationProps}
          >
            <span className="block text-gray-900 dark:text-white">
              {t('landing.hero.title.line1')}
            </span>
            <span className="block bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              {t('landing.hero.title.line2')}
            </span>
          </motion.h1>

          <motion.p
            className="text-xl sm:text-2xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto"
            {...animationProps}
          >
            {t('landing.hero.subtitle')}
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            {...animationProps}
          >
            <Button
              size="lg"
              className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white px-8 py-6 text-lg rounded-xl shadow-lg hover:shadow-xl transition-all"
              onClick={onGetStarted}
            >
              {t('landing.hero.cta.primary')}
              <ArrowRight className="ml-2 w-5 h-5" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className="px-8 py-6 text-lg rounded-xl border-2"
              onClick={onLearnMore}
            >
              {t('landing.hero.cta.secondary')}
            </Button>
          </motion.div>
        </motion.div>

        <motion.div
          className="mt-20 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6"
          {...staggerChildren}
        >
          {features.map((feature, index) => {
            const Icon = feature.icon
            const cardAnimationProps = prefersReducedMotion
              ? {}
              : {
                  variants: {
                    hidden: { opacity: 0, y: 20 },
                    visible: { opacity: 1, y: 0 }
                  },
                  transition: { duration: 0.5, ease: [0.22, 1, 0.36, 1] }
                }

            return (
              <motion.div
                key={index}
                className="p-6 rounded-2xl bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm border border-gray-200 dark:border-gray-700 hover:border-blue-500 dark:hover:border-blue-400 transition-colors"
                {...cardAnimationProps}
              >
                <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center mb-4">
                  <Icon className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-300 text-sm">
                  {feature.description}
                </p>
              </motion.div>
            )
          })}
        </motion.div>
      </div>
    </section>
  )
}

export default AppleHero
