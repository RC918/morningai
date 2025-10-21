import { motion } from 'framer-motion'
import { Sparkles } from 'lucide-react'

export const BrandLoader = ({ 
  message = '載入中...', 
  size = 'default',
  variant = 'full'
}) => {
  const sizes = {
    small: { container: 'w-12 h-12', icon: 'w-6 h-6', text: 'text-sm' },
    default: { container: 'w-20 h-20', icon: 'w-10 h-10', text: 'text-xl' },
    large: { container: 'w-32 h-32', icon: 'w-16 h-16', text: 'text-2xl' }
  }

  const currentSize = sizes[size]

  const logoVariants = {
    initial: { scale: 0.8, opacity: 0 },
    animate: {
      scale: [0.8, 1.1, 1],
      opacity: 1,
      rotate: [0, 360],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  }

  const sparkleVariants = {
    animate: (i) => ({
      scale: [0, 1, 0],
      opacity: [0, 1, 0],
      x: [0, Math.cos(i * 60 * Math.PI / 180) * 40, 0],
      y: [0, Math.sin(i * 60 * Math.PI / 180) * 40, 0],
      transition: {
        duration: 2,
        repeat: Infinity,
        delay: i * 0.3,
        ease: "easeOut"
      }
    })
  }

  const pulseVariants = {
    animate: {
      scale: [1, 1.5, 1],
      opacity: [0.5, 0, 0.5],
      transition: {
        duration: 2,
        repeat: Infinity,
        ease: "easeInOut"
      }
    }
  }

  if (variant === 'inline') {
    return (
      <div className="flex items-center space-x-3">
        <motion.div
          variants={logoVariants}
          initial="initial"
          animate="animate"
          className={`${currentSize.container} rounded-xl flex items-center justify-center shadow-lg`}
        >
          <img 
            src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
            alt="Morning AI" 
            className="w-full h-full rounded-xl"
          />
        </motion.div>
        <span className={`${currentSize.text} font-medium text-gray-700`}>
          {message}
        </span>
      </div>
    )
  }

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-br from-blue-50 via-purple-50 to-pink-50">
      <div className="relative">
        <motion.div
          variants={pulseVariants}
          animate="animate"
          className={`absolute inset-0 ${currentSize.container} bg-gradient-to-br from-blue-400 to-purple-600 rounded-2xl blur-xl`}
        />

        {[0, 1, 2, 3, 4, 5].map((i) => (
          <motion.div
            key={i}
            custom={i}
            variants={sparkleVariants}
            animate="animate"
            className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2"
          >
            <Sparkles className="w-4 h-4 text-yellow-400" />
          </motion.div>
        ))}

        <motion.div
          variants={logoVariants}
          initial="initial"
          animate="animate"
          className={`relative ${currentSize.container} rounded-2xl flex items-center justify-center shadow-2xl`}
        >
          <img 
            src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
            alt="Morning AI" 
            className="w-full h-full rounded-2xl"
          />
        </motion.div>
      </div>
      
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}
        className="text-center mt-8"
      >
        <h2 className={`${currentSize.text} font-semibold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent mb-3`}>
          {message}
        </h2>
        <div className="flex space-x-2 justify-center">
          {[0, 1, 2].map((i) => (
            <motion.div
              key={i}
              className="w-2 h-2 rounded-full bg-gradient-to-r from-blue-500 to-purple-500"
              animate={{
                y: [0, -12, 0],
                opacity: [1, 0.5, 1],
                scale: [1, 1.2, 1]
              }}
              transition={{
                duration: 0.8,
                repeat: Infinity,
                delay: i * 0.15,
                ease: "easeInOut"
              }}
            />
          ))}
        </div>
      </motion.div>
    </div>
  )
}

export default BrandLoader
