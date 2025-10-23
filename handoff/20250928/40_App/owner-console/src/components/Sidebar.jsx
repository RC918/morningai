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
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { DarkModeToggle } from './DarkModeToggle'
import { LanguageSwitcher } from './LanguageSwitcher'

const Sidebar = ({ user, onLogout }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()
  const { t } = useTranslation()

  const menuItems = [
    {
      path: '/dashboard',
      icon: LayoutDashboard,
      label: t('nav.dashboard'),
      description: t('dashboard.subtitle')
    },
    {
      path: '/governance',
      icon: Shield,
      label: t('nav.governance'),
      description: t('governance.subtitle')
    },
    {
      path: '/tenants',
      icon: Users,
      label: t('nav.tenants'),
      description: t('tenants.subtitle')
    },
    {
      path: '/monitoring',
      icon: Activity,
      label: t('nav.monitoring'),
      description: t('monitoring.subtitle')
    },
    {
      path: '/settings',
      icon: Settings,
      label: t('nav.settings'),
      description: t('settings.subtitle')
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
                <h1 className="text-lg font-bold text-gray-900 dark:text-white">Owner Console</h1>
                <p className="text-xs text-gray-600 dark:text-gray-600">Platform Management</p>
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
                {user?.name || 'Owner'}
              </p>
              <p className="text-xs text-purple-600 dark:text-purple-400 truncate font-semibold">
                {user?.role || 'Platform Owner'}
              </p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 p-4" aria-label="Main navigation">
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
                      ? 'bg-purple-50 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 border-r-2 border-purple-700 dark:border-purple-400'
                      : 'text-gray-600 dark:text-gray-300 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-gray-900 dark:hover:text-white'
                  }`}
                  aria-current={active ? 'page' : undefined}
                >
                  <Icon className={`w-5 h-5 ${collapsed ? 'mx-auto' : 'mr-3'}`} />
                  
                  {!collapsed && (
                    <div className="flex-1">
                      <div className="flex items-center justify-between">
                        <span>{item.label}</span>
                      </div>
                      <p className="text-xs text-gray-600 dark:text-gray-600 mt-1">
                        {item.description}
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
          aria-label={t('auth.logout')}
        >
          <LogOut className={`w-4 h-4 ${collapsed ? '' : 'mr-2'}`} />
          {!collapsed && t('auth.logout')}
        </Button>
      </div>
    </div>
  )
}

export default Sidebar
