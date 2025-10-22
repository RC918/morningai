import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { motion, useScroll, useTransform, useInView } from 'framer-motion'
import { ArrowRight, Sparkles, TrendingUp, Shield } from 'lucide-react'
import { Button } from '@/components/ui/button'

const AppleHero = ({ onGetStarted, onLearnMore }) => {
  const { t } = useTranslation()
  const containerRef = useRef(null)
  const featuresRef = useRef(null)
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false)
  
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start start", "end start"]
  })
  
  const y = useTransform(scrollYProgress, [0, 1], ['0%', '30%'])
  const opacity = useTransform(scrollYProgress, [0, 0.5], [1, 0.3])
  
  const featuresInView = useInView(featuresRef, { once: true, margin: "-100px" })

  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    setPrefersReducedMotion(mediaQuery.matches)
    
    const handleChange = (e) => setPrefersReducedMotion(e.matches)
    mediaQuery.addEventListener('change', handleChange)
    
    return () => mediaQuery.removeEventListener('change', handleChange)
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
    }
  ]

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.15,
        delayChildren: 0.2
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: [0.22, 1, 0.36, 1]
      }
    }
  }

  const featureVariants = {
    hidden: { opacity: 0, y: 30, scale: 0.95 },
    visible: (i) => ({
      opacity: 1,
      y: 0,
      scale: 1,
      transition: {
        delay: i * 0.1,
        duration: 0.5,
        ease: [0.22, 1, 0.36, 1]
      }
    })
  }

  return (
    <section
      ref={containerRef}
      className="relative min-h-screen flex items-center justify-center bg-white dark:bg-gray-900 overflow-hidden"
      aria-label={t('landing.hero.ariaLabel')}
    >
      {!prefersReducedMotion && (
        <motion.div
          className="absolute inset-0 pointer-events-none"
          style={{ y, opacity }}
        >
          <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-500/5 dark:bg-blue-500/10 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-purple-500/5 dark:bg-purple-500/10 rounded-full blur-3xl" />
        </motion.div>
      )}

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
        <motion.div
          className="text-center space-y-8"
          variants={prefersReducedMotion ? {} : containerVariants}
          initial="hidden"
          animate="visible"
        >
          <motion.div
            className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm font-medium"
            variants={prefersReducedMotion ? {} : itemVariants}
          >
            <Sparkles className="w-4 h-4" />
            {t('landing.hero.badge')}
          </motion.div>

          <motion.h1
            className="text-5xl sm:text-6xl lg:text-7xl font-bold tracking-tight text-gray-900 dark:text-white"
            variants={prefersReducedMotion ? {} : itemVariants}
          >
            {t('landing.hero.title.line1')}
            <br />
            {t('landing.hero.title.line2')}
          </motion.h1>

          <motion.p
            className="text-xl sm:text-2xl text-gray-600 dark:text-gray-400 max-w-3xl mx-auto"
            variants={prefersReducedMotion ? {} : itemVariants}
          >
            {t('landing.hero.subtitle')}
          </motion.p>

          <motion.div
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
            variants={prefersReducedMotion ? {} : itemVariants}
          >
            <motion.div
              whileHover={prefersReducedMotion ? {} : { scale: 1.05 }}
              whileTap={prefersReducedMotion ? {} : { scale: 0.95 }}
            >
              <Button
                size="lg"
                className="bg-gray-900 hover:bg-gray-800 dark:bg-white dark:hover:bg-gray-100 text-white dark:text-gray-900 px-8 py-6 text-lg"
                onClick={onGetStarted}
              >
                {t('landing.hero.cta.primary')}
                <ArrowRight className="ml-2 w-5 h-5" />
              </Button>
            </motion.div>
            <motion.div
              whileHover={prefersReducedMotion ? {} : { scale: 1.05 }}
              whileTap={prefersReducedMotion ? {} : { scale: 0.95 }}
            >
              <Button
                size="lg"
                variant="outline"
                className="px-8 py-6 text-lg border-gray-300 dark:border-gray-700"
                onClick={onLearnMore}
              >
                {t('landing.hero.cta.secondary')}
              </Button>
            </motion.div>
          </motion.div>
        </motion.div>

        <div ref={featuresRef} className="mt-20 grid grid-cols-1 sm:grid-cols-3 gap-8">
          {features.map((feature, index) => {
            const Icon = feature.icon
            return (
              <motion.div
                key={index}
                className="p-6 text-center group"
                custom={index}
                variants={prefersReducedMotion ? {} : featureVariants}
                initial="hidden"
                animate={featuresInView ? "visible" : "hidden"}
                whileHover={prefersReducedMotion ? {} : { y: -8 }}
              >
                <motion.div
                  className="w-12 h-12 mx-auto rounded-lg bg-gray-900 dark:bg-white flex items-center justify-center mb-4 transition-colors group-hover:bg-gray-800 dark:group-hover:bg-gray-100"
                  whileHover={prefersReducedMotion ? {} : { rotate: [0, -10, 10, -10, 0] }}
                  transition={{ duration: 0.5 }}
                >
                  <Icon className="w-6 h-6 text-white dark:text-gray-900" />
                </motion.div>
                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600 dark:text-gray-400 text-sm">
                  {feature.description}
                </p>
              </motion.div>
            )
          })}
        </div>
      </div>
    </section>
  )
}

export default AppleHero
