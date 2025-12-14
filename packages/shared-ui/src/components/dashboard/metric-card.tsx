import * as React from "react";
import { TrendingUp, TrendingDown, Minus } from "lucide-react";

import { cn } from "../../utils";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Progress } from "../ui/progress";

type MetricCardVariant = "default" | "blue" | "green" | "yellow" | "red" | "purple";

const variantIconColors: Record<MetricCardVariant, string> = {
  default: "text-[var(--neutral-600)]",
  blue: "text-[var(--primary-600)]",
  green: "text-[var(--success-600)]",
  yellow: "text-[var(--warning-600)]",
  red: "text-[var(--error-600)]",
  purple: "text-[var(--color-accent-600)]",
};

const trendColors = {
  up: "text-[var(--success-600)]",
  down: "text-[var(--error-600)]",
  stable: "text-[var(--neutral-500)]",
};

const defaultTrendLabels = {
  up: "Increasing",
  down: "Decreasing",
  stable: "Stable",
};

const defaultTrendAriaLabels = {
  up: "Trending up",
  down: "Trending down",
  stable: "Stable",
};

interface TrendLabels {
  up?: string;
  down?: string;
  stable?: string;
}

interface MetricCardProps {
  /** Card title/label */
  title: string;
  /** Metric value to display */
  value: string | number;
  /** Unit of measurement (e.g., "%", "req/min", "ms") */
  unit?: string;
  /** Icon element to display in the header */
  icon?: React.ReactNode;
  /** Trend direction indicator */
  trend?: "up" | "down" | "stable";
  /** Custom trend labels for i18n (e.g., { up: "上升中", down: "下降中", stable: "穩定" }) */
  trendLabels?: TrendLabels;
  /** Custom trend aria labels for i18n (e.g., { up: "趨勢上升", down: "趨勢下降", stable: "穩定" }) */
  trendAriaLabels?: TrendLabels;
  /** Description text below the value */
  description?: string;
  /** Progress value (0-100) for optional progress bar */
  progress?: number;
  /** Color variant for the icon */
  variant?: MetricCardVariant;
  /** Additional className for the card */
  className?: string;
}

function MetricCard({
  title,
  value,
  unit,
  icon,
  trend,
  trendLabels,
  trendAriaLabels,
  description,
  progress,
  variant = "default",
  className,
}: MetricCardProps) {
  const trendData = React.useMemo(() => {
    if (!trend) return null;
    
    const iconClass = cn("size-4", trendColors[trend]);
    const label = trendLabels?.[trend] ?? defaultTrendLabels[trend];
    const ariaLabel = trendAriaLabels?.[trend] ?? defaultTrendAriaLabels[trend];
    
    const TrendIcon = trend === "up" ? TrendingUp : trend === "down" ? TrendingDown : Minus;
    
    return {
      icon: <TrendIcon className={iconClass} aria-label={ariaLabel} />,
      label,
      colorClass: trendColors[trend],
    };
  }, [trend, trendLabels, trendAriaLabels]);

  const formattedValue = React.useMemo(() => 
    typeof value === "number" 
      ? Number.isInteger(value) ? value.toString() : value.toFixed(2)
      : value,
    [value]
  );

  return (
    <Card className={cn("shadow-card", className)}>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium text-[var(--text-secondary)]">
          {title}
        </CardTitle>
        {icon && (
          <div className="shrink-0">
            {React.isValidElement(icon)
              ? React.cloneElement(icon as React.ReactElement<{ className?: string }>, {
                  className: cn("size-5", variantIconColors[variant]),
                })
              : icon}
          </div>
        )}
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold text-[var(--text-primary)]">
          {formattedValue}
          {unit && <span className="ml-1 text-lg font-normal text-[var(--text-secondary)]">{unit}</span>}
        </div>
        
        {description && (
          <p className="mt-1 text-xs text-[var(--text-secondary)]">
            {description}
          </p>
        )}
        
        {trendData && (
          <div className="mt-2 flex items-center gap-1">
            {trendData.icon}
            <span className={cn("text-xs", trendData.colorClass)}>
              {trendData.label}
            </span>
          </div>
        )}
        
        {typeof progress === "number" && (
          <div className="mt-3" aria-hidden="true">
            <Progress value={progress} className="h-1.5" />
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export { MetricCard };
export type { MetricCardProps, MetricCardVariant, TrendLabels };
