import type * as React from 'react';

export interface User {
  name?: string;
  email?: string;
  role?: string;
  avatar?: string;
}

export interface SidebarProps {
  user?: User;
  collapsed?: boolean;
  isMobileDrawer?: boolean;
}

declare const Sidebar: React.FC<SidebarProps>;
export default Sidebar;
