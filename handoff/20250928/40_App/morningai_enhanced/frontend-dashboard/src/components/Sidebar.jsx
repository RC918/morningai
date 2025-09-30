import { useState } from 'react'
import { Link, useLocation } from 'react-router-dom'
import { 
  LayoutDashboard, 
  Settings, 
  TrendingUp, 
  CheckCircle, 
  History, 
  DollarSign,
  CreditCard,
  LogOut,
  User,
  ChevronLeft,
  ChevronRight,
  Brain
} from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'

const Sidebar = ({ user, onLogout }) => {
  const [collapsed, setCollapsed] = useState(false)
  const location = useLocation()

  const menuItems = [
    {
      path: '/dashboard',
      icon: LayoutDashboard,
      label: '監控儀表板',
      description: '系統狀態總覽'
    },
    {
      path: '/strategies',
      icon: Brain,
      label: '策略管理',
      description: '管理AI策略'
    },
    {
      path: '/approvals',
      icon: CheckCircle,
      label: '決策審批',
      description: '人工審核待辦',
      badge: '3' // 示例徽章
    },
    {
      path: '/history',
      icon: History,
      label: '歷史分析',
      description: '決策歷史回顧'
    },
    {
      path: '/costs',
      icon: DollarSign,
      label: '成本分析',
      description: 'AI服務成本'
    },
    {
      path: '/checkout',
      icon: CreditCard,
      label: '訂閱方案',
      description: '升級與付款'
    },
    {
      path: '/settings',
      icon: Settings,
      label: '系統設置',
      description: '配置管理'
    }
  ]

  const isActive = (path) => location.pathname === path

  return (
    <div className={`bg-white shadow-lg transition-all duration-300 ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      {/* 頭部 */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          {!collapsed && (
            <div className="flex items-center space-x-2">
              <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-white" />
              </div>
              <div>
                <h1 className="text-lg font-bold text-gray-900">Morning AI</h1>
                <p className="text-xs text-gray-500">智能決策系統</p>
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

      {/* 用戶信息 */}
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
                {user?.name || '管理員'}
              </p>
              <p className="text-xs text-gray-500 truncate">
                {user?.role || '系統管理員'}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* 導航菜單 */}
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

      {/* 底部操作 */}
      <div className="p-4 border-t border-gray-200">
        <Button
          variant="ghost"
          size="sm"
          onClick={onLogout}
          className={`w-full ${collapsed ? 'px-2' : 'justify-start'}`}
        >
          <LogOut className={`w-4 h-4 ${collapsed ? '' : 'mr-2'}`} />
          {!collapsed && '登出'}
        </Button>
      </div>
    </div>
  )
}

export default Sidebar

