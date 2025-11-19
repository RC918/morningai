/**
 * Dashboard Widget Filtering Utilities
 * 
 * Provides centralized filtering logic to prevent task_execution widget
 * (which contains owner-console agent names like GrowthStrategist, OpsAgent,
 * PMAgent, SecurityManager) from appearing in tenant dashboards.
 * 
 * All filtering is case-insensitive to handle legacy saved layouts that may
 * have used different casing.
 */

/**
 * Normalizes widget ID to lowercase for case-insensitive comparison
 */
export const normalizeWidgetId = (id: string): string => {
  return id.toLowerCase()
}

/**
 * Filters out task_execution widget from a list of widgets
 * 
 * This function is generic and works with any object that has an 'id' property.
 * Filtering is case-insensitive to handle legacy data.
 * 
 * @param widgets - Array of widgets to filter
 * @returns Filtered array with task_execution widget removed
 * 
 * @example
 * const widgets = [
 *   { id: 'cpu_usage', type: 'metric' },
 *   { id: 'task_execution', type: 'timeline' },
 *   { id: 'TASK_EXECUTION', type: 'timeline' }
 * ]
 * const filtered = excludeTaskExecution(widgets)
 * // Returns: [{ id: 'cpu_usage', type: 'metric' }]
 */
export const excludeTaskExecution = <T extends { id: string }>(widgets: T[]): T[] => {
  return widgets.filter((widget) => normalizeWidgetId(widget.id) !== 'task_execution')
}
