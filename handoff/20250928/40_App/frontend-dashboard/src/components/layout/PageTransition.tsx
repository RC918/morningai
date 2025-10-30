import { motion } from 'framer-motion'
import { pageVariants, pageTransition } from '@/lib/animations'

export const PageTransition = ({ children }) => {
  return (
    <motion.div
      initial="initial"
      animate="in"
      exit="out"
      variants={pageVariants}
      // @ts-expect-error TODO(#935): Fix Framer Motion Transition type compatibility
      transition={pageTransition}
    >
      {children}
    </motion.div>
  )
}

export default PageTransition
