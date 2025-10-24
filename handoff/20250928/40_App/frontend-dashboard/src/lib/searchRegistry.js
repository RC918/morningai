/**
 * Search Registry
 * 
 * Centralized registry for all searchable items in the application.
 * This allows for easier maintenance and extension of search functionality.
 * 
 * To add new searchable items:
 * 1. Add the item to the appropriate category array
 * 2. Ensure all required fields are present (id, title, description, category, path/action, keywords, weight)
 * 3. Update i18n files with corresponding translation keys
 */

export const SEARCH_CATEGORIES = {
  PAGES: 'pages',
  WIDGETS: 'widgets',
  SETTINGS: 'settings',
  DOCS: 'docs'
}

/**
 * Get all searchable items
 * @param {Function} t - i18n translation function
 * @returns {Array} Array of searchable items
 */
export const getSearchableItems = (t) => {
  return [
    ...getPageItems(t),
    ...getWidgetItems(t),
    ...getSettingsItems(t),
    ...getDocsItems(t)
  ]
}

/**
 * Page navigation items
 */
const getPageItems = (t) => [
  {
    id: 'dashboard',
    title: t('nav.dashboard'),
    description: t('dashboard.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/dashboard',
    keywords: ['dashboard', 'home', 'overview', 'metrics'],
    weight: 10
  },
  {
    id: 'strategies',
    title: t('nav.strategies'),
    description: t('strategies.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/strategies',
    keywords: ['strategies', 'strategy', 'management', 'planning'],
    weight: 9
  },
  {
    id: 'approvals',
    title: t('nav.approvals'),
    description: t('approvals.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/approvals',
    keywords: ['approvals', 'approval', 'decisions', 'review'],
    weight: 8
  },
  {
    id: 'history',
    title: t('nav.history'),
    description: t('history.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/history',
    keywords: ['history', 'analysis', 'past', 'logs'],
    weight: 7
  },
  {
    id: 'costs',
    title: t('nav.costs'),
    description: t('costs.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/costs',
    keywords: ['costs', 'cost', 'analysis', 'spending', 'budget'],
    weight: 8
  },
  {
    id: 'governance',
    title: t('nav.governance'),
    description: t('governance.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/governance',
    keywords: ['governance', 'agent', 'management', 'control'],
    weight: 6
  },
  {
    id: 'settings',
    title: t('nav.settings'),
    description: t('settings.description'),
    category: SEARCH_CATEGORIES.PAGES,
    path: '/settings',
    keywords: ['settings', 'preferences', 'configuration', 'options'],
    weight: 7
  }
]

/**
 * Widget items (currently commented out - requires Dashboard integration)
 * Uncomment when Dashboard.addWidget is exposed globally or via context
 */
const getWidgetItems = (t) => [
]

/**
 * Settings items
 */
const getSettingsItems = (t) => [
  {
    id: 'profile-settings',
    title: t('settings.tabs.profile'),
    description: t('settings.profile.description'),
    category: SEARCH_CATEGORIES.SETTINGS,
    path: '/settings?tab=profile',
    keywords: ['profile', 'account', 'user', 'personal'],
    weight: 4
  },
  {
    id: 'notification-settings',
    title: t('settings.tabs.notifications'),
    description: t('settings.notifications.description'),
    category: SEARCH_CATEGORIES.SETTINGS,
    path: '/settings?tab=notifications',
    keywords: ['notifications', 'alerts', 'email', 'push'],
    weight: 4
  },
  {
    id: 'security-settings',
    title: t('settings.tabs.security'),
    description: t('settings.security.description'),
    category: SEARCH_CATEGORIES.SETTINGS,
    path: '/settings?tab=security',
    keywords: ['security', 'password', 'authentication', '2fa', 'mfa'],
    weight: 4
  }
]

/**
 * Documentation items (placeholder for future)
 */
const getDocsItems = (t) => [
]

export default {
  SEARCH_CATEGORIES,
  getSearchableItems
}
