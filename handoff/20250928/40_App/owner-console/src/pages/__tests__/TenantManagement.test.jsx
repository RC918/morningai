import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import TenantManagement from '../TenantManagement';
import * as tenantApi from '@/lib/generated/tenant/tenant';

vi.mock('@/lib/generated/tenant/tenant', () => ({
  getTenantInfo: vi.fn(),
  getTenantMembers: vi.fn(),
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
      tenantApi.getTenantInfo.mockImplementation(() => new Promise(() => {}));
      tenantApi.getTenantMembers.mockImplementation(() => new Promise(() => {}));

      render(<TenantManagement />);

      expect(screen.getByText(/loading/i)).toBeInTheDocument();
    });
  });

  describe('Data Fetching', () => {
    it('should fetch tenant info and members from API', async () => {
      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [
            { id: 'user-1', tenant_id: 'tenant-1', name: 'User One' },
          ],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(tenantApi.getTenantInfo).toHaveBeenCalledTimes(1);
        expect(tenantApi.getTenantMembers).toHaveBeenCalledTimes(1);
      });
    });

    it('should enrich tenant data with user counts', async () => {
      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [
            { id: 'user-1', tenant_id: 'tenant-1', name: 'User One' },
            { id: 'user-2', tenant_id: 'tenant-1', name: 'User Two' },
          ],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
        expect(screen.getByText('2 tenants.users')).toBeInTheDocument();
      });
    });
  });

  describe('Error Handling', () => {
    it('should display error message when API fails', async () => {
      tenantApi.getTenantInfo.mockRejectedValueOnce(new Error('API Error'));
      tenantApi.getTenantMembers.mockResolvedValue({ status: 200, data: { members: [] } });

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('API Error')).toBeInTheDocument();
      });
    });

    it('should show retry button on error', async () => {
      tenantApi.getTenantInfo.mockRejectedValueOnce(new Error('API Error'));
      tenantApi.getTenantMembers.mockResolvedValue({ status: 200, data: { members: [] } });

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('common.refresh')).toBeInTheDocument();
      });
    });

    it('should retry loading when retry button is clicked', async () => {
      tenantApi.getTenantInfo.mockRejectedValueOnce(new Error('API Error'));
      tenantApi.getTenantMembers.mockResolvedValue({ status: 200, data: { members: [] } });

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('common.refresh')).toBeInTheDocument();
      });

      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      const retryButton = screen.getByText('common.refresh');
      fireEvent.click(retryButton);

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
      });
    });
  });

  describe('Tenant Display', () => {
    it('should display tenant list', async () => {
      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
      });
    });

    it('should display tenant status badges', async () => {
      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.getByText('tenants.active')).toBeInTheDocument();
      });
    });

    it('should handle empty tenant list', async () => {
      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
        expect(screen.getByText('Tenant One')).toBeInTheDocument();
      });
    });
  });

  describe('API Integration', () => {
    it('should use parallel API calls for efficiency', async () => {
      const mockTenantInfoResponse = {
        status: 200,
        data: {
          tenant_id: 'tenant-1',
          tenant_name: 'Tenant One',
        },
      };

      const mockMembersResponse = {
        status: 200,
        data: {
          members: [],
        },
      };

      tenantApi.getTenantInfo.mockResolvedValue(mockTenantInfoResponse);
      tenantApi.getTenantMembers.mockResolvedValue(mockMembersResponse);

      render(<TenantManagement />);

      await waitFor(() => {
        expect(tenantApi.getTenantInfo).toHaveBeenCalledTimes(1);
        expect(tenantApi.getTenantMembers).toHaveBeenCalledTimes(1);
      });
    });
  });
});
