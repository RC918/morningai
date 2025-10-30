import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '@/lib/api'

interface User {
  id: string | null
  name: string
  email: string
  avatar: string
  role: string
  tenant_id: string
}

interface Tenant {
  id: string
  name: string
  plan: string
  status: string
  billing_cycle: string
  features: string[]
}

interface PaymentMethod {
  type: string
  last_four: string
  expires: string
}

interface Usage {
  api_calls: number
  api_limit: number
  storage_used: number
  storage_limit: number
}

interface Billing {
  current_plan: string
  billing_status: string
  next_billing_date: string
  usage: Usage
  payment_method?: PaymentMethod
  plans?: any[]
}

interface Status {
  online: boolean
  last_sync: string
  notifications_count: number
  system_health: string
  maintenance_mode: boolean
}

interface Toast {
  id: string
  title: string
  description?: string
  variant?: string
  timestamp: number
}

interface Loading {
  user: boolean
  billing: boolean
  global: boolean
}

interface AppState {
  user: User
  tenant: Tenant
  billing: Billing
  status: Status
  toasts: Toast[]
  loading: Loading
  error: string | null
  setUser: (user: Partial<User>) => void
  setTenant: (tenant: Partial<Tenant>) => void
  setBilling: (billing: Partial<Billing>) => void
  setStatus: (status: Partial<Status>) => void
  addToast: (toast: { title: string; description?: string; variant?: string }) => { id: string; dismiss: () => void }
  removeToast: (id: string) => void
  clearToasts: () => void
  setLoading: (key: keyof Loading, value: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  loadUserData: () => Promise<void>
  loadBillingData: () => Promise<void>
  updateSystemStatus: () => void
  reset: () => void
}

const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      user: {
        id: null,
        name: 'Ryan Chen',
        email: 'ryan@morningai.com',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
        role: 'Owner',
        tenant_id: 'tenant_001'
      },
      
      tenant: {
        id: 'tenant_001',
        name: 'Morning AI',
        plan: 'pro',
        status: 'active',
        billing_cycle: 'monthly',
        features: ['dashboard', 'checkout', 'settings']
      },
      
      billing: {
        current_plan: 'pro',
        billing_status: 'active',
        next_billing_date: '2025-11-01',
        usage: {
          api_calls: 1250,
          api_limit: 10000,
          storage_used: 2.5,
          storage_limit: 100
        },
        payment_method: {
          type: 'card',
          last_four: '4242',
          expires: '12/26'
        }
      },
      
      status: {
        online: true,
        last_sync: new Date().toISOString(),
        notifications_count: 3,
        system_health: 'healthy',
        maintenance_mode: false
      },
      
      toasts: [],
      
      loading: {
        user: false,
        billing: false,
        global: false
      },
      
      error: null,
      
      setUser: (user: Partial<User>) => set({ user: { ...get().user, ...user } }),
      
      setTenant: (tenant: Partial<Tenant>) => set({ tenant: { ...get().tenant, ...tenant } }),
      
      setBilling: (billing: Partial<Billing>) => set({ billing: { ...get().billing, ...billing } }),
      
      setStatus: (status: Partial<Status>) => set({ status: { ...get().status, ...status } }),
      
      addToast: (toast: { title: string; description?: string; variant?: string }) => {
        const id = Math.random().toString(36).substr(2, 9)
        const newToast: Toast = {
          id,
          title: toast.title,
          description: toast.description,
          variant: toast.variant || 'default',
          timestamp: Date.now()
        }
        
        set(state => ({
          toasts: [...state.toasts, newToast]
        }))
        
        setTimeout(() => {
          get().removeToast(id)
        }, 5000)
        
        return { id, dismiss: () => get().removeToast(id) }
      },
      
      removeToast: (id: string) => set(state => ({
        toasts: state.toasts.filter(toast => toast.id !== id)
      })),
      
      clearToasts: () => set({ toasts: [] }),
      
      setLoading: (key: keyof Loading, value: boolean) => set(state => ({
        loading: { ...state.loading, [key]: value }
      })),
      
      setError: (error: string | null) => set({ error }),
      
      clearError: () => set({ error: null }),
      
      loadUserData: async () => {
        set(state => ({ loading: { ...state.loading, user: true } }))
        try {
          const userData = await apiClient.verifyAuth()
          set({ 
            user: { ...get().user, ...userData },
            loading: { ...get().loading, user: false }
          })
        } catch (error) {
          const err = error as Error
          console.warn('Failed to load user data:', err.message)
          set({ 
            loading: { ...get().loading, user: false },
            error: null
          })
        }
      },
      
      loadBillingData: async () => {
        set(state => ({ loading: { ...state.loading, billing: true } }))
        try {
          const billingData = await apiClient.getBillingPlans()
          set({ 
            billing: { ...get().billing, plans: billingData },
            loading: { ...get().loading, billing: false }
          })
        } catch (error) {
          const err = error as Error
          console.warn('Failed to load billing data:', err.message)
          set({ 
            loading: { ...get().loading, billing: false },
            error: null
          })
        }
      },
      
      updateSystemStatus: () => {
        set(state => ({
          status: {
            ...state.status,
            last_sync: new Date().toISOString(),
            online: navigator.onLine
          }
        }))
      },
      
      reset: () => set({
        user: {
          id: null,
          name: 'Ryan Chen',
          email: 'ryan@morningai.com',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
          role: 'Owner',
          tenant_id: 'tenant_001'
        },
        tenant: {
          id: 'tenant_001',
          name: 'Morning AI',
          plan: 'pro',
          status: 'active',
          billing_cycle: 'monthly',
          features: ['dashboard', 'checkout', 'settings']
        },
        billing: {
          current_plan: 'pro',
          billing_status: 'active',
          next_billing_date: '2025-11-01',
          usage: {
            api_calls: 1250,
            api_limit: 10000,
            storage_used: 2.5,
            storage_limit: 100
          }
        },
        status: {
          online: true,
          last_sync: new Date().toISOString(),
          notifications_count: 0,
          system_health: 'healthy',
          maintenance_mode: false
        },
        toasts: [],
        loading: {
          user: false,
          billing: false,
          global: false
        },
        error: null
      })
    }),
    {
      name: 'morning-ai-app-store',
      partialize: (state) => ({
        user: state.user,
        tenant: state.tenant,
        billing: state.billing,
        status: {
          notifications_count: state.status.notifications_count
        }
      })
    }
  )
)

export default useAppStore
