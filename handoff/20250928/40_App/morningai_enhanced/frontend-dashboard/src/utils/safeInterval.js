/**
 * Safe interval utility that prevents memory leaks and runaway intervals
 * @param {Function} fn - Function to execute on each interval
 * @param {number} ms - Interval duration in milliseconds
 * @param {number} max - Maximum number of executions (optional, default: Infinity)
 * @returns {Function} Cleanup function to stop the interval
 */
export function safeInterval(fn, ms, max = Infinity) {
  let count = 0
  let intervalId = null
  let stopped = false

  const execute = () => {
    if (stopped) return
    
    count++
    
    try {
      fn()
    } catch (error) {
      console.error('safeInterval execution error:', error)
    }
    
    if (count >= max) {
      stop()
    }
  }

  const stop = () => {
    if (intervalId !== null) {
      clearInterval(intervalId)
      intervalId = null
    }
    stopped = true
  }

  // Start the interval
  intervalId = setInterval(execute, ms)

  // Return cleanup function
  return stop
}
