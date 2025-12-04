"use client";

import * as React from "react";
import { cn } from "../../utils";

export interface PageScaffoldProps {
  /** Page title - rendered as h1 */
  title: React.ReactNode;
  /** Optional subtitle below the title */
  subtitle?: React.ReactNode;
  /** Optional icon displayed before the title */
  titleIcon?: React.ReactNode;
  /** Optional action buttons/elements aligned to the right of the header */
  actions?: React.ReactNode;
  /** Optional banner/alert content displayed below the header (e.g., error banners, warnings) */
  banner?: React.ReactNode;
  /** Optional KPI row content (e.g., StatCard components) */
  kpis?: React.ReactNode;
  /** Main page content */
  children: React.ReactNode;
  /** Custom class name for the root container */
  className?: string;
  /** Custom class name for the header section */
  headerClassName?: string;
  /** Custom class name for the KPI section */
  kpiClassName?: string;
  /** Custom class name for the content/body section */
  bodyClassName?: string;
}

/**
 * PageScaffold - Standardized page layout component
 * 
 * Enforces consistent page structure across all applications:
 * - Header with title, subtitle, icon, and actions
 * - Optional banner slot for alerts/errors
 * - Optional KPI row for metrics
 * - Content area for main page content
 * 
 * @example
 * ```tsx
 * <PageScaffold
 *   title={t("Tenant Management")}
 *   subtitle={t("Manage your tenants")}
 *   titleIcon={<Users />}
 *   actions={<Button>Add Tenant</Button>}
 *   banner={error && <AppleErrorBanner error={error} />}
 *   kpis={<TenantsKpiRow data={kpi} />}
 * >
 *   <TenantSection tenants={list} />
 * </PageScaffold>
 * ```
 */
function PageScaffold({
  title,
  subtitle,
  titleIcon,
  actions,
  banner,
  kpis,
  children,
  className,
  headerClassName,
  kpiClassName,
  bodyClassName,
}: PageScaffoldProps) {
  return (
    <div className={cn("space-y-8", className)}>
      {/* Header Section */}
      <header
        className={cn(
          "flex items-start justify-between gap-4",
          headerClassName
        )}
      >
        <div className="flex flex-col">
          <h1 className="flex items-center gap-2 text-xl font-semibold text-[var(--text-primary)]">
            {titleIcon && (
              <span className="flex-shrink-0 text-[var(--text-secondary)]">
                {titleIcon}
              </span>
            )}
            {title}
          </h1>
          {subtitle && (
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              {subtitle}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {actions}
          </div>
        )}
      </header>

      {/* Banner Section (errors, warnings, info) */}
      {banner && <div className="page-scaffold-banner">{banner}</div>}

      {/* KPI Row Section */}
      {kpis && (
        <section
          aria-label="Key metrics"
          className={cn(
            "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5",
            kpiClassName
          )}
        >
          {kpis}
        </section>
      )}

      {/* Main Content Section */}
      <div className={cn("space-y-6", bodyClassName)}>
        {children}
      </div>
    </div>
  );
}

PageScaffold.displayName = "PageScaffold";

export { PageScaffold };
