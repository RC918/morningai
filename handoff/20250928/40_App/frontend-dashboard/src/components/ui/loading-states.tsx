import React from 'react';
import { cn } from '@/lib/utils';

export function Spinner({ className, size = 'md' }) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
  };

  return (
    <div
      className={cn(
        'spinner border-2 border-gray-200 border-t-primary rounded-full',
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

export function Skeleton({ className, variant = 'default' }) {
  const variants = {
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
        'skeleton rounded-md bg-gray-200 dark:bg-gray-700',
        variants[variant],
        className
      )}
      aria-hidden="true"
    />
  );
}

export function LoadingDots({ className }) {
  return (
    <div className={cn('flex space-x-1', className)} role="status" aria-label="Loading">
      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
      <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
      <span className="sr-only">Loading...</span>
    </div>
  );
}

export function ProgressBar({ value = 0, className, showLabel = false }) {
  return (
    <div className={cn('w-full', className)}>
      <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
        <div
          className="progress-fill bg-primary h-full rounded-full transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, value))}%` }}
          role="progressbar"
          aria-valuenow={value}
          aria-valuemin="0"
          aria-valuemax="100"
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

export function PulseLoader({ className }) {
  return (
    <div className={cn('flex space-x-2', className)} role="status" aria-label="Loading">
      <div className="w-3 h-3 bg-primary rounded-full animate-pulse" />
      <div className="w-3 h-3 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
      <div className="w-3 h-3 bg-primary rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
      <span className="sr-only">Loading...</span>
    </div>
  );
}
