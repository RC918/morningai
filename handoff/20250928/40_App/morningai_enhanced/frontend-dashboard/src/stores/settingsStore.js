import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '@/lib/api'

const useSettingsStore = create(
  persist(
    (set, get) => ({
      profile: {
        name: 'Ryan Chen',
        email: 'ryan@morningai.com',
        avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
        role: 'Owner'
      },
      
      preferences: {
        language: 'zh-TW',
        theme: 'light',
        notifications: {
          email: true,
          desktop: true,
          aiSuggestions: true
        }
      },
      
      loading: false,
      error: null,
      
      setProfile: (profile) => set({ profile }),
      
      setPreferences: (preferences) => set({ preferences }),
      
      setLanguage: (language) => set((state) => ({
        preferences: { ...state.preferences, language }
      })),
      
      setTheme: (theme) => {
        set((state) => ({
          preferences: { ...state.preferences, theme }
        }))
        document.documentElement.setAttribute('data-theme', theme)
        if (theme === 'dark') {
          document.documentElement.classList.add('dark')
        } else {
          document.documentElement.classList.remove('dark')
        }
      },
      
      setNotifications: (notifications) => set((state) => ({
        preferences: { ...state.preferences, notifications }
      })),
      
      loadFromAPI: async () => {
        set({ loading: true, error: null })
        try {
          const data = await apiClient.getSettings()
          set({ 
            profile: data.profile || get().profile,
            preferences: data.preferences || get().preferences,
            loading: false 
          })
        } catch (error) {
          console.warn('Failed to load settings from API, using persisted state:', error.message)
          set({ loading: false, error: null })
        }
      },
      
      saveToAPI: async () => {
        set({ loading: true, error: null })
        try {
          const { profile, preferences } = get()
          await apiClient.saveSettings({ profile, preferences })
          set({ loading: false })
        } catch (error) {
          console.warn('Failed to save settings to API, changes saved locally:', error.message)
          set({ loading: false, error: null })
        }
      },
      
      reset: () => set({
        profile: {
          name: 'Ryan Chen',
          email: 'ryan@morningai.com',
          avatar: 'https://api.dicebear.com/7.x/avataaars/svg?seed=Ryan',
          role: 'Owner'
        },
        preferences: {
          language: 'zh-TW',
          theme: 'light',
          notifications: {
            email: true,
            desktop: true,
            aiSuggestions: true
          }
        }
      })
    }),
    {
      name: 'morning-ai-settings',
      partialize: (state) => ({
        profile: state.profile,
        preferences: state.preferences
      })
    }
  )
)

export default useSettingsStore
