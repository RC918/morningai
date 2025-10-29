import { useEffect, useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { WifiOff, Wifi } from 'lucide-react'

export const OfflineIndicator = () => {
  const [isOnline, setIsOnline] = useState(navigator.onLine)
  const [showReconnected, setShowReconnected] = useState(false)
  
  useEffect(() => {
    const handleOnline = () => {
      setIsOnline(true)
      setShowReconnected(true)
      setTimeout(() => setShowReconnected(false), 3000)
    }
    
    const handleOffline = () => {
      setIsOnline(false)
      setShowReconnected(false)
    }
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])
  
  return (
    <AnimatePresence>
      {!isOnline && (
        <motion.div
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          exit={{ y: -100 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed top-0 left-0 right-0 bg-red-500 text-white py-2 px-4 text-center z-50 shadow-lg"
          role="alert"
          aria-live="assertive"
        >
          <WifiOff className="inline w-4 h-4 mr-2" aria-hidden="true" />
          您目前處於離線狀態，部分功能可能無法使用
        </motion.div>
      )}
      
      {showReconnected && (
        <motion.div
          initial={{ y: -100 }}
          animate={{ y: 0 }}
          exit={{ y: -100 }}
          transition={{ type: 'spring', stiffness: 300, damping: 30 }}
          className="fixed top-0 left-0 right-0 bg-green-500 text-white py-2 px-4 text-center z-50 shadow-lg"
          role="alert"
          aria-live="polite"
        >
          <Wifi className="inline w-4 h-4 mr-2" aria-hidden="true" />
          網路連線已恢復
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default OfflineIndicator
