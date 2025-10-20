import { useState, useEffect } from 'react'
import { Progress } from '@/components/ui/progress'
import { motion } from 'framer-motion'

export const ProgressLoader = ({ 
  steps = [],
  currentStep = 0,
  estimatedTime = 5000 
}) => {
  const [progress, setProgress] = useState(0)
  
  useEffect(() => {
    let raf, mounted = true
    const tick = () => {
      if (!mounted) return
      setProgress(prev => {
        const target = ((currentStep + 1) / steps.length) * 100
        return Math.min(prev + 1, target)
      })
      if (mounted && progress < 100) {
        raf = requestAnimationFrame(tick)
      }
    }
    raf = requestAnimationFrame(tick)
    
    return () => {
      mounted = false
      cancelAnimationFrame(raf)
    }
  }, [currentStep, steps.length, progress])
  
  return (
    <div className="max-w-md mx-auto p-6">
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
      >
        <h3 className="text-lg font-semibold mb-4">
          {steps[currentStep]?.title || '處理中...'}
        </h3>
        <Progress value={progress} className="mb-2" />
        <p className="text-sm text-gray-600">
          {steps[currentStep]?.description}
        </p>
        <div className="mt-4 text-xs text-gray-500">
          步驟 {currentStep + 1} / {steps.length}
        </div>
      </motion.div>
    </div>
  )
}

export default ProgressLoader
