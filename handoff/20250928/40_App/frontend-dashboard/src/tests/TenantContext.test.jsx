/**
 * Unit tests for TenantContext
 * Tests tenant state management, loading states, and error handling
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import { TenantProvider, useTenant } from '../contexts/TenantContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

describe('TenantContext', () => {
  let originalFetch;
  
  beforeEach(() => {
    originalFetch = global.fetch;
    localStorage.clear();
  });
  
  afterEach(() => {
    global.fetch = originalFetch;
    vi.clearAllMocks();
  });

  const TestConsumer = () => {
    const { tenant, loading, error } = useTenant();
    
    if (loading) return <div>Loading...</div>;
    if (error) return <div>Error: {error}</div>;
    if (!tenant) return <div>No tenant</div>;
    
    return (
      <div>
        <div data-testid="tenant-id">{tenant.id}</div>
        <div data-testid="tenant-name">{tenant.name}</div>
      </div>
    );
  };

  it('should fetch and display tenant info successfully', async () => {
    const mockTenant = {
      tenant_id: 'tenant-123',
      tenant_name: 'Test Organization',
      created_at: '2025-01-01T00:00:00Z'
    };

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTenant),
      })
    );

    localStorage.setItem('token', 'fake-token');

    render(
      <TenantProvider>
        <TestConsumer />
      </TenantProvider>
    );

    expect(screen.getByText('Loading...')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId('tenant-id')).toHaveTextContent('tenant-123');
    });

    expect(screen.getByTestId('tenant-name')).toHaveTextContent('Test Organization');
    
    expect(global.fetch).toHaveBeenCalledWith(
      `${API_BASE_URL}/api/tenant/me`,
      expect.objectContaining({
        headers: expect.objectContaining({
          'Authorization': 'Bearer fake-token'
        })
      })
    );
  });

  it('should handle missing token gracefully', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Unauthorized' }),
      })
    );

    render(
      <TenantProvider>
        <TestConsumer />
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  it('should handle network errors', async () => {
    global.fetch = vi.fn(() =>
      Promise.reject(new Error('Network error'))
    );

    localStorage.setItem('token', 'fake-token');

    render(
      <TenantProvider>
        <TestConsumer />
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  it('should handle 404 not found', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ 
          error: { message: 'User not assigned to tenant' } 
        }),
      })
    );

    localStorage.setItem('token', 'fake-token');

    render(
      <TenantProvider>
        <TestConsumer />
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByText(/Error:/)).toBeInTheDocument();
    });
  });

  it('should provide refreshTenant function', async () => {
    const mockTenant = {
      tenant_id: 'tenant-123',
      tenant_name: 'Test Org',
      created_at: '2025-01-01T00:00:00Z'
    };

    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: true,
        json: () => Promise.resolve(mockTenant),
      })
    );

    localStorage.setItem('token', 'fake-token');

    const TestRefresh = () => {
      const { tenant, refreshTenant } = useTenant();
      
      return (
        <div>
          {tenant && <div data-testid="tenant-name">{tenant.name}</div>}
          <button onClick={refreshTenant}>Refresh</button>
        </div>
      );
    };

    render(
      <TenantProvider>
        <TestRefresh />
      </TenantProvider>
    );

    await waitFor(() => {
      expect(screen.getByTestId('tenant-name')).toBeInTheDocument();
    });

    const refreshButton = screen.getByText('Refresh');
    expect(refreshButton).toBeInTheDocument();
  });
});
