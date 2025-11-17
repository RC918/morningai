import React from 'react';
import { cn } from '@/lib/utils';

type SpinnerSize = 'sm' | 'md' | 'lg'

interface SpinnerProps {
  className?: string
  size?: SpinnerSize
}

export function Spinner({ className, size = 'md' }: SpinnerProps): React.ReactElement {
  const sizeClasses: Record<SpinnerSize, string> = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div
      className={cn(
        'spinner border-2 border-neutral-200 border-t-primary rounded-full',
        sizeClasses[size],
        className
      )}
      role="status"
      aria-label="Loading"
    >
      <span className="sr-only">Loading...</span>
    </div>
  );
}

type SkeletonVariant = 'default' | 'text' | 'title' | 'avatar' | 'button' | 'card'

interface SkeletonProps {
  className?: string
  variant?: SkeletonVariant
}

export function Skeleton({ className, variant = 'default' }: SkeletonProps): React.ReactElement {
  const variants: Record<SkeletonVariant, string> = {
    default: 'h-4 w-full',
    text: 'h-4 w-3/4',
    title: 'h-6 w-1/2',
    avatar: 'h-12 w-12 rounded-full',
    button: 'h-10 w-24',
    card: 'h-32 w-full',
  };

  return (
    <div
      className={cn(
        'skeleton rounded-md bg-neutral-200 dark:bg-neutral-700',
        variants[variant],
        className
      )}
      aria-hidden="true"
    />
  );
}

interface LoadingDotsProps {
  className?: string
}

export function LoadingDots({ className }: LoadingDotsProps): React.ReactElement {
  return (
    <div className={cn('flex space-x-1', className)} role="status" aria-label="Loading">
      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      <span className="sr-only">Loading...</span>
    </div>
  );
}

interface ProgressBarProps {
  value?: number
  className?: string
  showLabel?: boolean
}

export function ProgressBar({ value = 0, className, showLabel = false }: ProgressBarProps): React.ReactElement {
  return (
    <div className={cn('w-full', className)}>
      <div className="w-full bg-neutral-200 dark:bg-neutral-700 rounded-full h-2 overflow-hidden">
        <div
          className="progress-fill bg-primary h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin={0}
          aria-valuemax={100}
        />
      </div>
      {showLabel && (
        <div className="text-sm text-muted-foreground mt-1 text-right">
          {Math.round(value)}%
        </div>
      )}
    </div>
  );
}

interface PulseLoaderProps {
  className?: string
}

export function PulseLoader({ className }: PulseLoaderProps): React.ReactElement {
  return (
    <div className={cn('flex space-x-2', className)} role="status" aria-label="Loading">
      <div className="w-3 h-3 bg-primary rounded-full animate-pulse" />
      <div className="w-3 h-3 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
      <div className="w-3 h-3 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
      <span className="sr-only">Loading...</span>
    </div>
  );
}
