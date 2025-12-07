/**
 * Session-related constants for confidence scoring and approval workflows.
 * 
 * These constants are shared across Sessions.jsx and ConfidenceApproval.jsx
 * to ensure consistent behavior and easier maintenance.
 * 
 * Issue: #1823 (Tier 4 - Sessions UI/UX optimization)
 */

/**
 * High confidence threshold - sessions at or above this score are considered
 * high confidence and display with positive (green) indicators.
 * @type {number}
 */
export const CONFIDENCE_THRESHOLD = 0.8

/**
 * Medium confidence threshold - sessions between this and CONFIDENCE_THRESHOLD
 * are considered medium confidence and display with warning (yellow) indicators.
 * Sessions below this threshold are considered low confidence.
 * @type {number}
 */
export const MEDIUM_CONFIDENCE_THRESHOLD = 0.6

/**
 * Validates a confidence score and returns a safe value.
 * Handles null, undefined, NaN, and out-of-range values.
 * 
 * @param {number|null|undefined} confidence - The confidence score to validate
 * @param {number} defaultValue - Default value to return if invalid (default: 0)
 * @returns {number} A valid confidence score between 0 and 1
 */
export const validateConfidence = (confidence, defaultValue = 0) => {
  // Handle null, undefined, or non-number types
  if (confidence === null || confidence === undefined) {
    return defaultValue
  }
  
  // Handle NaN
  if (typeof confidence !== 'number' || Number.isNaN(confidence)) {
    return defaultValue
  }
  
  // Clamp to valid range [0, 1]
  if (confidence < 0) return 0
  if (confidence > 1) return 1
  
  return confidence
}

/**
 * Gets the confidence level category based on the score.
 * 
 * @param {number} confidence - The confidence score (0-1)
 * @returns {'high' | 'medium' | 'low'} The confidence level category
 */
export const getConfidenceLevel = (confidence) => {
  const validConfidence = validateConfidence(confidence)
  
  if (validConfidence >= CONFIDENCE_THRESHOLD) return 'high'
  if (validConfidence >= MEDIUM_CONFIDENCE_THRESHOLD) return 'medium'
  return 'low'
}
