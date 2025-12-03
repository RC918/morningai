"use client";

import * as React from "react";
import { cn } from "../../utils";

export interface AdminNavItem {
  label: string;
  href: string;
  icon?: React.ComponentType<{ className?: string }>;
  active?: boolean;
}

export interface AdminUser {
  name: string;
  role: string;
  avatar?: string;
}

export interface AdminSidebarProps {
  navItems: AdminNavItem[];
  user: AdminUser;
  logo?: React.ReactNode;
  appName?: string;
  appSubtitle?: string;
  className?: string;
  renderLink?: (props: {
    href: string;
    className: string;
    children: React.ReactNode;
  }) => React.ReactNode;
}

function AdminSidebar({
  navItems,
  user,
  logo,
  appName = "MorningAI",
  appSubtitle = "Owner Console",
  className,
  renderLink,
}: AdminSidebarProps) {
  const defaultRenderLink = ({
    href,
    className: linkClassName,
    children,
  }: {
    href: string;
    className: string;
    children: React.ReactNode;
  }) => (
    <a href={href} className={linkClassName}>
      {children}
    </a>
  );

  const LinkComponent = renderLink || defaultRenderLink;

  return (
    <aside
      className={cn(
        "w-64 border-r border-neutral-200 bg-white shadow-sm flex flex-col dark:border-neutral-700 dark:bg-neutral-900",
        className
      )}
    >
      <div className="px-6 py-5 border-b border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center gap-3">
          {logo || (
            <div className="h-9 w-9 rounded-xl bg-primary-500 text-white flex items-center justify-center font-semibold">
              M
            </div>
          )}
          <div>
            <div className="text-sm font-semibold text-neutral-900 dark:text-neutral-100">
              {appName}
            </div>
            <div className="text-xs text-neutral-500 dark:text-neutral-400">
              {appSubtitle}
            </div>
          </div>
        </div>
      </div>
      <nav className="px-3 py-4 space-y-1 flex-1">
        {navItems.map((item) => (
          <LinkComponent
            key={item.href}
            href={item.href}
            className={cn(
              "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
              item.active
                ? "bg-primary-50 text-primary-700 font-medium dark:bg-primary-900/20 dark:text-primary-400"
                : "text-neutral-500 hover:bg-neutral-50 dark:text-neutral-400 dark:hover:bg-neutral-800"
            )}
          >
            {item.icon && <item.icon className="h-5 w-5" />}
            {item.label}
          </LinkComponent>
        ))}
      </nav>
      <div className="px-4 py-4 border-t border-neutral-200 dark:border-neutral-700">
        <div className="flex items-center gap-3">
          {user.avatar ? (
            <img
              src={user.avatar}
              alt=""
              aria-hidden="true"
              className="h-8 w-8 rounded-full object-cover"
            />
          ) : (
            <div
              aria-hidden="true"
              className="h-8 w-8 rounded-full bg-neutral-100 dark:bg-neutral-700 flex items-center justify-center text-xs font-medium text-neutral-600 dark:text-neutral-300"
            >
              {user.name.charAt(0).toUpperCase()}
            </div>
          )}
          <div className="flex-1 min-w-0">
            <div className="text-sm font-medium text-neutral-900 dark:text-neutral-100 truncate">
              {user.name}
            </div>
            <div className="text-xs text-neutral-500 dark:text-neutral-400 truncate">
              {user.role}
            </div>
          </div>
        </div>
      </div>
    </aside>
  );
}

AdminSidebar.displayName = "AdminSidebar";

export { AdminSidebar };
