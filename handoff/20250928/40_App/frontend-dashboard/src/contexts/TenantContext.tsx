import React, { createContext, useContext, useState, useEffect } from 'react';
import { apiClient } from '../lib/api-client';

interface Tenant {
  id: string;
  name: string;
  createdAt: string;
}

interface TenantContextValue {
  tenant: Tenant | null;
  loading: boolean;
  error: string | null;
  refreshTenant: () => void;
}

const TenantContext = createContext<TenantContextValue | null>(null);

export const TenantProvider = ({ children }: { children: React.ReactNode }) => {
  const [tenant, setTenant] = useState<Tenant | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTenantInfo = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiClient<{
        tenant_id: string;
        tenant_name: string;
        created_at: string;
      }>('/api/tenant/me', {
        method: 'GET'
      });
      
      setTenant({
        id: data.tenant_id,
        name: data.tenant_name,
        createdAt: data.created_at
      });

      setLoading(false);
    } catch (err) {
      console.error('Error fetching tenant info:', err);
      
      if (err && typeof err === 'object' && 'status' in err && err.status === 404) {
        setError('Tenant information not found. Please contact support.');
      } else {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load tenant information';
        setError(errorMessage);
      }
      
      setLoading(false);
    }
  };

  const refreshTenant = () => {
    fetchTenantInfo();
  };

  useEffect(() => {
    fetchTenantInfo();
  }, []);

  const value = {
    tenant,
    loading,
    error,
    refreshTenant
  };

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  );
};

export const useTenant = () => {
  const context = useContext(TenantContext);
  
  if (!context) {
    throw new Error('useTenant must be used within a TenantProvider');
  }
  
  return context;
};
