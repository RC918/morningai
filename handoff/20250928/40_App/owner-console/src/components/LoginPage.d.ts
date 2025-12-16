import type * as React from 'react';

export interface LoginCredentials {
  email: string;
  password: string;
}

export interface LoginResponse {
  next_step?: 'session' | 'enroll_2fa' | 'challenge_2fa';
  requires_2fa?: boolean;
  token?: string;
  tmp_login_token?: string;
  user?: unknown;
  tokens?: {
    accessToken?: string;
    expiresAt?: string;
  };
}

export interface LoginPageProps {
  onLogin: (credentials: LoginCredentials) => Promise<LoginResponse | void>;
  onRefreshUser?: () => Promise<void>;
  redirectPath?: string;
}

declare const LoginPage: React.FC<LoginPageProps>;
export default LoginPage;
