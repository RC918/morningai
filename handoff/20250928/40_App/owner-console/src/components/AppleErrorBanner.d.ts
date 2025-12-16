import type * as React from 'react';

export interface AppleErrorBannerProps {
  title: string;
  message: string;
  onRetry?: () => void;
  retryLabel?: string;
  icon?: React.ReactNode;
  testId?: string;
  retryTestId?: string;
}

export const AppleErrorBanner: React.FC<AppleErrorBannerProps>;
