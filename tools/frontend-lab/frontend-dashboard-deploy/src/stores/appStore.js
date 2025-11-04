import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '@/lib/api'

const useAppStore = create(
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
      
      pathTracking: {
        activePaths: {}
      },
      
      setUser: (user) => set({ user: { ...get().user, ...user } }),
      
      setTenant: (tenant) => set({ tenant: { ...get().tenant, ...tenant } }),
      
      setBilling: (billing) => set({ billing: { ...get().billing, ...billing } }),
      
      setStatus: (status) => set({ status: { ...get().status, ...status } }),
      
      addToast: (toast) => {
        const id = Math.random().toString(36).substr(2, 9)
        const newToast = {
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
      
      removeToast: (id) => set(state => ({
        toasts: state.toasts.filter(toast => toast.id !== id)
      })),
      
      clearToasts: () => set({ toasts: [] }),
      
      setLoading: (key, value) => set(state => ({
        loading: { ...state.loading, [key]: value }
      })),
      
      setError: (error) => set({ error }),
      
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
          console.warn('Failed to load user data:', error.message)
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
          console.warn('Failed to load billing data:', error.message)
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
      
      trackPathStart: (pathName) => {
        const pathId = `${pathName}_${Date.now()}`
        set(state => ({
          pathTracking: {
            ...state.pathTracking,
            activePaths: {
              ...state.pathTracking.activePaths,
              [pathId]: {
                name: pathName,
                startTime: Date.now(),
                status: 'in_progress'
              }
            }
          }
        }))
        return pathId
      },
      
      trackPathComplete: (pathId) => {
        const state = get()
        const path = state.pathTracking.activePaths[pathId]
        if (path) {
          const duration = Date.now() - path.startTime
          const trackingData = {
            path_name: path.name,
            status: 'completed',
            duration_ms: duration,
            timestamp: new Date().toISOString(),
            user_id: state.user.id,
            tenant_id: state.user.tenant_id
          }
          
          if (window.Sentry) {
            window.Sentry.captureMessage('Path Completed', {
              level: 'info',
              extra: trackingData
            })
          }
          
          const { [pathId]: _, ...remainingPaths } = state.pathTracking.activePaths
          set(state => ({
            pathTracking: {
              ...state.pathTracking,
              activePaths: remainingPaths
            }
          }))
        }
      },
      
      trackPathFail: (pathId, error) => {
        const state = get()
        const path = state.pathTracking.activePaths[pathId]
        if (path) {
          const duration = Date.now() - path.startTime
          const trackingData = {
            path_name: path.name,
            status: 'failed',
            duration_ms: duration,
            error: error?.message || 'Unknown error',
            timestamp: new Date().toISOString(),
            user_id: state.user.id,
            tenant_id: state.user.tenant_id
          }
          
          if (window.Sentry) {
            window.Sentry.captureException(error, {
              extra: trackingData
            })
          }
          
          const { [pathId]: _, ...remainingPaths } = state.pathTracking.activePaths
          set(state => ({
            pathTracking: {
              ...state.pathTracking,
              activePaths: remainingPaths
            }
          }))
        }
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
