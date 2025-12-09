import { useState } from 'react'
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
  Beaker,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button, Tooltip, TooltipTrigger, TooltipContent } from '@morningai/shared-ui'

/**
 * Sidebar component for owner-console with iotask-style light theme.
 * 
 * Design Decision: Updated to use light theme following iotask design reference.
 * Uses a thin blue vertical bar indicator for active navigation items instead of
 * full background color, creating a cleaner, more modern SaaS appearance.
 * 
 * Optimizations (2024-12):
 * - Single-line menu items (removed description text)
 * - 44px row height for better density
 * - Tooltip on collapsed state (industry standard: Linear, Notion, Slack, Vercel)
 * - Enhanced expand/collapse control with hover feedback and animation
 * - Unified icon specs (20x20px)
 */
const Sidebar = ({ user }) => {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
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
            collapsed ? 'mx-auto' : 'mr-3'
          } ${active ? 'text-primary-600 dark:text-primary-400' : ''}`}
          strokeWidth={1.5}
        />
        {!collapsed && (
          <span className="truncate">{t(item.labelKey)}</span>
        )}
      </Link>
    )

    if (collapsed) {
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

  return (
    <div className={`bg-white dark:bg-neutral-900 border-r border-neutral-200 dark:border-neutral-700 transition-all duration-300 flex flex-col ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="p-4 border-b border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center justify-between">
          {collapsed ? (
            <Link to="/dashboard" className="hover:opacity-80 transition-opacity">
              <img 
                src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                alt="Morning AI" 
                className="w-10 h-10 rounded-lg"
                style={{ width: '40px', height: '40px', maxWidth: '40px', maxHeight: '40px' }}
              />
            </Link>
          ) : (
            <Link to="/dashboard" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <img 
                src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                alt="Morning AI" 
                className="w-10 h-10 rounded-lg"
                style={{ width: '40px', height: '40px', maxWidth: '40px', maxHeight: '40px' }}
              />
              <div>
                <h1 className="text-lg font-semibold text-neutral-900 dark:text-white">{t('app.tagline')}</h1>
                <p className="text-xs text-neutral-500 dark:text-neutral-400">{t('tenants.subtitle')}</p>
              </div>
            </Link>
          )}
          
{collapsed ? (
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCollapsed(!collapsed)}
                  className="group h-9 w-9 rounded-lg p-2 text-neutral-500 hover:bg-primary-500/10 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-primary-500/15 dark:hover:text-white transition-colors duration-150"
                  aria-label={t('sidebar.expand')}
                  aria-expanded={false}
                >
                  <ChevronRight 
                    className="w-5 h-5 opacity-60 group-hover:opacity-100 transition-all duration-150"
                    strokeWidth={1.5}
                  />
                </Button>
              </TooltipTrigger>
              <TooltipContent
                side="right"
                sideOffset={8}
                className="z-50 bg-white text-neutral-900 rounded-md shadow-sm border border-neutral-200 px-2 py-1 text-xs"
              >
                {t('sidebar.expand')}
              </TooltipContent>
            </Tooltip>
          ) : (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setCollapsed(!collapsed)}
              className="group h-9 w-9 rounded-lg p-2 text-neutral-500 hover:bg-primary-500/10 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-primary-500/15 dark:hover:text-white transition-colors duration-150"
              aria-label={t('sidebar.collapse')}
              aria-expanded={true}
            >
              <ChevronRight 
                className="w-5 h-5 rotate-180 opacity-60 group-hover:opacity-100 transition-all duration-150"
                strokeWidth={1.5}
              />
            </Button>
          )}
        </div>
      </div>

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
