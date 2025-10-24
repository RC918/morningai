import { useState, useCallback } from 'react'

/**
 * useUndoRedo Hook
 * 
 * Provides undo/redo functionality for state management with history tracking.
 * Supports up to 50 history steps to prevent memory issues.
 * 
 * @param {*} initialState - The initial state value
 * @param {Object} options - Configuration options
 * @param {number} options.maxHistory - Maximum number of history steps (default: 50)
 * @returns {Object} State management object with undo/redo capabilities
 * 
 * @example
 * const {
 *   state,
 *   setState,
 *   undo,
 *   redo,
 *   canUndo,
 *   canRedo,
 *   reset,
 *   clearHistory
 * } = useUndoRedo(initialWidgets)
 */
export const useUndoRedo = (initialState, options = {}) => {
  const { maxHistory = 50 } = options
  
  const [history, setHistory] = useState([initialState])
  const [currentIndex, setCurrentIndex] = useState(0)
  
  const currentState = history[currentIndex]
  
  const canUndo = currentIndex > 0
  const canRedo = currentIndex < history.length - 1
  
  /**
   * Set a new state and add it to history
   * Clears any redo history after current index
   */
  const setState = useCallback((newState) => {
    setHistory(prev => {
      const newHistory = prev.slice(0, currentIndex + 1)
      
      newHistory.push(newState)
      
      if (newHistory.length > maxHistory) {
        newHistory.shift()
        setCurrentIndex(maxHistory - 1)
      } else {
        setCurrentIndex(newHistory.length - 1)
      }
      
      return newHistory
    })
  }, [currentIndex, maxHistory])
  
  /**
   * Undo to previous state
   */
  const undo = useCallback(() => {
    if (canUndo) {
      setCurrentIndex(prev => prev - 1)
    }
  }, [canUndo])
  
  /**
   * Redo to next state
   */
  const redo = useCallback(() => {
    if (canRedo) {
      setCurrentIndex(prev => prev + 1)
    }
  }, [canRedo])
  
  /**
   * Reset to initial state and clear history
   */
  const reset = useCallback(() => {
    setHistory([initialState])
    setCurrentIndex(0)
  }, [initialState])
  
  /**
   * Clear all history but keep current state
   */
  const clearHistory = useCallback(() => {
    setHistory([currentState])
    setCurrentIndex(0)
  }, [currentState])
  
  return {
    state: currentState,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
    reset,
    clearHistory,
    historyLength: history.length,
    currentIndex
  }
}

export default useUndoRedo
