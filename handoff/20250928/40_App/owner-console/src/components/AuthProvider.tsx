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
  LoginResponse,
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
  login: (credentials: LoginCredentials) => Promise<LoginResponse>;
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

  const login = async (credentials: LoginCredentials): Promise<LoginResponse> => {
    console.info('[AuthProvider] login() called', { email: credentials.email });
    try {
      const response = await authLogin(credentials);
      console.info('[AuthProvider] authLogin response', { requires_2fa: response.requires_2fa, has_user: !!response.user });
      
      if (response.requires_2fa) {
        console.info('[AuthProvider] 2FA required, returning early');
        return response;
      }
      
      console.info('[AuthProvider] Setting user and authenticated state');
      setUser(response.user);
      setIsAuthenticated(true);
      return response;
    } catch (error) {
      console.error('[AuthProvider] login error', error);
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
