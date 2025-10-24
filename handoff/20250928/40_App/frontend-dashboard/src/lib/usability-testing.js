/**
 * Usability Testing Framework
 * 
 * Provides automated data collection for usability testing sessions:
 * - Session tracking and timing
 * - Task completion tracking
 * - User interaction recording
 * - Automatic metric calculation (TTV, success rates)
 * - Integration with SUS and NPS surveys
 * 
 * @module usability-testing
 */

import * as Sentry from '@sentry/react'

/**
 * Usability Testing Session Manager
 */
class UsabilityTestingSession {
  constructor(participantId, sessionId) {
    this.participantId = participantId
    this.sessionId = sessionId || `session-${Date.now()}`
    this.startTime = Date.now()
    this.tasks = []
    this.interactions = []
    this.currentTask = null
    this.isRecording = false
  }

  /**
   * Start recording a usability testing session
   */
  startSession() {
    this.isRecording = true
    this.startTime = Date.now()

    Sentry.captureMessage('Usability Testing Session Started', {
      level: 'info',
      tags: {
        type: 'usability_test',
        participant_id: this.participantId,
        session_id: this.sessionId
      },
      extra: {
        start_time: new Date(this.startTime).toISOString()
      }
    })

    this._saveSession()

    console.log(`[Usability Test] Session started: ${this.sessionId}`)
  }

  /**
   * Start tracking a specific task
   * @param {string} taskId - Unique task identifier (e.g., 'scenario-1-login')
   * @param {string} taskName - Human-readable task name
   * @param {string} description - Task description
   */
  startTask(taskId, taskName, description) {
    if (!this.isRecording) {
      console.warn('[Usability Test] Session not started. Call startSession() first.')
      return
    }

    const task = {
      taskId,
      taskName,
      description,
      startTime: Date.now(),
      endTime: null,
      duration: null,
      success: null,
      errors: [],
      interactions: [],
      notes: []
    }

    this.currentTask = task
    this.tasks.push(task)

    Sentry.captureMessage('Usability Test Task Started', {
      level: 'info',
      tags: {
        type: 'usability_test_task',
        participant_id: this.participantId,
        session_id: this.sessionId,
        task_id: taskId
      },
      extra: {
        task_name: taskName,
        description
      }
    })

    this._saveSession()

    console.log(`[Usability Test] Task started: ${taskName}`)
  }

  /**
   * End the current task
   * @param {boolean} success - Whether the task was completed successfully
   * @param {string} notes - Optional notes about task completion
   */
  endTask(success, notes = '') {
    if (!this.currentTask) {
      console.warn('[Usability Test] No active task to end.')
      return
    }

    this.currentTask.endTime = Date.now()
    this.currentTask.duration = this.currentTask.endTime - this.currentTask.startTime
    this.currentTask.success = success
    if (notes) {
      this.currentTask.notes.push(notes)
    }

    Sentry.captureMessage('Usability Test Task Completed', {
      level: 'info',
      tags: {
        type: 'usability_test_task',
        participant_id: this.participantId,
        session_id: this.sessionId,
        task_id: this.currentTask.taskId,
        success: success ? 'true' : 'false'
      },
      extra: {
        task_name: this.currentTask.taskName,
        duration_ms: this.currentTask.duration,
        duration_seconds: Math.round(this.currentTask.duration / 1000),
        success,
        notes
      }
    })

    this._saveSession()

    console.log(`[Usability Test] Task ended: ${this.currentTask.taskName} (${success ? 'SUCCESS' : 'FAILED'})`)
    this.currentTask = null
  }

  /**
   * Record an error or issue during a task
   * @param {string} errorType - Type of error (e.g., 'navigation', 'confusion', 'technical')
   * @param {string} description - Description of the error
   */
  recordError(errorType, description) {
    if (!this.currentTask) {
      console.warn('[Usability Test] No active task. Error not recorded.')
      return
    }

    const error = {
      timestamp: Date.now(),
      type: errorType,
      description
    }

    this.currentTask.errors.push(error)

    Sentry.captureMessage('Usability Test Error', {
      level: 'warning',
      tags: {
        type: 'usability_test_error',
        participant_id: this.participantId,
        session_id: this.sessionId,
        task_id: this.currentTask.taskId,
        error_type: errorType
      },
      extra: {
        description,
        task_name: this.currentTask.taskName
      }
    })

    this._saveSession()
  }

  /**
   * Record a user interaction
   * @param {string} action - Type of action (e.g., 'click', 'scroll', 'input')
   * @param {string} target - Target element or description
   * @param {object} metadata - Additional metadata
   */
  recordInteraction(action, target, metadata = {}) {
    if (!this.isRecording) return

    const interaction = {
      timestamp: Date.now(),
      action,
      target,
      metadata,
      taskId: this.currentTask?.taskId || null
    }

    this.interactions.push(interaction)

    if (this.currentTask) {
      this.currentTask.interactions.push(interaction)
    }

    this._saveSession()
  }

  /**
   * Add a note to the current task
   * @param {string} note - Note text
   */
  addNote(note) {
    if (!this.currentTask) {
      console.warn('[Usability Test] No active task. Note not recorded.')
      return
    }

    this.currentTask.notes.push({
      timestamp: Date.now(),
      text: note
    })

    this._saveSession()
  }

  /**
   * End the usability testing session
   */
  endSession() {
    if (!this.isRecording) {
      console.warn('[Usability Test] Session not started.')
      return
    }

    this.isRecording = false
    const endTime = Date.now()
    const totalDuration = endTime - this.startTime

    const sessionSummary = this.getSessionSummary()

    Sentry.captureMessage('Usability Testing Session Ended', {
      level: 'info',
      tags: {
        type: 'usability_test',
        participant_id: this.participantId,
        session_id: this.sessionId
      },
      extra: {
        end_time: new Date(endTime).toISOString(),
        total_duration_ms: totalDuration,
        total_duration_minutes: Math.round(totalDuration / 60000),
        ...sessionSummary
      }
    })

    this._saveSession()

    console.log(`[Usability Test] Session ended: ${this.sessionId}`)
    console.log('Session Summary:', sessionSummary)

    return sessionSummary
  }

  /**
   * Get session summary with metrics
   */
  getSessionSummary() {
    const completedTasks = this.tasks.filter(t => t.endTime !== null)
    const successfulTasks = completedTasks.filter(t => t.success)
    const failedTasks = completedTasks.filter(t => !t.success)

    const totalErrors = this.tasks.reduce((sum, task) => sum + task.errors.length, 0)

    const avgTaskDuration = completedTasks.length > 0
      ? completedTasks.reduce((sum, task) => sum + task.duration, 0) / completedTasks.length
      : 0

    return {
      session_id: this.sessionId,
      participant_id: this.participantId,
      total_duration_ms: Date.now() - this.startTime,
      total_duration_minutes: Math.round((Date.now() - this.startTime) / 60000),
      tasks_total: this.tasks.length,
      tasks_completed: completedTasks.length,
      tasks_successful: successfulTasks.length,
      tasks_failed: failedTasks.length,
      success_rate: completedTasks.length > 0 
        ? (successfulTasks.length / completedTasks.length * 100).toFixed(1) + '%'
        : '0%',
      total_errors: totalErrors,
      total_interactions: this.interactions.length,
      avg_task_duration_ms: Math.round(avgTaskDuration),
      avg_task_duration_seconds: Math.round(avgTaskDuration / 1000),
      tasks: this.tasks.map(t => ({
        task_id: t.taskId,
        task_name: t.taskName,
        duration_seconds: t.duration ? Math.round(t.duration / 1000) : null,
        success: t.success,
        errors: t.errors.length,
        interactions: t.interactions.length
      }))
    }
  }

  /**
   * Export session data for analysis
   */
  exportData() {
    return {
      session_id: this.sessionId,
      participant_id: this.participantId,
      start_time: new Date(this.startTime).toISOString(),
      end_time: this.isRecording ? null : new Date().toISOString(),
      tasks: this.tasks,
      interactions: this.interactions,
      summary: this.getSessionSummary()
    }
  }

  /**
   * Save session to localStorage
   * @private
   */
  _saveSession() {
    try {
      const data = this.exportData()
      localStorage.setItem(`usability_test_${this.sessionId}`, JSON.stringify(data))
    } catch (error) {
      console.error('[Usability Test] Failed to save session:', error)
    }
  }

  /**
   * Load session from localStorage
   * @param {string} sessionId - Session ID to load
   * @returns {UsabilityTestingSession|null}
   */
  static loadSession(sessionId) {
    try {
      const data = localStorage.getItem(`usability_test_${sessionId}`)
      if (!data) return null

      const parsed = JSON.parse(data)
      const session = new UsabilityTestingSession(parsed.participant_id, parsed.session_id)
      session.startTime = new Date(parsed.start_time).getTime()
      session.tasks = parsed.tasks
      session.interactions = parsed.interactions
      session.isRecording = parsed.end_time === null

      return session
    } catch (error) {
      console.error('[Usability Test] Failed to load session:', error)
      return null
    }
  }

  /**
   * List all saved sessions
   * @returns {Array<string>} Array of session IDs
   */
  static listSessions() {
    const sessions = []
    for (let i = 0; i < localStorage.length; i++) {
      const key = localStorage.key(i)
      if (key && key.startsWith('usability_test_')) {
        sessions.push(key.replace('usability_test_', ''))
      }
    }
    return sessions
  }

  /**
   * Delete a session
   * @param {string} sessionId - Session ID to delete
   */
  static deleteSession(sessionId) {
    localStorage.removeItem(`usability_test_${sessionId}`)
  }
}

/**
 * SUS (System Usability Scale) Calculator
 */
export class SUSCalculator {
  /**
   * Calculate SUS score from responses
   * @param {Array<number>} responses - Array of 10 responses (1-5 scale)
   * @returns {object} SUS score and grade
   */
  static calculate(responses) {
    if (responses.length !== 10) {
      throw new Error('SUS requires exactly 10 responses')
    }

    if (responses.some(r => r < 1 || r > 5)) {
      throw new Error('All responses must be between 1 and 5')
    }

    let score = 0
    for (let i = 0; i < 10; i++) {
      if (i % 2 === 0) {
        score += responses[i] - 1
      } else {
        score += 5 - responses[i]
      }
    }

    const finalScore = score * 2.5

    let grade
    if (finalScore >= 80.3) grade = 'A'
    else if (finalScore >= 68) grade = 'B'
    else if (finalScore >= 51) grade = 'C'
    else if (finalScore >= 38) grade = 'D'
    else grade = 'F'

    let adjective
    if (finalScore >= 85) adjective = 'Excellent'
    else if (finalScore >= 73) adjective = 'Good'
    else if (finalScore >= 52) adjective = 'OK'
    else if (finalScore >= 39) adjective = 'Poor'
    else adjective = 'Awful'

    return {
      score: finalScore,
      grade,
      adjective,
      responses,
      calculation: {
        raw_score: score,
        multiplier: 2.5
      }
    }
  }

  /**
   * Get SUS questions
   * @returns {Array<string>} Array of 10 SUS questions
   */
  static getQuestions() {
    return [
      'I think that I would like to use this system frequently',
      'I found the system unnecessarily complex',
      'I thought the system was easy to use',
      'I think that I would need the support of a technical person to be able to use this system',
      'I found the various functions in this system were well integrated',
      'I thought there was too much inconsistency in this system',
      'I would imagine that most people would learn to use this system very quickly',
      'I found the system very cumbersome to use',
      'I felt very confident using the system',
      'I needed to learn a lot of things before I could get going with this system'
    ]
  }
}

/**
 * NPS (Net Promoter Score) Calculator
 */
export class NPSCalculator {
  /**
   * Calculate NPS from responses
   * @param {Array<number>} responses - Array of responses (0-10 scale)
   * @returns {object} NPS score and breakdown
   */
  static calculate(responses) {
    if (responses.some(r => r < 0 || r > 10)) {
      throw new Error('All responses must be between 0 and 10')
    }

    const total = responses.length
    const promoters = responses.filter(r => r >= 9).length
    const passives = responses.filter(r => r >= 7 && r <= 8).length
    const detractors = responses.filter(r => r <= 6).length

    const promoterPercentage = (promoters / total) * 100
    const detractorPercentage = (detractors / total) * 100
    const nps = promoterPercentage - detractorPercentage

    let rating
    if (nps >= 70) rating = 'Excellent'
    else if (nps >= 50) rating = 'Great'
    else if (nps >= 30) rating = 'Good'
    else if (nps >= 0) rating = 'Needs Improvement'
    else rating = 'Critical'

    return {
      nps: Math.round(nps),
      rating,
      breakdown: {
        promoters,
        promoter_percentage: Math.round(promoterPercentage),
        passives,
        passive_percentage: Math.round((passives / total) * 100),
        detractors,
        detractor_percentage: Math.round(detractorPercentage),
        total
      },
      responses
    }
  }

  /**
   * Get NPS question
   * @returns {string} NPS question
   */
  static getQuestion() {
    return 'How likely are you to recommend this product to a friend or colleague? (0 = Not at all likely, 10 = Extremely likely)'
  }
}

/**
 * Global usability testing instance
 */
let globalSession = null

/**
 * Initialize usability testing
 * @param {string} participantId - Unique participant identifier
 * @param {string} sessionId - Optional session identifier
 * @returns {UsabilityTestingSession}
 */
export function initUsabilityTest(participantId, sessionId) {
  globalSession = new UsabilityTestingSession(participantId, sessionId)
  globalSession.startSession()
  
  if (typeof window !== 'undefined') {
    window.usabilityTest = globalSession
  }
  
  return globalSession
}

/**
 * Get current usability testing session
 * @returns {UsabilityTestingSession|null}
 */
export function getCurrentSession() {
  return globalSession
}

/**
 * Quick access functions for common operations
 */
export const usabilityTest = {
  start: (participantId, sessionId) => initUsabilityTest(participantId, sessionId),
  startTask: (taskId, taskName, description) => globalSession?.startTask(taskId, taskName, description),
  endTask: (success, notes) => globalSession?.endTask(success, notes),
  recordError: (type, description) => globalSession?.recordError(type, description),
  recordInteraction: (action, target, metadata) => globalSession?.recordInteraction(action, target, metadata),
  addNote: (note) => globalSession?.addNote(note),
  end: () => globalSession?.endSession(),
  getSummary: () => globalSession?.getSessionSummary(),
  export: () => globalSession?.exportData(),
  getCurrentSession,
  loadSession: UsabilityTestingSession.loadSession,
  listSessions: UsabilityTestingSession.listSessions,
  deleteSession: UsabilityTestingSession.deleteSession
}

export default UsabilityTestingSession
