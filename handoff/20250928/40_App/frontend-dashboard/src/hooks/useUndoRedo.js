import { useReducer, useCallback, useMemo } from 'react'

const ACTIONS = {
  SET_STATE: 'SET_STATE',
  UNDO: 'UNDO',
  REDO: 'REDO',
  RESET: 'RESET',
  CLEAR_HISTORY: 'CLEAR_HISTORY'
}

const undoRedoReducer = (state, action) => {
  switch (action.type) {
    case ACTIONS.SET_STATE: {
      const { newState, maxHistory } = action.payload
      const newHistory = state.history.slice(0, state.currentIndex + 1)
      newHistory.push(newState)
      
      if (newHistory.length > maxHistory) {
        newHistory.shift()
        return {
          ...state,
          history: newHistory,
          currentIndex: maxHistory - 1
        }
      }
      
      return {
        ...state,
        history: newHistory,
        currentIndex: newHistory.length - 1
      }
    }
    
    case ACTIONS.UNDO: {
      if (state.currentIndex > 0) {
        return {
          ...state,
          currentIndex: state.currentIndex - 1
        }
      }
      return state
    }
    
    case ACTIONS.REDO: {
      if (state.currentIndex < state.history.length - 1) {
        return {
          ...state,
          currentIndex: state.currentIndex + 1
        }
      }
      return state
    }
    
    case ACTIONS.RESET: {
      return {
        history: [action.payload.initialState],
        currentIndex: 0
      }
    }
    
    case ACTIONS.CLEAR_HISTORY: {
      return {
        history: [state.history[state.currentIndex]],
        currentIndex: 0
      }
    }
    
    default:
      return state
  }
}

/**
 * useUndoRedo Hook
 * 
 * Provides undo/redo functionality for state management with history tracking.
 * Uses useReducer to prevent race conditions and ensure atomic state updates.
 * Supports up to 50 history steps to prevent memory issues.
 * 
 * SCOPE LIMITATION: This hook only tracks the specific state passed to it.
 * In Dashboard.jsx, only dashboardLayout is tracked. Other dashboard state
 * (systemMetrics, recentDecisions, performanceData) is NOT tracked.
 * 
 * For multi-state undo/redo, consider:
 * - Using a single state object containing all tracked data
 * - Implementing a global undo/redo manager
 * - Using a state management library with built-in time-travel (Redux DevTools)
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
  
  const [internalState, dispatch] = useReducer(undoRedoReducer, {
    history: [initialState],
    currentIndex: 0
  })
  
  const currentState = internalState.history[internalState.currentIndex]
  
  const canUndo = internalState.currentIndex > 0
  const canRedo = internalState.currentIndex < internalState.history.length - 1
  
  /**
   * Set a new state and add it to history
   * Clears any redo history after current index
   */
  const setState = useCallback((newState) => {
    dispatch({
      type: ACTIONS.SET_STATE,
      payload: { newState, maxHistory }
    })
  }, [maxHistory])
  
  /**
   * Undo to previous state
   */
  const undo = useCallback(() => {
    dispatch({ type: ACTIONS.UNDO })
  }, [])
  
  /**
   * Redo to next state
   */
  const redo = useCallback(() => {
    dispatch({ type: ACTIONS.REDO })
  }, [])
  
  /**
   * Reset to initial state and clear history
   */
  const reset = useCallback(() => {
    dispatch({
      type: ACTIONS.RESET,
      payload: { initialState }
    })
  }, [initialState])
  
  /**
   * Clear all history but keep current state
   */
  const clearHistory = useCallback(() => {
    dispatch({ type: ACTIONS.CLEAR_HISTORY })
  }, [])
  
  return {
    state: currentState,
    setState,
    undo,
    redo,
    canUndo,
    canRedo,
    reset,
    clearHistory,
    historyLength: internalState.history.length,
    currentIndex: internalState.currentIndex
  }
}

export default useUndoRedo
