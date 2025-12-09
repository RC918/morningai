import { useState, useEffect, useRef, createContext, useContext } from 'react'
import GlobalHeader from './GlobalHeader'
import Sidebar from './Sidebar'
import { Sheet, SheetContent } from '@morningai/shared-ui'

/**
 * Context for sidebar state management
 * Allows child components to access and control sidebar state
 */
const SidebarContext = createContext({
  collapsed: false,
  setCollapsed: () => {},
  isMobile: false,
  mobileOpen: false,
  setMobileOpen: () => {}
})

export const useSidebar = () => useContext(SidebarContext)

/**
 * OwnerConsoleLayout - Single-layer Header + Sidebar architecture
 * 
 * Design: GitHub/Linear-style layout with:
 * - Single global header at top (no second header bar)
 * - Collapsible sidebar on desktop
 * - Drawer-style sidebar on mobile
 * 
 * @param {Object} props
 * @param {Object} props.user - Current user object
 * @param {Function} props.onLogout - Logout handler
 * @param {React.ReactNode} props.children - Main content
 */
const OwnerConsoleLayout = ({ user, onLogout, children }) => {
  const [collapsed, setCollapsed] = useState(false)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [isMobile, setIsMobile] = useState(false)
  
  // Store desktop collapsed state to restore when returning from mobile
  const desktopCollapsedRef = useRef(false)

  // Handle responsive breakpoint detection
  useEffect(() => {
    const checkMobile = () => {
      const mobile = window.innerWidth < 768 // md breakpoint
      const wasMobile = isMobile
      
      setIsMobile(mobile)
      
      if (mobile && !wasMobile) {
        // Entering mobile: save desktop state and collapse
        desktopCollapsedRef.current = collapsed
        setCollapsed(true)
      } else if (!mobile && wasMobile) {
        // Returning to desktop: restore saved state
        setCollapsed(desktopCollapsedRef.current)
      }
    }

    checkMobile()
    window.addEventListener('resize', checkMobile)
    return () => window.removeEventListener('resize', checkMobile)
  }, [isMobile, collapsed])

  const handleToggleSidebar = () => {
    if (isMobile) {
      setMobileOpen(!mobileOpen)
    } else {
      setCollapsed(!collapsed)
    }
  }

  const contextValue = {
    collapsed,
    setCollapsed,
    isMobile,
    mobileOpen,
    setMobileOpen
  }

  return (
    <SidebarContext.Provider value={contextValue}>
      <div className="flex flex-col h-screen bg-neutral-100 dark:bg-neutral-950">
                {/* Single Global Header */}
                <GlobalHeader 
                  user={user} 
                  onLogout={onLogout}
                  collapsed={collapsed}
                  onToggleSidebar={handleToggleSidebar}
                  isMobile={isMobile}
                  mobileOpen={mobileOpen}
                />

        {/* Main Layout: Sidebar + Content */}
        <div className="flex flex-1 overflow-hidden">
          {/* Desktop Sidebar */}
          {!isMobile && (
            <Sidebar user={user} collapsed={collapsed} />
          )}

          {/* Mobile Sidebar (Drawer) */}
          {isMobile && (
            <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
              <SheetContent 
                side="left" 
                className="p-0 w-64 bg-white dark:bg-neutral-900"
              >
                <Sidebar user={user} collapsed={false} isMobileDrawer />
              </SheetContent>
            </Sheet>
          )}

          {/* Main Content Area */}
          <main 
            id="main-content" 
            className="flex-1 overflow-y-auto p-6" 
            role="main"
          >
            {children}
          </main>
        </div>
      </div>
    </SidebarContext.Provider>
  )
}

export default OwnerConsoleLayout
