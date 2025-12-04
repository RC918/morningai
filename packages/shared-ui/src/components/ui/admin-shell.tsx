"use client";

import * as React from "react";
import { cn } from "../../utils";
import { AdminSidebar, type AdminNavItem, type AdminUser } from "./admin-sidebar";
import { AdminTopbar } from "./admin-topbar";

interface AdminShellPropsBase {
  navItems: AdminNavItem[];
  user: AdminUser;
  logo?: React.ReactNode;
  appName?: string;
  appSubtitle?: string;
  topbarTitle?: string;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  className?: string;
  sidebarClassName?: string;
  /** Accessible label for the sidebar (defaults to "Primary navigation") */
  sidebarAriaLabel?: string;
  topbarClassName?: string;
  mainClassName?: string;
  children: React.ReactNode;
  renderLink?: (props: {
    href: string;
    className: string;
    children: React.ReactNode;
  }) => React.ReactNode;
  topbarChildren?: React.ReactNode;
}

interface AdminShellPropsWithoutRightPanel extends AdminShellPropsBase {
  /** Right panel content (e.g., activity feed, notifications) for three-column layout */
  rightPanel?: undefined;
  /** Custom class name for the right panel container */
  rightPanelClassName?: undefined;
  /** Accessible label for the right panel aside element */
  rightPanelAriaLabel?: undefined;
}

interface AdminShellPropsWithRightPanel extends AdminShellPropsBase {
  /** Right panel content (e.g., activity feed, notifications) for three-column layout */
  rightPanel: React.ReactNode;
  /** Custom class name for the right panel container */
  rightPanelClassName?: string;
  /** Accessible label for the right panel aside element (required for A11y) */
  rightPanelAriaLabel: string;
}

export type AdminShellProps = AdminShellPropsWithoutRightPanel | AdminShellPropsWithRightPanel;

function AdminShell({
  navItems,
  user,
  logo,
  appName,
  appSubtitle,
  topbarTitle,
  searchPlaceholder,
  onSearch,
  className,
  sidebarClassName,
  sidebarAriaLabel,
  topbarClassName,
  mainClassName,
  children,
  renderLink,
  topbarChildren,
  rightPanel,
  rightPanelClassName,
  rightPanelAriaLabel,
}: AdminShellProps) {
  return (
    <div
      className={cn(
        "min-h-screen bg-neutral-50 text-neutral-900 dark:bg-neutral-950 dark:text-neutral-100",
        className
      )}
    >
      <div className="flex h-screen">
        <AdminSidebar
          navItems={navItems}
          user={user}
          logo={logo}
          appName={appName}
          appSubtitle={appSubtitle}
          className={sidebarClassName}
          renderLink={renderLink}
          ariaLabel={sidebarAriaLabel}
        />
        <div className="flex-1 flex flex-col overflow-hidden">
          <AdminTopbar
            user={user}
            title={topbarTitle}
            searchPlaceholder={searchPlaceholder}
            onSearch={onSearch}
            className={topbarClassName}
          >
            {topbarChildren}
          </AdminTopbar>
          <div className="flex-1 flex overflow-hidden">
            <main className={cn("flex-1 overflow-auto p-6", mainClassName)}>
              {children}
            </main>
            {rightPanel && (
              <aside
                aria-label={rightPanelAriaLabel}
                className={cn(
                  "hidden lg:block w-80 border-l border-neutral-200 bg-white overflow-auto dark:border-neutral-700 dark:bg-neutral-900",
                  rightPanelClassName
                )}
              >
                {rightPanel}
              </aside>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

AdminShell.displayName = "AdminShell";

export { AdminShell };
export type { AdminNavItem, AdminUser };
