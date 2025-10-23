import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  LayoutDashboard, 
  Settings, 
  TrendingUp, 
  CheckCircle, 
  History, 
  DollarSign,
  Shield,
  LogOut,
  User,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  CreditCard
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { isFeatureEnabled, AVAILABLE_FEATURES } from '@/lib/feature-flags'
import { DarkModeToggle } from './DarkModeToggle'
import { LanguageSwitcher } from './LanguageSwitcher'

const Sidebar = ({ user, onLogout }) => {
  const { t } = useTranslation()
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const allMenuItems = [
    {
      path: '/dashboard',
      icon: LayoutDashboard,
      label: t('sidebar.dashboard.label'),
      description: t('sidebar.dashboard.description'),
      feature: AVAILABLE_FEATURES.DASHBOARD
    },
    {
      path: '/strategies',
      icon: Sparkles,
      label: t('sidebar.strategies.label'),
      description: t('sidebar.strategies.description'),
      feature: AVAILABLE_FEATURES.STRATEGIES
    },
    {
      path: '/approvals',
      icon: CheckCircle,
      label: t('sidebar.approvals.label'),
      description: t('sidebar.approvals.description'),
      badge: '3',
      feature: AVAILABLE_FEATURES.APPROVALS
    },
    {
      path: '/history',
      icon: History,
      label: t('sidebar.history.label'),
      description: t('sidebar.history.description'),
      feature: AVAILABLE_FEATURES.HISTORY
    },
    {
      path: '/costs',
      icon: DollarSign,
      label: t('sidebar.costs.label'),
      description: t('sidebar.costs.description'),
      feature: AVAILABLE_FEATURES.COSTS
    },
    {
      path: '/governance',
      icon: Shield,
      label: 'Agent Governance',
      description: 'Monitor agent reputation and compliance',
      feature: AVAILABLE_FEATURES.GOVERNANCE
    },
    {
      path: '/settings',
      icon: Settings,
      label: t('sidebar.settings.label'),
      description: t('sidebar.settings.description'),
      feature: AVAILABLE_FEATURES.SETTINGS
    },
    {
      path: '/checkout',
      icon: CreditCard,
      label: t('sidebar.checkout.label'),
      description: t('sidebar.checkout.description'),
      feature: AVAILABLE_FEATURES.CHECKOUT
    }
  ]

  const menuItems = allMenuItems.filter(item => isFeatureEnabled(item.feature))

  const isActive = (path) => location.pathname === path

  return (
    <div className={`bg-white dark:bg-gray-900 shadow-lg transition-all duration-300 ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center justify-between">
          {collapsed ? (
            <Link to="/dashboard" className="hover:opacity-80 transition-opacity">
              <img 
                src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                alt="Morning AI" 
                className="w-10 h-10 rounded-lg shadow-sm"
                style={{ width: '40px', height: '40px', maxWidth: '40px', maxHeight: '40px' }}
              />
            </Link>
          ) : (
            <Link to="/dashboard" className="flex items-center space-x-3 hover:opacity-80 transition-opacity">
              <img 
                src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                alt="Morning AI" 
                className="w-10 h-10 rounded-lg shadow-sm"
                style={{ width: '40px', height: '40px', maxWidth: '40px', maxHeight: '40px' }}
              />
              <div>
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">Morning AI</h1>
                <p className="text-xs text-gray-600 dark:text-gray-600">{t('sidebar.header.subtitle')}</p>
              </div>
            </Link>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="p-1"
            aria-label={collapsed ? t('accessibility.expandSection') : t('accessibility.collapseSection')}
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

      <div className="p-4 border-b border-gray-200 dark:border-gray-700">
        <div className="flex items-center space-x-3">
          <Avatar className="w-10 h-10">
            <AvatarImage src={user?.avatar} />
            <AvatarFallback className="bg-blue-100 dark:bg-blue-900 text-blue-600 dark:text-blue-300">
              {user?.name?.charAt(0) || 'U'}
            </AvatarFallback>
          </Avatar>
          
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {user?.name || t('sidebar.user.defaultName')}
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-600 truncate">
                {user?.role || t('sidebar.user.defaultRole')}
              </p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 p-4" aria-label={t('sidebar.navigation', 'Main navigation')}>
        <ul className="space-y-2" role="list">
          {menuItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 border-r-2 border-blue-700 dark:border-blue-400'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  aria-current={active ? 'page' : undefined}
                  aria-label={`${item.label}${item.badge ? ` (${item.badge} ${t('accessibility.info', 'notifications')})` : ''}`}
                >
                  <Icon className={`w-5 h-5 ${collapsed ? 'mx-auto' : 'mr-3'}`} />
                  
                  {!collapsed && (
                    <>
                      <div className="flex-1">
                        <div className="flex items-center justify-between">
                          <span>{item.label}</span>
                          {item.badge && (
                            <span className="bg-red-100 text-red-600 text-xs px-2 py-1 rounded-full">
                              {item.badge}
                            </span>
                          )}
                        </div>
                        <p className="text-xs text-gray-600 dark:text-gray-600 mt-1">
                          {item.description}
                        </p>
                      </div>
                    </>
                  )}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        <div className={`flex ${collapsed ? 'flex-col gap-2' : 'gap-2'}`}>
          <DarkModeToggle variant={collapsed ? 'compact' : 'default'} />
          <LanguageSwitcher variant={collapsed ? 'compact' : 'default'} />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onLogout}
          className={`w-full ${collapsed ? 'px-2' : 'justify-start'} text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white`}
          aria-label={t('sidebar.logout')}
        >
          <LogOut className={`w-4 h-4 ${collapsed ? '' : 'mr-2'}`} />
          {!collapsed && t('sidebar.logout')}
        </Button>
      </div>
    </div>
  )
}

export default Sidebar

