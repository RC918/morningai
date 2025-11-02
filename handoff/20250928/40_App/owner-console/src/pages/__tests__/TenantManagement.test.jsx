import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TenantManagement from '../TenantManagement';
import * as apiClient from '../../lib/api-client';

vi.mock('../../lib/api-client', () => ({
  apiClient: vi.fn(),
}));

vi.mock('react-i18next', () => ({
  useTranslation: () => ({
    t: (key) => key,
  }),
}));

describe('TenantManagement Page (P1)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('Loading State', () => {
    it('should display loading spinner initially', () => {
      apiClient.apiClient.mockImplementation(() => new Promise(() => {}));

      render(<TenantManagement />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe('Data Fetching', () => {
    it('should fetch tenant info and members from API', async () => {
      const mockTenantInfo = {
        data: {
          tenants: [
            { id: 'tenant-1', name: 'Tenant One', status: 'active' },
          ],
        },
      };

      const mockMembers = {
        data: {
          members: [
            { id: 'user-1', tenant_id: 'tenant-1', name: 'User One' },
          ],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(apiClient.apiClient).toHaveBeenCalledWith('/api/tenant/info', { method: 'GET' });
        expect(apiClient.apiClient).toHaveBeenCalledWith('/api/tenant/members', { method: 'GET' });
      });
    });

    it('should enrich tenant data with user counts', async () => {
      const mockTenantInfo = {
        data: {
          tenants: [
            { id: 'tenant-1', name: 'Tenant One', status: 'active' },
            { id: 'tenant-2', name: 'Tenant Two', status: 'active' },
          ],
        },
      };

      const mockMembers = {
        data: {
          members: [
            { id: 'user-1', tenant_id: 'tenant-1', name: 'User One' },
            { id: 'user-2', tenant_id: 'tenant-1', name: 'User Two' },
            { id: 'user-3', tenant_id: 'tenant-2', name: 'User Three' },
          ],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
        expect(screen.getByText('Tenant Two')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      apiClient.apiClient.mockRejectedValueOnce(new Error('API Error'));

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      apiClient.apiClient.mockRejectedValueOnce(new Error('API Error'));

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('common.refresh')).toBeInTheDocument();
      });
    });

    it('should retry loading when retry button is clicked', async () => {
      apiClient.apiClient.mockRejectedValueOnce(new Error('API Error'));

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('common.refresh')).toBeInTheDocument();
      });

      const mockTenantInfo = {
        data: {
          tenants: [{ id: 'tenant-1', name: 'Tenant One', status: 'active' }],
        },
      };

      const mockMembers = {
        data: {
          members: [],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      const retryButton = screen.getByText('common.refresh');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
      });
    });
  });

  describe('Tenant Display', () => {
    it('should display tenant list', async () => {
      const mockTenantInfo = {
        data: {
          tenants: [
            { id: 'tenant-1', name: 'Tenant One', status: 'active', plan: 'pro' },
            { id: 'tenant-2', name: 'Tenant Two', status: 'active', plan: 'enterprise' },
          ],
        },
      };

      const mockMembers = {
        data: {
          members: [],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
        expect(screen.getByText('Tenant Two')).toBeInTheDocument();
      });
    });

    it('should display tenant status badges', async () => {
      const mockTenantInfo = {
        data: {
          tenants: [
            { id: 'tenant-1', name: 'Tenant One', status: 'active' },
          ],
        },
      };

      const mockMembers = {
        data: {
          members: [],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('tenants.active')).toBeInTheDocument();
      });
    });

    it('should handle empty tenant list', async () => {
      const mockTenantInfo = {
        data: {
          tenants: [],
        },
      };

      const mockMembers = {
        data: {
          members: [],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('should use parallel API calls for efficiency', async () => {
      const mockTenantInfo = {
        data: {
          tenants: [{ id: 'tenant-1', name: 'Tenant One', status: 'active' }],
        },
      };

      const mockMembers = {
        data: {
          members: [],
        },
      };

      apiClient.apiClient
        .mockResolvedValueOnce(mockTenantInfo)
        .mockResolvedValueOnce(mockMembers);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(apiClient.apiClient).toHaveBeenCalledTimes(2);
      });

      const calls = apiClient.apiClient.mock.calls;
      expect(calls[0][0]).toBe('/api/tenant/info');
      expect(calls[1][0]).toBe('/api/tenant/members');
    });
  });
});
