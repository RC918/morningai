/**
 * Spring Animation System - Apple-Level UI/UX
 * Implements iOS-style spring-based animations with haptic feedback simulation
 * 
 * Based on Apple Human Interface Guidelines and iOS 26.1 design patterns
 */


/**
 * Check if user prefers reduced motion
 */
const prefersReducedMotion = () => {
  if (typeof window === 'undefined') return false;
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
};


/**
 * Apple-style spring presets matching iOS animations
 */
export const springPresets = {
  gentle: {
    type: 'spring',
    stiffness: 120,
    damping: 14,
    mass: 0.5,
    duration: 0.6
  },
  
  default: {
    type: 'spring',
    stiffness: 170,
    damping: 26,
    mass: 1,
    duration: 0.5
  },
  
  bouncy: {
    type: 'spring',
    stiffness: 260,
    damping: 20,
    mass: 0.8,
    duration: 0.7
  },
  
  snappy: {
    type: 'spring',
    stiffness: 300,
    damping: 30,
    mass: 0.6,
    duration: 0.4
  },
  
  smooth: {
    type: 'spring',
    stiffness: 100,
    damping: 20,
    mass: 1.2,
    duration: 0.8
  },
  
  wobbly: {
    type: 'spring',
    stiffness: 180,
    damping: 12,
    mass: 1,
    duration: 0.9
  }
};

/**
 * Get spring configuration based on preset name
 */
export const getSpringConfig = (preset = 'default') => {
  if (prefersReducedMotion()) {
    return { duration: 0 };
  }
  
  return springPresets[preset] || springPresets.default;
};


/**
 * Get spring-based animation variants for Framer Motion
 */
export const getSpringVariants = (type = 'fade', preset = 'default') => {
  if (prefersReducedMotion()) {
    return {
      initial: { opacity: 1 },
      animate: { opacity: 1 },
      exit: { opacity: 1 }
    };
  }
  
  const spring = getSpringConfig(preset);
  
  const variants = {
    fade: {
      initial: { opacity: 0 },
      animate: { opacity: 1, transition: spring },
      exit: { opacity: 0, transition: { ...spring, duration: spring.duration * 0.6 } }
    },
    
    scale: {
      initial: { opacity: 0, scale: 0.8 },
      animate: { 
        opacity: 1, 
        scale: 1,
        transition: spring
      },
      exit: { 
        opacity: 0, 
        scale: 0.9,
        transition: { ...spring, duration: spring.duration * 0.5 }
      }
    },
    
    pop: {
      initial: { scale: 1 },
      animate: { 
        scale: [1, 0.95, 1],
        transition: {
          ...spring,
          times: [0, 0.4, 1]
        }
      }
    },
    
    bounce: {
      initial: { scale: 1 },
      animate: { 
        scale: [1, 1.1, 0.95, 1.02, 1],
        transition: {
          ...springPresets.bouncy,
          times: [0, 0.2, 0.5, 0.8, 1]
        }
      }
    },
    
    slideUp: {
      initial: { opacity: 0, y: 100 },
      animate: { 
        opacity: 1, 
        y: 0,
        transition: spring
      },
      exit: { 
        opacity: 0, 
        y: 50,
        transition: { ...spring, duration: spring.duration * 0.6 }
      }
    },
    
    slideDown: {
      initial: { opacity: 0, y: -20, scale: 0.95 },
      animate: { 
        opacity: 1, 
        y: 0,
        scale: 1,
        transition: spring
      },
      exit: { 
        opacity: 0, 
        y: -10,
        scale: 0.98,
        transition: { ...spring, duration: spring.duration * 0.5 }
      }
    },
    
    slideLeft: {
      initial: { opacity: 0, x: 50 },
      animate: { 
        opacity: 1, 
        x: 0,
        transition: spring
      },
      exit: { 
        opacity: 0, 
        x: -50,
        transition: spring
      }
    },
    
    slideRight: {
      initial: { opacity: 0, x: -50 },
      animate: { 
        opacity: 1, 
        x: 0,
        transition: spring
      },
      exit: { 
        opacity: 0, 
        x: 50,
        transition: spring
      }
    },
    
    expand: {
      initial: { opacity: 0, height: 0, scale: 0.95 },
      animate: { 
        opacity: 1, 
        height: 'auto',
        scale: 1,
        transition: spring
      },
      exit: { 
        opacity: 0, 
        height: 0,
        scale: 0.95,
        transition: { ...spring, duration: spring.duration * 0.6 }
      }
    },
    
    rotate: {
      initial: { rotate: 0 },
      animate: { 
        rotate: 360,
        transition: {
          ...spring,
          repeat: Infinity,
          repeatType: 'loop'
        }
      }
    },
    
    shake: {
      initial: { x: 0 },
      animate: { 
        x: [0, -10, 10, -10, 10, -5, 5, 0],
        transition: {
          duration: 0.5,
          times: [0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 1]
        }
      }
    },
    
    pulse: {
      initial: { scale: 1, opacity: 1 },
      animate: { 
        scale: [1, 1.05, 1],
        opacity: [1, 0.8, 1],
        transition: {
          ...spring,
          repeat: Infinity,
          repeatDelay: 1
        }
      }
    }
  };
  
  return variants[type] || variants.fade;
};


/**
 * Haptic feedback types matching iOS patterns
 */
export const hapticTypes = {
  light: { intensity: 0.3, duration: 10 },
  medium: { intensity: 0.5, duration: 15 },
  heavy: { intensity: 0.7, duration: 20 },
  success: { intensity: 0.6, duration: 25, pattern: [10, 5, 10] },
  warning: { intensity: 0.7, duration: 30, pattern: [15, 10, 15] },
  error: { intensity: 0.8, duration: 35, pattern: [20, 10, 20, 10, 20] },
  selection: { intensity: 0.4, duration: 8 }
};

/**
 * Simulate haptic feedback with visual animation
 * Returns animation properties to apply to element
 */
export const getHapticAnimation = (type = 'light') => {
  if (prefersReducedMotion()) {
    return {};
  }
  
  const haptic = hapticTypes[type] || hapticTypes.light;
  
  const animations = {
    light: {
      scale: [1, 0.98, 1],
      transition: { duration: 0.1, times: [0, 0.5, 1] }
    },
    medium: {
      scale: [1, 0.96, 1],
      transition: { duration: 0.15, times: [0, 0.5, 1] }
    },
    heavy: {
      scale: [1, 0.94, 1.02, 1],
      transition: { duration: 0.2, times: [0, 0.4, 0.7, 1] }
    },
    success: {
      scale: [1, 0.95, 1.05, 1],
      transition: { 
        duration: 0.4,
        times: [0, 0.2, 0.6, 1],
        ease: 'easeOut'
      }
    },
    warning: {
      x: [0, -3, 3, -3, 3, 0],
      transition: { duration: 0.3, times: [0, 0.2, 0.4, 0.6, 0.8, 1] }
    },
    error: {
      x: [0, -5, 5, -5, 5, -3, 3, 0],
      transition: { duration: 0.5, times: [0, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1] }
    },
    selection: {
      scale: [1, 0.99, 1],
      transition: { duration: 0.08, times: [0, 0.5, 1] }
    }
  };
  
  return animations[type] || animations.light;
};

/**
 * Trigger haptic feedback (visual simulation)
 * Returns a promise that resolves when animation completes
 */
export const triggerHaptic = async (element, type = 'light') => {
  if (!element || prefersReducedMotion()) {
    return Promise.resolve();
  }
  
  const animation = getHapticAnimation(type);
  const haptic = hapticTypes[type] || hapticTypes.light;
  
  element.classList.add(`haptic-${type}`);
  
  return new Promise((resolve) => {
    setTimeout(() => {
      element.classList.remove(`haptic-${type}`);
      resolve();
    }, haptic.duration);
  });
};


/**
 * Get animation based on context (screen size, user preferences, etc.)
 */
export const getContextualAnimation = (baseAnimation, context = {}) => {
  if (prefersReducedMotion()) {
    return { duration: 0 };
  }
  
  const {
    isMobile = false,
    isLowPower = false,
    connectionSpeed = 'fast',
    userPreference = 'default'
  } = context;
  
  let preset = 'default';
  
  if (isLowPower || connectionSpeed === 'slow') {
    preset = 'snappy'; // Faster, less resource-intensive
  } else if (isMobile) {
    preset = 'smooth'; // Smoother for touch interactions
  } else if (userPreference === 'playful') {
    preset = 'bouncy'; // More expressive animations
  } else if (userPreference === 'minimal') {
    preset = 'gentle'; // Subtle animations
  }
  
  return getSpringVariants(baseAnimation, preset);
};

/**
 * Detect user context
 */
export const getUserContext = () => {
  const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
  const isLowPower = navigator.deviceMemory ? navigator.deviceMemory < 4 : false;
  
  let connectionSpeed = 'fast';
  if (navigator.connection) {
    const effectiveType = navigator.connection.effectiveType;
    if (effectiveType === 'slow-2g' || effectiveType === '2g') {
      connectionSpeed = 'slow';
    } else if (effectiveType === '3g') {
      connectionSpeed = 'medium';
    }
  }
  
  return {
    isMobile,
    isLowPower,
    connectionSpeed,
    userPreference: localStorage.getItem('animationPreference') || 'default'
  };
};


/**
 * Create a sequence of spring animations
 */
export const createAnimationSequence = (steps, preset = 'default') => {
  if (prefersReducedMotion()) {
    return { duration: 0 };
  }
  
  const spring = getSpringConfig(preset);
  const totalDuration = steps.reduce((sum, step) => sum + (step.duration || spring.duration), 0);
  
  return {
    ...spring,
    duration: totalDuration,
    times: steps.map((step, i) => {
      const prevDuration = steps.slice(0, i).reduce((sum, s) => sum + (s.duration || spring.duration), 0);
      return prevDuration / totalDuration;
    })
  };
};

/**
 * Stagger children animations
 */
export const getStaggerConfig = (preset = 'default', staggerDelay = 0.05) => {
  if (prefersReducedMotion()) {
    return { staggerChildren: 0 };
  }
  
  const spring = getSpringConfig(preset);
  
  return {
    staggerChildren: staggerDelay,
    delayChildren: 0.1,
    transition: spring
  };
};


let animationMetrics = {
  totalAnimations: 0,
  activeAnimations: 0,
  droppedFrames: 0,
  averageFPS: 60
};

/**
 * Track animation performance
 * Returns a cleanup function to prevent memory leaks
 */
export const trackAnimation = (animationId) => {
  animationMetrics.totalAnimations++;
  animationMetrics.activeAnimations++;
  
  let lastTime = performance.now();
  let frameCount = 0;
  let fps = [];
  let rafId = null;
  let isActive = true;
  
  const measureFrame = () => {
    if (!isActive) return;
    
    const currentTime = performance.now();
    const delta = currentTime - lastTime;
    
    if (delta > 0) {
      const currentFPS = 1000 / delta;
      fps.push(currentFPS);
      
      if (currentFPS < 55) {
        animationMetrics.droppedFrames++;
      }
    }
    
    lastTime = currentTime;
    frameCount++;
    
    if (frameCount < 60 && isActive) {
      rafId = requestAnimationFrame(measureFrame);
    } else {
      const avgFPS = fps.reduce((sum, f) => sum + f, 0) / fps.length;
      animationMetrics.averageFPS = (animationMetrics.averageFPS + avgFPS) / 2;
      animationMetrics.activeAnimations--;
      rafId = null;
    }
  };
  
  rafId = requestAnimationFrame(measureFrame);
  
  return () => {
    isActive = false;
    if (rafId !== null) {
      cancelAnimationFrame(rafId);
      animationMetrics.activeAnimations--;
    }
  };
};

/**
 * Get animation performance metrics
 */
export const getAnimationMetrics = () => {
  return { ...animationMetrics };
};

/**
 * Reset animation metrics
 */
export const resetAnimationMetrics = () => {
  animationMetrics = {
    totalAnimations: 0,
    activeAnimations: 0,
    droppedFrames: 0,
    averageFPS: 60
  };
};


export default {
  springPresets,
  getSpringConfig,
  getSpringVariants,
  hapticTypes,
  getHapticAnimation,
  triggerHaptic,
  getContextualAnimation,
  getUserContext,
  createAnimationSequence,
  getStaggerConfig,
  trackAnimation,
  getAnimationMetrics,
  resetAnimationMetrics
};
