import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { 
  LayoutDashboard, 
  Settings, 
  Shield,
  Users,
  Activity,
  LogOut,
  ChevronLeft,
  ChevronRight
} from 'lucide-react'
import { Button, Avatar, AvatarFallback, AvatarImage } from '@morningai/shared-ui'
import { DarkModeToggle } from './DarkModeToggle'
import { LanguageSwitcher } from './LanguageSwitcher'

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
      path: '/settings',
      icon: Settings,
      labelKey: 'nav.settings',
      descriptionKey: 'settings.subtitle'
    }
  ]

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
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">{t('app.tagline')}</h1>
                <p className="text-xs text-gray-600 dark:text-gray-600">{t('tenants.subtitle')}</p>
              </div>
            </Link>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="p-1"
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
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
            <AvatarFallback className="bg-purple-100 dark:bg-purple-900 text-purple-600 dark:text-purple-300">
              {user?.name?.charAt(0) || 'O'}
            </AvatarFallback>
          </Avatar>
          
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 dark:text-white truncate">
                {user?.name || t('sidebar.user.defaultName')}
              </p>
              <p className="text-xs text-purple-600 dark:text-purple-400 truncate font-semibold">
                {user?.role || t('sidebar.user.defaultRole')}
              </p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 p-4" aria-label="Main navigation">
        <ul className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon
            const active = isActive(item.path)
            
            return (
              <li key={item.path}>
                <Link
                  to={item.path}
                  className={`flex items-center px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    active
                      ? 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-r-2 border-purple-700 dark:border-purple-400'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon className={`w-5 h-5 shrink-0 ${collapsed ? 'mx-auto' : 'mr-3'}`} />
                  
                  {!collapsed && (
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <span className="leading-tight">{t(item.labelKey)}</span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-600 mt-0.5 leading-tight">
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

      <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
        <div className={`flex ${collapsed ? 'justify-center' : 'justify-start'}`}>
          <DarkModeToggle variant={collapsed ? 'compact' : 'default'} />
        </div>
        <div className={`flex ${collapsed ? 'justify-center' : 'justify-start'}`}>
          <LanguageSwitcher variant={collapsed ? 'compact' : 'default'} />
        </div>
        <Button
          variant="ghost"
          size="sm"
          onClick={onLogout}
          className={`w-full ${collapsed ? 'px-2' : 'justify-start'} text-gray-600 dark:text-gray-300 hover:text-gray-900 dark:hover:text-white`}
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
