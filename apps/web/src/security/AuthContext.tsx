/**
 * Authentication Context for Kearney Data Platform
 *
 * Manages:
 * - API key and OIDC token storage
 * - User roles and tenant context
 * - Authentication state persistence (localStorage)
 * - Login/logout flows
 */

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface AuthState {
  token: string | null;
  provider: 'apikey' | 'oidc' | null;
  roles: string[];
  tenant: string | null;
  userId: string | null;
}

interface AuthContextType extends AuthState {
  loginWithApiKey: (apiKey: string, tenant?: string) => Promise<void>;
  loginWithOIDC: (oidcToken: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
  isAdmin: boolean;
  isEditor: boolean;
  isViewer: boolean;
  canEdit: boolean;
  canManageSecurity: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'kearney_auth';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [authState, setAuthState] = useState<AuthState>({
    token: null,
    provider: null,
    roles: [],
    tenant: null,
    userId: null,
  });

  // Load auth state from localStorage on mount
  useEffect(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    if (stored) {
      try {
        const parsed = JSON.parse(stored);
        setAuthState(parsed);
      } catch (e) {
        console.error('Failed to parse stored auth state:', e);
        localStorage.removeItem(STORAGE_KEY);
      }
    }
  }, []);

  // Persist auth state to localStorage
  useEffect(() => {
    if (authState.token) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(authState));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [authState]);

  const loginWithApiKey = async (apiKey: string, tenant?: string) => {
    try {
      // Verify API key by calling a protected endpoint
      const response = await fetch('/api/verify', {
        method: 'GET',
        headers: {
          'X-API-Key': apiKey,
          ...(tenant && { 'X-Tenant': tenant }),
        },
      });

      if (!response.ok) {
        throw new Error('Invalid API key');
      }

      const data = await response.json();

      setAuthState({
        token: apiKey,
        provider: 'apikey',
        roles: data.roles || [],
        tenant: tenant || data.tenant || null,
        userId: data.user_id || 'api-user',
      });
    } catch (error) {
      console.error('API key login failed:', error);
      throw error;
    }
  };

  const loginWithOIDC = async (oidcToken: string) => {
    try {
      // Verify OIDC token
      const response = await fetch('/api/verify', {
        method: 'GET',
        headers: {
          Authorization: `Bearer ${oidcToken}`,
        },
      });

      if (!response.ok) {
        throw new Error('Invalid OIDC token');
      }

      const data = await response.json();

      setAuthState({
        token: oidcToken,
        provider: 'oidc',
        roles: data.roles || [],
        tenant: data.tenant || null,
        userId: data.user_id || data.sub || 'oidc-user',
      });
    } catch (error) {
      console.error('OIDC login failed:', error);
      throw error;
    }
  };

  const logout = () => {
    setAuthState({
      token: null,
      provider: null,
      roles: [],
      tenant: null,
      userId: null,
    });
  };

  // Computed properties
  const isAuthenticated = authState.token !== null;
  const isAdmin = authState.roles.includes('admin');
  const isEditor = authState.roles.includes('editor') || isAdmin;
  const isViewer = authState.roles.includes('viewer') || isEditor;
  const canEdit = isEditor;
  const canManageSecurity = isAdmin;

  const value: AuthContextType = {
    ...authState,
    loginWithApiKey,
    loginWithOIDC,
    logout,
    isAuthenticated,
    isAdmin,
    isEditor,
    isViewer,
    canEdit,
    canManageSecurity,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

export default AuthContext;
