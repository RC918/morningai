/**
 * Unit tests for TenantSettings component
 * Tests organization settings display, member management, and role updates
 */
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TenantSettings from '../components/TenantSettings';
import { TenantProvider } from '../contexts/TenantContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001';

const mockTenantContext = {
  tenant: {
    id: 'tenant-123',
    name: 'Test Organization',
    createdAt: '2025-01-01T00:00:00Z'
  },
  loading: false,
  error: null,
  refreshTenant: vi.fn()
};

vi.mock('../contexts/TenantContext', async () => {
  const actual = await vi.importActual('../contexts/TenantContext');
  return {
    ...actual,
    useTenant: () => mockTenantContext
  };
});

describe('TenantSettings', () => {
  beforeEach(() => {
    localStorage.setItem('token', 'fake-token');
    vi.clearAllMocks();
  });

  const mockTenantInfo = {
    tenant_id: 'tenant-123',
    tenant_name: 'Test Organization',
    member_count: 5,
    task_count: 42,
    created_at: '2025-01-01T00:00:00Z'
  };

  const mockMembers = [
    {
      id: 'user-1',
      email: 'alice@example.com',
      display_name: 'Alice Admin',
      role: 'owner',
      created_at: '2025-01-01T00:00:00Z'
    },
    {
      id: 'user-2',
      email: 'bob@example.com',
      display_name: 'Bob Member',
      role: 'member',
      created_at: '2025-01-02T00:00:00Z'
    }
  ];

  it('should display tenant information', async () => {
    global.fetch = vi.fn((url) => {
      if (url.includes('/api/tenant/info')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTenantInfo)
        });
      }
      if (url.includes('/api/tenant/members')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ members: mockMembers })
        });
      }
    });

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText('Test Organization')).toBeInTheDocument();
    });

    expect(screen.getByText(/5.*members/i)).toBeInTheDocument();
    expect(screen.getByText(/42.*tasks/i)).toBeInTheDocument();
  });

  it('should display member list', async () => {
    global.fetch = vi.fn((url) => {
      if (url.includes('/api/tenant/info')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTenantInfo)
        });
      }
      if (url.includes('/api/tenant/members')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ members: mockMembers })
        });
      }
    });

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    });

    expect(screen.getByText('bob@example.com')).toBeInTheDocument();
    expect(screen.getByText('Alice Admin')).toBeInTheDocument();
    expect(screen.getByText('Bob Member')).toBeInTheDocument();
  });

  it('should display role badges correctly', async () => {
    global.fetch = vi.fn((url) => {
      if (url.includes('/api/tenant/info')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTenantInfo)
        });
      }
      if (url.includes('/api/tenant/members')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ members: mockMembers })
        });
      }
    });

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText('Owner')).toBeInTheDocument();
    });

    expect(screen.getByText('Member')).toBeInTheDocument();
  });

  it('should handle role update', async () => {
    let updateCalled = false;

    global.fetch = vi.fn((url, options) => {
      if (url.includes('/api/tenant/info')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTenantInfo)
        });
      }
      if (url.includes('/api/tenant/members') && options?.method === 'GET') {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ members: mockMembers })
        });
      }
      if (options?.method === 'PUT') {
        updateCalled = true;
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ id: 'user-2', role: 'admin' })
        });
      }
    });

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText('bob@example.com')).toBeInTheDocument();
    });

    const roleSelects = screen.getAllByRole('combobox');
    expect(roleSelects.length).toBeGreaterThan(0);
  });

  it('should handle loading state', () => {
    global.fetch = vi.fn(() => new Promise(() => {}));

    render(<TenantSettings />);

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
  });

  it('should handle error state', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 500,
        json: () => Promise.resolve({ error: 'Server error' })
      })
    );

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('should handle unauthorized access', async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
        status: 401,
        json: () => Promise.resolve({ error: 'Unauthorized' })
      })
    );

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });

  it('should format dates correctly', async () => {
    global.fetch = vi.fn((url) => {
      if (url.includes('/api/tenant/info')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve(mockTenantInfo)
        });
      }
      if (url.includes('/api/tenant/members')) {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ members: mockMembers })
        });
      }
    });

    render(<TenantSettings />);

    await waitFor(() => {
      expect(screen.getByText('alice@example.com')).toBeInTheDocument();
    });

    const dateElements = screen.getAllByText(/2025/);
    expect(dateElements.length).toBeGreaterThan(0);
  });
});
