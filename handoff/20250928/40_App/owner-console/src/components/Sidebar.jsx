import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  LayoutDashboard, 
  Shield,
  ShieldCheck,
  ShieldAlert,
  ListTodo,
  Users,
  Activity,
  BarChart3,
  Beaker
} from 'lucide-react'
import { Tooltip, TooltipTrigger, TooltipContent } from '@morningai/shared-ui'

/**
 * Sidebar component for owner-console with GitHub/Linear-style design.
 * 
 * Design: Clean, single-layer sidebar that works with GlobalHeader.
 * - No internal header (Logo and toggle moved to GlobalHeader)
 * - Accepts collapsed prop from parent (OwnerConsoleLayout)
 * - Tooltip on collapsed state for nav items
 * - Single-line menu items with 44px row height
 * 
 * @param {Object} props
 * @param {Object} props.user - Current user object
 * @param {boolean} props.collapsed - Whether sidebar is collapsed
 * @param {boolean} props.isMobileDrawer - Whether rendering in mobile drawer mode
 */
const Sidebar = ({ user, collapsed = false, isMobileDrawer = false }) => {
  const { t } = useTranslation()
  const location = useLocation()

  const menuItems = [
    {
      path: '/dashboard',
      icon: LayoutDashboard,
      labelKey: 'nav.dashboard'
    },
    {
      path: '/governance',
      icon: Shield,
      labelKey: 'nav.governance'
    },
    {
      path: '/approval-queue',
      icon: ShieldAlert,
      labelKey: 'nav.approvalQueue'
    },
    {
      path: '/sessions',
      icon: ListTodo,
      labelKey: 'nav.sessions'
    },
    {
      path: '/ai-policies',
      icon: ShieldCheck,
      labelKey: 'nav.aiPolicies'
    },
    {
      path: '/tenants',
      icon: Users,
      labelKey: 'nav.tenants'
    },
    {
      path: '/monitoring',
      icon: Activity,
      labelKey: 'nav.monitoring'
    },
    {
      path: '/ux-metrics',
      icon: BarChart3,
      labelKey: 'nav.uxMetrics'
    },
    {
      path: '/failure-experiments',
      icon: Beaker,
      labelKey: 'nav.failureExperiments'
    }
  ]

  const isActive = (path) => location.pathname === path

  const NavItem = ({ item }) => {
    const Icon = item.icon
    const active = isActive(item.path)
    
    const linkContent = (
      <Link
        to={item.path}
        className={`relative flex items-center h-11 px-3 rounded-lg text-sm font-medium transition-all duration-200 ${
          active
            ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
            : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
        }`}
        aria-current={active ? 'page' : undefined}
      >
        {active && (
          <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary-500 rounded-r-full transition-all duration-200" />
        )}
        <Icon 
          className={`w-5 h-5 flex-shrink-0 transition-colors duration-200 ${
            collapsed && !isMobileDrawer ? 'mx-auto' : 'mr-3'
          } ${active ? 'text-primary-600 dark:text-primary-400' : ''}`}
          strokeWidth={1.5}
        />
        {(!collapsed || isMobileDrawer) && (
          <span className="truncate">{t(item.labelKey)}</span>
        )}
      </Link>
    )

    // Show tooltip only when collapsed (not in mobile drawer mode)
    if (collapsed && !isMobileDrawer) {
      return (
        <Tooltip>
          <TooltipTrigger asChild>
            {linkContent}
          </TooltipTrigger>
          <TooltipContent
            side="right"
            sideOffset={8}
            className="z-50 bg-white text-neutral-900 rounded-md shadow-sm border border-neutral-200 px-2 py-1 text-xs"
          >
            {t(item.labelKey)}
          </TooltipContent>
        </Tooltip>
      )
    }

    return linkContent
  }

  // Determine width based on collapsed state and mobile drawer mode
  const sidebarWidth = isMobileDrawer 
    ? 'w-full' 
    : collapsed 
      ? 'w-16' 
      : 'w-64'

  return (
    <div className={`bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 transition-all duration-200 flex flex-col h-full ${sidebarWidth}`}>
      {/* Navigation */}
      <nav className="flex-1 p-2 overflow-y-auto" aria-label={t('nav.mainNavigation')}>
        <ul className="space-y-1">
          {menuItems.map((item) => (
            <li key={item.path}>
              <NavItem item={item} />
            </li>
          ))}
        </ul>
      </nav>
    </div>
  )
}

export default Sidebar
