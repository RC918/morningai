import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  LayoutDashboard, 
  Settings, 
  Shield,
  ShieldCheck,
  ShieldAlert,
  ListTodo,
  Users,
  Activity,
  BarChart3,
  Beaker,
  LogOut,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button } from '@morningai/shared-ui'
import { DarkModeToggle } from './DarkModeToggle'

/**
 * Sidebar component for owner-console with iotask-style light theme.
 * 
 * Design Decision: Updated to use light theme following iotask design reference.
 * Uses a thin blue vertical bar indicator for active navigation items instead of
 * full background color, creating a cleaner, more modern SaaS appearance.
 */
const Sidebar = ({ user, onLogout }) => {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const menuItems = [
    {
      path: '/dashboard',
      icon: LayoutDashboard,
      labelKey: 'nav.dashboard',
      descriptionKey: 'dashboard.subtitle'
    },
                {
                  path: '/governance',
                  icon: Shield,
                  labelKey: 'nav.governance',
                  descriptionKey: 'governance.subtitle'
                },
                {
                  path: '/approval-queue',
                  icon: ShieldAlert,
                  labelKey: 'nav.approvalQueue',
                  descriptionKey: 'approvalQueue.subtitle'
                },
                {
                  path: '/sessions',
                  icon: ListTodo,
                  labelKey: 'nav.sessions',
                  descriptionKey: 'sessions.subtitle'
                },
                {
                  path: '/ai-policies',
                  icon: ShieldCheck,
                  labelKey: 'nav.aiPolicies',
                  descriptionKey: 'aiPolicies.subtitle'
                },
        {
          path: '/tenants',
      icon: Users,
      labelKey: 'nav.tenants',
      descriptionKey: 'tenants.subtitle'
    },
    {
      path: '/monitoring',
      icon: Activity,
      labelKey: 'nav.monitoring',
      descriptionKey: 'monitoring.subtitle'
    },
        {
          path: '/ux-metrics',
          icon: BarChart3,
          labelKey: 'nav.uxMetrics',
          descriptionKey: 'uxMetrics.subtitle'
        },
        {
          path: '/failure-experiments',
          icon: Beaker,
          labelKey: 'nav.failureExperiments',
          descriptionKey: 'failureExperiment.subtitle'
        },
        {
          path: '/settings',
      icon: Settings,
      labelKey: 'nav.settings',
      descriptionKey: 'settings.subtitle'
    }
  ]

  const isActive = (path) => location.pathname === path

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
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="p-1 text-neutral-400 hover:text-neutral-600 hover:bg-neutral-100 dark:hover:text-white dark:hover:bg-neutral-700"
            aria-label={collapsed ? t('sidebar.expand') : t('sidebar.collapse')}
            aria-expanded={!collapsed}
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      <nav className="flex-1 p-4 overflow-y-auto" aria-label={t('nav.mainNavigation')}>
        <ul className="space-y-1">
          {menuItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`relative flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
                      : 'text-neutral-600 hover:bg-neutral-100 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-neutral-800 dark:hover:text-white'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  {/* iotask-style: thin blue vertical bar indicator for active state */}
                  {active && (
                    <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-6 bg-primary-500 rounded-r-full" />
                  )}
                  <Icon className={`w-5 h-5 ${collapsed ? 'mx-auto' : 'mr-3'} ${active ? 'text-primary-600 dark:text-primary-400' : ''}`} />
                  
                  {!collapsed && (
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span>{t(item.labelKey)}</span>
                      </div>
                      <p className={`text-xs mt-1 ${active ? 'text-primary-500 dark:text-primary-300' : 'text-neutral-500'}`}>
                        {t(item.descriptionKey)}
                      </p>
                    </div>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-neutral-200 dark:border-neutral-700 space-y-2 mt-auto">
        <div className={`flex ${collapsed ? 'justify-center' : 'justify-start'}`}>
          <DarkModeToggle variant={collapsed ? 'compact' : 'default'} />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onLogout}
          className={`w-full ${collapsed ? 'px-2' : 'justify-start'} text-neutral-500 hover:text-neutral-900 hover:bg-neutral-100 dark:text-neutral-400 dark:hover:text-white dark:hover:bg-neutral-700`}
          aria-label={t('nav.logout')}
        >
          <LogOut className={`w-4 h-4 ${collapsed ? '' : 'mr-2'}`} />
          {!collapsed && t('nav.logout')}
        </Button>
      </div>
    </div>
  )
}

export default Sidebar
