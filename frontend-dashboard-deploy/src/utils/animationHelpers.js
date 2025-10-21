import { animations, durations, easings } from './animations'

export const withDelay = (animation, delay) => ({
  ...animation,
  transition: {
    ...animation.transition,
    delay
  }
})

export const withDuration = (animation, duration) => ({
  ...animation,
  transition: {
    ...animation.transition,
    duration
  }
})

export const withEasing = (animation, easing) => ({
  ...animation,
  transition: {
    ...animation.transition,
    ease: easing
  }
})

export const combineAnimations = (...anims) => {
  return anims.reduce((acc, anim) => ({
    initial: { ...acc.initial, ...anim.initial },
    animate: { ...acc.animate, ...anim.animate },
    exit: { ...acc.exit, ...anim.exit },
    transition: { ...acc.transition, ...anim.transition }
  }), { initial: {}, animate: {}, exit: {}, transition: {} })
}

export const createSequence = (animations, baseDelay = 0, delayIncrement = 0.1) => {
  return animations.map((anim, index) => 
    withDelay(anim, baseDelay + (index * delayIncrement))
  )
}

export const useAnimationPreset = (preset) => {
  const presets = {
    card: {
      ...animations.fadeInUp,
      ...animations.cardHover
    },
    button: {
      ...animations.scaleIn,
      ...animations.buttonHover
    },
    icon: {
      ...animations.rotateIn,
      ...animations.iconHover
    },
    modal: {
      initial: { scale: 0.9, opacity: 0, y: 20 },
      animate: { scale: 1, opacity: 1, y: 0 },
      exit: { scale: 0.9, opacity: 0, y: 20 },
      transition: { type: "spring", stiffness: 300, damping: 25 }
    },
    drawer: {
      initial: { x: "100%", opacity: 0 },
      animate: { x: 0, opacity: 1 },
      exit: { x: "100%", opacity: 0 },
      transition: { type: "spring", stiffness: 300, damping: 30 }
    },
    dropdown: {
      initial: { opacity: 0, y: -10, scale: 0.95 },
      animate: { opacity: 1, y: 0, scale: 1 },
      exit: { opacity: 0, y: -10, scale: 0.95 },
      transition: { duration: durations.fast }
    },
    toast: {
      initial: { opacity: 0, y: 50, scale: 0.3 },
      animate: { opacity: 1, y: 0, scale: 1 },
      exit: { opacity: 0, scale: 0.5, transition: { duration: 0.2 } },
      transition: { type: "spring", stiffness: 500, damping: 30 }
    }
  }

  return presets[preset] || animations.fadeIn
}

export const createListAnimation = (itemCount, staggerDelay = 0.05) => {
  return {
    container: {
      animate: {
        transition: {
          staggerChildren: staggerDelay
        }
      }
    },
    item: (index) => ({
      initial: { opacity: 0, x: -20 },
      animate: { 
        opacity: 1, 
        x: 0,
        transition: {
          delay: index * staggerDelay
        }
      }
    })
  }
}

export const createGridAnimation = (columns = 3, staggerDelay = 0.03) => {
  return {
    container: {
      animate: {
        transition: {
          staggerChildren: staggerDelay
        }
      }
    },
    item: (index) => {
      const row = Math.floor(index / columns)
      const col = index % columns
      return {
        initial: { opacity: 0, scale: 0.8 },
        animate: { 
          opacity: 1, 
          scale: 1,
          transition: {
            delay: (row + col) * staggerDelay
          }
        }
      }
    }
  }
}

export const createScrollAnimation = (threshold = 0.1) => ({
  initial: { opacity: 0, y: 50 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, amount: threshold },
  transition: { duration: durations.slow }
})

export const createParallaxAnimation = (speed = 0.5) => ({
  initial: { y: 0 },
  animate: { y: -100 * speed },
  transition: { duration: 1, ease: "linear" }
})

export const createCounterAnimation = (from, to, duration = 2) => ({
  initial: { value: from },
  animate: { value: to },
  transition: { duration, ease: "easeOut" }
})

export const createTypewriterAnimation = (text, speed = 0.05) => {
  const chars = text.split('')
  return {
    container: {
      animate: {
        transition: {
          staggerChildren: speed
        }
      }
    },
    char: {
      initial: { opacity: 0 },
      animate: { opacity: 1 }
    }
  }
}

export const createShimmerAnimation = () => ({
  animate: {
    backgroundPosition: ["200% 0", "-200% 0"],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "linear"
    }
  }
})

export const createRippleAnimation = () => ({
  initial: { scale: 0, opacity: 0.5 },
  animate: { scale: 2, opacity: 0 },
  transition: { duration: 0.6, ease: "easeOut" }
})

export const createGlowAnimation = (color = "rgba(59, 130, 246, 0.5)") => ({
  animate: {
    boxShadow: [
      `0 0 20px ${color}`,
      `0 0 40px ${color}`,
      `0 0 20px ${color}`
    ],
    transition: {
      duration: 2,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
})

export const createWaveAnimation = (amplitude = 10, frequency = 2) => ({
  animate: {
    y: [0, -amplitude, 0, amplitude, 0],
    transition: {
      duration: frequency,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
})

export const createFlipAnimation = () => ({
  initial: { rotateY: 0 },
  animate: { rotateY: 180 },
  exit: { rotateY: 0 },
  transition: { duration: 0.6 }
})

export const createSlideAnimation = (direction = 'left') => {
  const directions = {
    left: { initial: { x: -100 }, animate: { x: 0 }, exit: { x: 100 } },
    right: { initial: { x: 100 }, animate: { x: 0 }, exit: { x: -100 } },
    up: { initial: { y: 100 }, animate: { y: 0 }, exit: { y: -100 } },
    down: { initial: { y: -100 }, animate: { y: 0 }, exit: { y: 100 } }
  }
  
  return {
    ...directions[direction],
    transition: { type: "spring", stiffness: 300, damping: 30 }
  }
}

export const createBounceAnimation = (height = 20) => ({
  animate: {
    y: [0, -height, 0],
    transition: {
      duration: 0.6,
      repeat: Infinity,
      ease: "easeOut"
    }
  }
})

export const createRotateAnimation = (degrees = 360, duration = 1) => ({
  animate: {
    rotate: degrees,
    transition: {
      duration,
      repeat: Infinity,
      ease: "linear"
    }
  }
})

export const createPulseAnimation = (scale = 1.05, duration = 2) => ({
  animate: {
    scale: [1, scale, 1],
    transition: {
      duration,
      repeat: Infinity,
      ease: "easeInOut"
    }
  }
})

export default {
  withDelay,
  withDuration,
  withEasing,
  combineAnimations,
  createSequence,
  useAnimationPreset,
  createListAnimation,
  createGridAnimation,
  createScrollAnimation,
  createParallaxAnimation,
  createCounterAnimation,
  createTypewriterAnimation,
  createShimmerAnimation,
  createRippleAnimation,
  createGlowAnimation,
  createWaveAnimation,
  createFlipAnimation,
  createSlideAnimation,
  createBounceAnimation,
  createRotateAnimation,
  createPulseAnimation
}
