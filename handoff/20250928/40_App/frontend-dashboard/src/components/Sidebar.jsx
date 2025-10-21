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
    <div className={`bg-white shadow-lg transition-all duration-300 ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <img 
                src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
                alt="Morning AI" 
                className="w-8 h-8 rounded-lg"
              />
              <div>
                <h1 className="text-lg font-bold text-gray-900">Morning AI</h1>
                <p className="text-xs text-gray-500">{t('app.tagline')}</p>
              </div>
            </div>
          )}
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setCollapsed(!collapsed)}
            className="p-1"
          >
            {collapsed ? (
              <ChevronRight className="w-4 h-4" />
            ) : (
              <ChevronLeft className="w-4 h-4" />
            )}
          </Button>
        </div>
      </div>

      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center space-x-3">
          <Avatar className="w-10 h-10">
            <AvatarImage src={user?.avatar} />
            <AvatarFallback className="bg-blue-100 text-blue-600">
              {user?.name?.charAt(0) || 'U'}
            </AvatarFallback>
          </Avatar>
          
          {!collapsed && (
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-gray-900 truncate">
                {user?.name || t('sidebar.defaultUser')}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user?.role || t('sidebar.defaultRole')}
              </p>
            </div>
          )}
        </div>
      </div>

      <nav className="flex-1 p-4">
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
                      ? 'bg-blue-50 text-blue-700 border-r-2 border-blue-700'
                      : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                  }`}
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
                        <p className="text-xs text-gray-400 mt-1">
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

      <div className="p-4 border-t border-gray-200">
        <Button
          variant="ghost"
          size="sm"
          onClick={onLogout}
          className={`w-full ${collapsed ? 'px-2' : 'justify-start'}`}
        >
          <LogOut className={`w-4 h-4 ${collapsed ? '' : 'mr-2'}`} />
          {!collapsed && t('common.logout')}
        </Button>
      </div>
    </div>
  )
}

export default Sidebar

