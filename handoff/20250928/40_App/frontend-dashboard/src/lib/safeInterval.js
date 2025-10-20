/**
 * Safe interval utility with visibility pause and max iterations
 * @param {Function} tick - Function to call on each interval
 * @param {number} ms - Interval duration in milliseconds
 * @param {number} maxIterations - Maximum number of iterations (default: 120)
 * @returns {Function} Cleanup function to stop the interval
 */
export function safeInterval(tick, ms, maxIterations = 120) {
  let n = 0
  let id

  const step = () => {
    tick()
    if (++n >= maxIterations) {
      clearInterval(id)
    }
  }

  const vis = () => {
    if (document.hidden) {
      clearInterval(id)
    } else {
      clearInterval(id)
      id = setInterval(step, ms)
    }
  }

  document.addEventListener('visibilitychange', vis)
  vis()

  return () => {
    clearInterval(id)
    document.removeEventListener('visibilitychange', vis)
  }
}
