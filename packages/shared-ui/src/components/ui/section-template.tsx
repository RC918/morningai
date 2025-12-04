"use client";

import * as React from "react";
import { cn } from "../../utils";
import { SectionCard } from "../dashboard/section-card";

export type SectionTemplateVariant = "plain" | "card";

export interface SectionTemplateProps {
  /** Section title - rendered as h2 for plain variant, passed to SectionCard for card variant */
  title: string;
  /** Optional description below the title */
  description?: React.ReactNode;
  /** Optional action buttons/elements aligned to the right of the header */
  actions?: React.ReactNode;
  /** Section content */
  children: React.ReactNode;
  /** 
   * Section variant:
   * - "plain": Renders a semantic section with h2 title (default)
   * - "card": Delegates to SectionCard component for card-based sections
   */
  variant?: SectionTemplateVariant;
  /** Custom class name for the section container */
  className?: string;
  /** Custom class name for the header section (plain variant only) */
  headerClassName?: string;
  /** Custom class name for the body/content section. Note: for the 'card' variant, this class is applied to the entire SectionCard component, not just the content area. */
  bodyClassName?: string;
}

/**
 * SectionTemplate - Standardized section layout component
 * 
 * Provides consistent section structure within pages. Works inside PageScaffold
 * to create a hierarchical page layout.
 * 
 * Use `variant="plain"` (default) for semantic sections with custom styling.
 * Use `variant="card"` for card-based sections that delegate to SectionCard.
 * 
 * @example
 * ```tsx
 * // Plain section (default)
 * <SectionTemplate
 *   title={t("Active Tenants")}
 *   description={t("Manage your active tenant accounts")}
 *   actions={<Button size="sm">View All</Button>}
 * >
 *   <TenantList tenants={activeTenants} />
 * </SectionTemplate>
 * 
 * // Card-based section
 * <SectionTemplate
 *   variant="card"
 *   title={t("System Status")}
 *   description={t("Current system health metrics")}
 *   actions={<Button size="sm">Refresh</Button>}
 * >
 *   <SystemStatusList items={statusItems} />
 * </SectionTemplate>
 * ```
 */
function SectionTemplate({
  title,
  description,
  actions,
  children,
  variant = "plain",
  className,
  headerClassName,
  bodyClassName,
}: SectionTemplateProps) {
  // Card variant: delegate to SectionCard component
  if (variant === "card") {
    // Map description to subtitle (only if it's a string, as SectionCard expects string)
    if (process.env.NODE_ENV !== 'production' && description && typeof description !== 'string') {
      console.warn('SectionTemplate: The "description" prop must be a string when using the "card" variant. The provided ReactNode will not be rendered.');
    }
    const subtitle = typeof description === "string" ? description : undefined;
    
    return (
      <section className={className}>
        <SectionCard
          title={title}
          subtitle={subtitle}
          action={actions}
          className={bodyClassName}
        >
          {children}
        </SectionCard>
      </section>
    );
  }

  // Plain variant: render semantic section with h2 title
  return (
    <section className={className}>
      <div
        className={cn(
          "flex items-start justify-between gap-4",
          headerClassName
        )}
      >
        <div>
          <h2 className="text-base font-semibold text-[var(--text-primary)]">
            {title}
          </h2>
          {description && (
            <p className="mt-1 text-sm text-[var(--text-secondary)]">
              {description}
            </p>
          )}
        </div>
        {actions && (
          <div className="flex items-center gap-2 flex-shrink-0">
            {actions}
          </div>
        )}
      </div>

      <div className={cn("mt-4 space-y-4", bodyClassName)}>
        {children}
      </div>
    </section>
  );
}

SectionTemplate.displayName = "SectionTemplate";

export { SectionTemplate };
