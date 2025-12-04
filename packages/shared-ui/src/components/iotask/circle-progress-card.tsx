import * as React from "react";

import { cn } from "../../utils";

interface CircleProgressCardProps {
  title: string;
  value: number;
  max?: number;
  label?: string;
  subtitle?: string;
  size?: "sm" | "md" | "lg";
  color?: "primary" | "success" | "warning" | "error" | "accent";
  className?: string;
}

const sizeConfig = {
  sm: { size: 80, strokeWidth: 6, fontSize: "text-lg" },
  md: { size: 120, strokeWidth: 8, fontSize: "text-2xl" },
  lg: { size: 160, strokeWidth: 10, fontSize: "text-3xl" },
};

const colorStyles = {
  primary: "stroke-[var(--primary-500)]",
  success: "stroke-[var(--success-500)]",
  warning: "stroke-[var(--warning-500)]",
  error: "stroke-[var(--error-500)]",
  accent: "stroke-[var(--color-accent-500)]",
};

function CircleProgressCard({
  title,
  value,
  max = 100,
  label,
  subtitle,
  size = "md",
  color = "primary",
  className,
}: CircleProgressCardProps) {
  const config = sizeConfig[size];
  const radius = (config.size - config.strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div
      className={cn(
        "rounded-xl border border-[var(--border)] bg-[var(--surface)] p-5 shadow-card",
        className
      )}
    >
      <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-4">
        {title}
      </h3>
      <div className="flex flex-col items-center">
        <div className="relative" style={{ width: config.size, height: config.size }}>
          <svg
            className="transform -rotate-90"
            width={config.size}
            height={config.size}
            aria-hidden="true"
          >
            <circle
              cx={config.size / 2}
              cy={config.size / 2}
              r={radius}
              fill="none"
              stroke="var(--neutral-200)"
              strokeWidth={config.strokeWidth}
            />
            <circle
              cx={config.size / 2}
              cy={config.size / 2}
              r={radius}
              fill="none"
              className={cn("transition-all duration-500", colorStyles[color])}
              strokeWidth={config.strokeWidth}
              strokeLinecap="round"
              strokeDasharray={circumference}
              strokeDashoffset={strokeDashoffset}
            />
          </svg>
          <div className="absolute inset-0 flex flex-col items-center justify-center">
            <span className={cn("font-bold text-[var(--text-primary)]", config.fontSize)}>
              {label || `${Math.round(percentage)}%`}
            </span>
          </div>
        </div>
        {subtitle && (
          <p className="mt-3 text-xs text-[var(--text-secondary)] text-center">
            {subtitle}
          </p>
        )}
      </div>
    </div>
  );
}

export { CircleProgressCard };
export type { CircleProgressCardProps };
