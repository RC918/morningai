/**
 * Auth Provider Component
 * Issue #767 - API Connection
 * Feature Flag: OWNER_CONSOLE_API
 * 
 * Provides authentication context and UI integration
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  User,
  LoginCredentials,
  login as authLogin,
  logout as authLogout,
  getCurrentUser,
  isAuthenticated as checkAuth,
  initAuth,
  cleanupAuth,
} from '../lib/auth';

interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginCredentials) => Promise<any>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initialize = async () => {
      if (typeof window !== 'undefined' &&
          import.meta.env.VITE_PREVIEW_PUBLIC_METRICS === 'true' &&
          window.location.pathname.startsWith('/ux-metrics')) {
        setIsAuthenticated(true);
        setUser({
          id: 'preview-user',
          email: 'preview@morningai.com',
          role: 'owner',
          tenantId: 'preview-tenant',
          name: 'Preview User',
        } as User);
        setIsLoading(false);
        return;
      }

      const { isAuthenticated: authenticated, user: storedUser } = await initAuth();
      setIsAuthenticated(authenticated);
      setUser(storedUser);
      setIsLoading(false);
    };
    
    initialize();

    return () => {
      cleanupAuth();
    };
  }, []);

  const login = async (credentials: LoginCredentials) => {
    try {
      const response = await authLogin(credentials);
      
      if (response.next_step === 'session' || !response.next_step) {
        setUser(response.user ?? null);
        setIsAuthenticated(true);
      }
      
      return response;
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  };

  const logout = async () => {
    try {
      await authLogout();
    } finally {
      setUser(null);
      setIsAuthenticated(false);
    }
  };

  const refreshUser = async () => {
    try {
      const currentUser = await getCurrentUser();
      setUser(currentUser);
      setIsAuthenticated(true);
    } catch (error) {
      setUser(null);
      setIsAuthenticated(false);
      throw error;
    }
  };

  const value: AuthContextType = {
    user,
    isAuthenticated,
    isLoading,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthProvider;
