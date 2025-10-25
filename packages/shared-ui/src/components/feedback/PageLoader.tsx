import { motion } from 'framer-motion'
import { useTranslation } from 'react-i18next'

export const PageLoader = ({ message }) => {
  const { t } = useTranslation()
  const displayMessage = message || t('feedback.loading')
  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <motion.div
        animate={{
          scale: [1, 1.2, 1],
          rotate: [0, 360]
        }}
        transition={{
          duration: 2,
          repeat: Infinity,
          ease: "easeInOut"
        }}
        className="w-20 h-20 rounded-2xl flex items-center justify-center mb-6"
      >
        <img 
          src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
          alt="Morning AI" 
          className="w-full h-full rounded-2xl"
        />
      </motion.div>
      
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.2 }}
        className="text-center"
      >
        <h2 className="text-xl font-semibold text-gray-900 mb-2">
          {displayMessage}
        </h2>
        <div className="flex space-x-1 justify-center">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 bg-blue-600 rounded-full"
              animate={{
                y: [0, -10, 0],
                opacity: [1, 0.5, 1]
              }}
              transition={{
                duration: 0.6,
                repeat: Infinity,
                delay: i * 0.2
              }}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default PageLoader
