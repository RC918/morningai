"use client";

import * as React from "react";
import { cn } from "../../utils";
import type { AdminUser } from "./admin-sidebar";

export interface AdminTopbarProps {
  user: AdminUser;
  title?: string;
  searchPlaceholder?: string;
  onSearch?: (query: string) => void;
  className?: string;
  children?: React.ReactNode;
}

function AdminTopbar({
  user,
  title = "Platform Overview",
  searchPlaceholder = "Search tenants, events, agents...",
  onSearch,
  className,
  children,
}: AdminTopbarProps) {
  const [searchQuery, setSearchQuery] = React.useState("");

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchQuery(value);
    onSearch?.(value);
  };

  return (
    <header
      className={cn(
        "h-14 flex items-center justify-between px-6 border-b border-neutral-200 bg-white dark:border-neutral-700 dark:bg-neutral-900",
        className
      )}
    >
      <div className="text-sm text-neutral-500 dark:text-neutral-400">
        {title}
      </div>
      <div className="flex items-center gap-4">
        <input
          type="text"
          placeholder={searchPlaceholder}
          aria-label={searchPlaceholder}
          value={searchQuery}
          onChange={handleSearchChange}
          className="h-9 w-64 px-3 rounded-full border border-neutral-200 bg-neutral-50 text-xs focus:outline-none focus:ring-2 focus:ring-primary-100 dark:border-neutral-700 dark:bg-neutral-800 dark:text-neutral-100"
        />
        {children}
        {user.avatar ? (
          <img
            src={user.avatar}
            alt={user.name}
            className="h-8 w-8 rounded-full object-cover"
          />
        ) : (
          <div
            aria-label={user.name}
            role="img"
            className="h-8 w-8 rounded-full bg-neutral-100 dark:bg-neutral-700 flex items-center justify-center text-xs font-medium text-neutral-600 dark:text-neutral-300"
          >
            {user.name.charAt(0).toUpperCase()}
          </div>
        )}
      </div>
    </header>
  );
}

AdminTopbar.displayName = "AdminTopbar";

export { AdminTopbar };
