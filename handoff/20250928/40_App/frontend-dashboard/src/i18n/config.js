import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import tolgee from './tolgee'

import zhTW from './locales/zh-TW.json'
import enUS from './locales/en-US.json'

const resources = {
  'zh-TW': {
    translation: zhTW
  },
  'en-US': {
    translation: enUS
  }
}

const isLocalStorageAvailable = () => {
  try {
    const test = '__i18n_test__'
    localStorage.setItem(test, test)
    localStorage.removeItem(test)
    return true
  } catch (e) {
    return false
  }
}

const isBrowser = () => typeof window !== 'undefined'

const customLanguageDetector = {
  name: 'customDetector',
  lookup() {
    if (!isBrowser()) {
      return 'en-US'
    }

    if (isLocalStorageAvailable()) {
      try {
        const savedLang = localStorage.getItem('i18nextLng')
        if (savedLang && (savedLang === 'zh-TW' || savedLang === 'en-US')) {
          return savedLang
        }
      } catch (e) {
        console.warn('Failed to read from localStorage:', e)
      }
    }

    try {
      const browserLang = navigator.language || navigator.userLanguage
      
      if (!browserLang) {
        return 'en-US'
      }

      const langLower = browserLang.toLowerCase()
      
      if (langLower === 'zh-tw' || langLower === 'zh-hant' || langLower.startsWith('zh-tw') || langLower.startsWith('zh-hant')) {
        return 'zh-TW'
      }
      
      if (langLower === 'zh-cn' || langLower === 'zh-hans' || langLower.startsWith('zh-cn') || langLower.startsWith('zh-hans')) {
        return 'zh-TW'
      }
      
      if (langLower === 'zh' || langLower.startsWith('zh-')) {
        return 'zh-TW'
      }
      
      return 'en-US'
    } catch (e) {
      console.warn('Failed to detect browser language:', e)
      return 'en-US'
    }
  },
  cacheUserLanguage(lng) {
    if (!isBrowser() || !isLocalStorageAvailable()) {
      return
    }

    try {
      localStorage.setItem('i18nextLng', lng)
    } catch (e) {
      console.warn('Failed to cache language preference:', e)
    }
  }
}

const languageDetector = new LanguageDetector()
languageDetector.addDetector(customLanguageDetector)

i18n
  .use(languageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en-US',
    
    detection: {
      order: ['customDetector'],
      caches: ['localStorage']
    },

    interpolation: {
      escapeValue: false
    },

    react: {
      useSuspense: false
    }
  })

export default i18n
export { customLanguageDetector, isLocalStorageAvailable, isBrowser, tolgee }
