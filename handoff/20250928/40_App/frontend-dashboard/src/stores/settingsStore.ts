import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import apiClient from '@/lib/api'

interface Profile {
  name: string
  email: string
  avatar: string
  role: string
}

interface Notifications {
  email: boolean
  desktop: boolean
  aiSuggestions: boolean
}

interface Preferences {
  language: string
  theme: string
  notifications: Notifications
}

interface SettingsState {
  profile: Profile
  preferences: Preferences
  loading: boolean
  error: string | null
  setProfile: (profile: Profile) => void
  setPreferences: (preferences: Preferences) => void
  setLanguage: (language: string) => void
  setTheme: (theme: string) => void
  setNotifications: (notifications: Notifications) => void
  loadFromAPI: () => Promise<void>
  saveToAPI: () => Promise<void>
  reset: () => void
}

const useSettingsStore = create<SettingsState>()(
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
      
      setProfile: (profile: Profile) => set({ profile }),
      
      setPreferences: (preferences: Preferences) => set({ preferences }),
      
      setLanguage: (language: string) => set((state) => ({
        preferences: { ...state.preferences, language }
      })),
      
      setTheme: (theme: string) => {
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
      
      setNotifications: (notifications: Notifications) => set((state) => ({
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
          const err = error as Error
          console.warn('Failed to load settings from API, using persisted state:', err.message)
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
          const err = error as Error
          console.warn('Failed to save settings to API, changes saved locally:', err.message)
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
