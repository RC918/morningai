import React, { createContext, useContext, useState, useEffect } from 'react';

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

      const token = localStorage.getItem('auth_token');
      
      if (!token) {
        setLoading(false);
        return;
      }

      const response = await fetch(`${import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'}/api/tenant/me`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        if (response.status === 404) {
          setError('Tenant information not found. Please contact support.');
        } else {
          throw new Error('Failed to fetch tenant information');
        }
        setLoading(false);
        return;
      }

      const data = await response.json();
      
      setTenant({
        id: data.tenant_id,
        name: data.tenant_name,
        createdAt: data.created_at
      });

      setLoading(false);
    } catch (err) {
      console.error('Error fetching tenant info:', err);
      const errorMessage = err instanceof Error ? err.message : 'Failed to load tenant information';
      setError(errorMessage);
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
