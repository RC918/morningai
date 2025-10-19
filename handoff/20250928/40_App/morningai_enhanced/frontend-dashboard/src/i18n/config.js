import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

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

const customLanguageDetector = {
  name: 'customDetector',
  lookup() {
    const savedLang = localStorage.getItem('i18nextLng')
    if (savedLang && (savedLang === 'zh-TW' || savedLang === 'en-US')) {
      return savedLang
    }

    const browserLang = navigator.language || navigator.userLanguage
    
    if (browserLang.toLowerCase().startsWith('zh')) {
      return 'zh-TW'
    }
    
    return 'en-US'
  },
  cacheUserLanguage(lng) {
    localStorage.setItem('i18nextLng', lng)
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
