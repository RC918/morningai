import { useState } from 'react'
import { useTranslation } from 'react-i18next'
import { Link } from 'react-router-dom'
import { Search, Bell, HelpCircle, Settings, LogOut, PanelLeft } from 'lucide-react'
import { 
  Button, 
  Avatar, 
  AvatarFallback, 
  AvatarImage,
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuLabel,
  Tooltip,
  TooltipTrigger
} from '@morningai/shared-ui'
import { LanguageSwitcher } from './LanguageSwitcher'
import { OwnerTooltipContent } from './OwnerTooltipContent'

/**
 * GlobalHeader - Single global header for Owner Console
 * 
 * Design: GitHub/Linear-style header with:
 * - Left: Sidebar toggle, Logo, Product name
 * - Center: Search box
 * - Right: Language, Notifications, Help, User menu
 * 
 * @param {Object} props
 * @param {Object} props.user - Current user object
 * @param {Function} props.onLogout - Logout handler
 * @param {boolean} props.collapsed - Sidebar collapsed state (desktop)
 * @param {Function} props.onToggleSidebar - Toggle sidebar handler
 * @param {boolean} props.isMobile - Whether in mobile viewport
 * @param {boolean} props.mobileOpen - Mobile drawer open state
 */
const GlobalHeader = ({ user, onLogout, collapsed, onToggleSidebar, isMobile, mobileOpen }) => {
  const { t } = useTranslation()
  const [searchQuery, setSearchQuery] = useState('')

  return (
    <header className="bg-white dark:bg-neutral-900 border-b border-neutral-200 dark:border-neutral-700 px-4 h-14 flex items-center justify-between flex-shrink-0 z-40">
      {/* Left Section: Toggle + Logo + Product Name */}
      <div className="flex items-center space-x-3">
        {/* Sidebar Toggle */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleSidebar}
              className="group h-9 w-9 rounded-lg p-2 text-neutral-500 hover:bg-primary-500/10 hover:text-neutral-900 dark:text-neutral-400 dark:hover:bg-primary-500/15 dark:hover:text-white transition-colors duration-150"
                            aria-label={isMobile ? (mobileOpen ? t('sidebar.collapse') : t('sidebar.expand')) : (collapsed ? t('sidebar.expand') : t('sidebar.collapse'))}
                            aria-expanded={isMobile ? mobileOpen : !collapsed}
            >
              <PanelLeft 
                className="w-5 h-5 opacity-60 group-hover:opacity-100 transition-all duration-150"
                strokeWidth={1.5}
              />
            </Button>
          </TooltipTrigger>
          <OwnerTooltipContent>
            {isMobile ? (mobileOpen ? t('sidebar.collapse') : t('sidebar.expand')) : (collapsed ? t('sidebar.expand') : t('sidebar.collapse'))}
          </OwnerTooltipContent>
        </Tooltip>

        {/* Logo + Product Name */}
        <Link 
          to="/dashboard" 
          className="flex items-center space-x-2 hover:opacity-80 transition-opacity"
        >
          <img 
            src="/assets/brand/icon-only/MorningAI_icon_1024.png" 
            alt="Morning AI" 
            className="w-8 h-8 rounded-lg"
          />
          <span className="text-base font-semibold text-neutral-900 dark:text-white hidden sm:inline">
            {t('app.tagline')}
          </span>
        </Link>
      </div>

      {/* Center Section: Search Box */}
      <div className="flex-1 max-w-md mx-4 hidden md:block">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-400" />
          <input
            type="text"
            placeholder={t('header.searchPlaceholder', 'Search...')}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-8 pr-4 py-2 w-full bg-neutral-100 dark:bg-neutral-800 border-0 rounded-lg text-sm text-neutral-700 dark:text-neutral-200 placeholder-neutral-400 dark:placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:bg-white dark:focus:bg-neutral-700 transition-colors"
          />
        </div>
      </div>

      {/* Right Section: Language, Notifications, Help, User */}
      <div className="flex items-center space-x-1">
        {/* Mobile Search Button */}
        <Button
          variant="ghost"
          size="sm"
          className="md:hidden p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:hover:text-white dark:hover:bg-neutral-800 rounded-lg"
          aria-label={t('header.search')}
        >
          <Search className="w-5 h-5" />
        </Button>

        {/* Help */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:hover:text-white dark:hover:bg-neutral-800 rounded-lg"
              aria-label={t('header.help')}
            >
              <HelpCircle className="w-5 h-5" />
            </Button>
          </TooltipTrigger>
          <OwnerTooltipContent>
            {t('header.help')}
          </OwnerTooltipContent>
        </Tooltip>

        {/* Notifications */}
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant="ghost"
              size="sm"
              className="p-2 text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:hover:text-white dark:hover:bg-neutral-800 rounded-lg relative"
              aria-label={t('header.notifications')}
            >
              <Bell className="w-5 h-5" />
            </Button>
          </TooltipTrigger>
          <OwnerTooltipContent>
            {t('header.notifications')}
          </OwnerTooltipContent>
        </Tooltip>

        {/* Language Switcher */}
        <LanguageSwitcher 
          variant="compact" 
          className="border-none bg-transparent shadow-none text-neutral-500 hover:text-neutral-700 hover:bg-neutral-100 dark:hover:text-white dark:hover:bg-neutral-800" 
        />

        {/* User Menu */}
        <div className="pl-2 ml-2 border-l border-neutral-200 dark:border-neutral-700">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button 
                className="flex items-center space-x-2 hover:opacity-80 transition-opacity cursor-pointer focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 rounded-lg p-1"
                aria-label={t('header.userMenu', 'User menu')}
              >
                <Avatar className="w-8 h-8">
                  <AvatarImage src={user?.avatar} alt={user?.name ? `${user.name}'s avatar` : 'User avatar'} />
                  <AvatarFallback className="bg-primary-500 text-white text-sm">
                    {user?.name?.charAt(0) || 'U'}
                  </AvatarFallback>
                </Avatar>
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 rounded-xl border-0 bg-white dark:bg-neutral-800 shadow-lg">
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium text-neutral-900 dark:text-white">{user?.name || t('header.defaultUser')}</p>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400">{user?.email || ''}</p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link to="/settings" className="cursor-pointer">
                  <Settings className="mr-2 h-4 w-4" />
                  {t('nav.settings')}
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem 
                onClick={onLogout}
                className="cursor-pointer text-error-600 focus:text-error-600 focus:bg-error-50"
              >
                <LogOut className="mr-2 h-4 w-4" />
                {t('nav.logout')}
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}

export default GlobalHeader
