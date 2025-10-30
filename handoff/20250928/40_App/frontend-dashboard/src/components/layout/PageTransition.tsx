import { motion } from 'framer-motion'
import { pageVariants, pageTransition } from '@/lib/animations'

export const PageTransition = ({ children }) => {
  return (
    <motion.div
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      transition={pageTransition}
    >
      {children}
    </motion.div>
  )
}

export default PageTransition
