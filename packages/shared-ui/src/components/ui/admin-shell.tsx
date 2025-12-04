"use client";

import * as React from "react";
import { cn } from "../../utils";
import { AdminSidebar, type AdminNavItem, type AdminUser } from "./admin-sidebar";
import { AdminTopbar } from "./admin-topbar";

export interface AdminShellProps {
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
  topbarClassName?: string;
  mainClassName?: string;
  children: React.ReactNode;
  renderLink?: (props: {
    href: string;
    className: string;
    children: React.ReactNode;
  }) => React.ReactNode;
  topbarChildren?: React.ReactNode;
  /** Right panel content (e.g., activity feed, notifications) for three-column layout */
  rightPanel?: React.ReactNode;
  /** Custom class name for the right panel container */
  rightPanelClassName?: string;
}

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
  topbarClassName,
  mainClassName,
  children,
  renderLink,
  topbarChildren,
  rightPanel,
  rightPanelClassName,
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
                className={cn(
                  "w-80 border-l border-neutral-200 bg-white overflow-auto dark:border-neutral-700 dark:bg-neutral-900",
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
