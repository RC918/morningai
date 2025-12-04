import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Search, Bell, Settings, HelpCircle } from 'lucide-react'
import { Button, Avatar, AvatarFallback, AvatarImage } from '@morningai/shared-ui'
import { LanguageSwitcher } from './LanguageSwitcher'

const DashboardHeader = ({ user, title, subtitle, notificationCount = 0 }) => {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')
  const hasNotifications = notificationCount > 0

  return (
    <header className="bg-white border-b border-neutral-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <h1 className="text-xl font-semibold text-neutral-800">
            {title || t('dashboard.title')}
          </h1>
          {subtitle && (
            <p className="text-sm text-neutral-500 mt-1">{subtitle}</p>
          )}
        </div>

        <div className="flex items-center space-x-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
            <input
              type="text"
              placeholder={t('header.searchPlaceholder', 'Search...')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-8 pr-4 py-2 w-64 bg-neutral-100 border-0 rounded-lg text-sm text-neutral-700 placeholder-neutral-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white transition-colors"
            />
          </div>

          <Button
            variant="ghost"
            size="sm"
            className="p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 rounded-lg"
            aria-label={t('header.help')}
          >
            <HelpCircle className="w-5 h-5" />
          </Button>

                    <Button
                      variant="ghost"
                      size="sm"
                      className="p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 rounded-lg relative"
                      aria-label={t('header.notifications')}
                    >
                      <Bell className="w-5 h-5" />
                      {hasNotifications && (
                        <span className="absolute top-1 right-1 w-2 h-2 bg-pink-500 rounded-full"></span>
                      )}
                    </Button>

          <Button
            variant="ghost"
            size="sm"
            className="p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 rounded-lg"
            aria-label={t('header.settings')}
          >
            <Settings className="w-5 h-5" />
          </Button>

          <LanguageSwitcher variant="compact" className="border-none bg-transparent shadow-none text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100" />

          <div className="flex items-center space-x-3 pl-4 border-l border-neutral-200">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={user?.avatar} alt={user?.name ? `${user.name}'s avatar` : 'User avatar'} />
                          <AvatarFallback className="bg-primary-500 text-white text-sm">
                            {user?.name?.charAt(0) || 'U'}
                          </AvatarFallback>
                        </Avatar>
            <div className="hidden md:block">
              <p className="text-sm font-medium text-neutral-700">
                {user?.name || t('header.defaultUser')}
              </p>
              <p className="text-xs text-neutral-500">
                {user?.role || t('header.defaultRole')}
              </p>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}

export default DashboardHeader
