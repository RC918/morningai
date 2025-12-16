import type * as React from 'react';

export interface User {
  name?: string;
  email?: string;
  role?: string;
  avatar?: string;
}

export interface DashboardHeaderProps {
  user?: User;
  title?: string;
  subtitle?: string;
  notificationCount?: number;
  onLogout?: () => void;
}

declare const DashboardHeader: React.FC<DashboardHeaderProps>;
export default DashboardHeader;
