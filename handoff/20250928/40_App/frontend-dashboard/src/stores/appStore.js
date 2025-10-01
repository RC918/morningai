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
      }),

      dashboardState: {
        isEditMode: false,
        showReportCenter: false,
        availableWidgets: [],
        dashboardLayout: [],
        dashboardData: {},
        systemMetrics: {
          cpu_usage: 72,
          memory_usage: 68,
          response_time: 145,
          error_rate: 0.02,
          active_strategies: 12,
          pending_approvals: 3,
          cost_today: 45.67,
          cost_saved: 123.45
        },
        recentDecisions: [],
        performanceData: []
      },

      setEditMode: (isEditMode) => set(state => ({ 
        dashboardState: { ...state.dashboardState, isEditMode } 
      })),
      setShowReportCenter: (showReportCenter) => set(state => ({ 
        dashboardState: { ...state.dashboardState, showReportCenter } 
      })),
      updateSystemMetrics: (metrics) => set(state => ({ 
        dashboardState: { ...state.dashboardState, systemMetrics: { ...state.dashboardState.systemMetrics, ...metrics } } 
      })),
      setDashboardLayout: (layout) => set(state => ({ 
        dashboardState: { ...state.dashboardState, dashboardLayout: layout } 
      })),
      setAvailableWidgets: (widgets) => set(state => ({ 
        dashboardState: { ...state.dashboardState, availableWidgets: widgets } 
      })),
      setDashboardData: (data) => set(state => ({ 
        dashboardState: { ...state.dashboardState, dashboardData: data } 
      })),
      setRecentDecisions: (decisions) => set(state => ({ 
        dashboardState: { ...state.dashboardState, recentDecisions: decisions } 
      })),
      setPerformanceData: (data) => set(state => ({ 
        dashboardState: { ...state.dashboardState, performanceData: data } 
      })),
      loadDashboardData: async () => {
        set(state => ({ loading: { ...state.loading, dashboard: true } }))
        try {
          const data = await apiClient.getDashboardData()
          set(state => ({ 
            dashboardState: { ...state.dashboardState, dashboardData: data },
            loading: { ...state.loading, dashboard: false }
          }))
        } catch (error) {
          console.error('Failed to load dashboard data:', error)
          set(state => ({ loading: { ...state.loading, dashboard: false } }))
        }
      },

      decisionApprovalState: {
        pendingDecisions: [],
        selectedDecision: null,
        approvalComment: ''
      },

      setPendingDecisions: (decisions) => set(state => ({ 
        decisionApprovalState: { ...state.decisionApprovalState, pendingDecisions: decisions } 
      })),
      setSelectedDecision: (decision) => set(state => ({ 
        decisionApprovalState: { ...state.decisionApprovalState, selectedDecision: decision } 
      })),
      setApprovalComment: (comment) => set(state => ({ 
        decisionApprovalState: { ...state.decisionApprovalState, approvalComment: comment } 
      })),
      approveDecision: async (decisionId, comment = '') => {
        try {
          await new Promise(resolve => setTimeout(resolve, 1000))
          set(state => ({
            decisionApprovalState: {
              ...state.decisionApprovalState,
              pendingDecisions: state.decisionApprovalState.pendingDecisions.filter(d => d.id !== decisionId),
              selectedDecision: null,
              approvalComment: ''
            }
          }))
          get().addToast({
            title: "決策已批准",
            description: "策略將立即執行",
            variant: "default"
          })
        } catch (error) {
          get().addToast({
            title: "批准失敗", 
            description: "請稍後重試",
            variant: "destructive"
          })
        }
      },
      rejectDecision: async (decisionId, comment) => {
        if (!comment.trim()) {
          get().addToast({
            title: "請提供拒絕理由",
            description: "拒絕決策時必須說明原因",
            variant: "destructive"
          })
          return
        }

        try {
          await new Promise(resolve => setTimeout(resolve, 1000))
          set(state => ({
            decisionApprovalState: {
              ...state.decisionApprovalState,
              pendingDecisions: state.decisionApprovalState.pendingDecisions.filter(d => d.id !== decisionId),
              selectedDecision: null,
              approvalComment: ''
            }
          }))
          get().addToast({
            title: "決策已拒絕",
            description: "系統將尋找替代方案",
            variant: "default"
          })
        } catch (error) {
          get().addToast({
            title: "拒絕失敗",
            description: "請稍後重試",
            variant: "destructive"
          })
        }
      }
    }),
    {
      name: 'morning-ai-app-store',
      partialize: (state) => ({
        user: state.user,
        tenant: state.tenant,
        billing: state.billing,
        status: {
          notifications_count: state.status.notifications_count
        },
        dashboardState: state.dashboardState,
        decisionApprovalState: state.decisionApprovalState
      })
    }
  )
)

export default useAppStore
