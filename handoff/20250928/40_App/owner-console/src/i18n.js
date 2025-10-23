import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'
import tolgee from './tolgee'

import enUS from './locales/en-US.json'
import zhTW from './locales/zh-TW.json'

const resources = {
  'en-US': {
    translation: enUS
  },
  'zh-TW': {
    translation: zhTW
  }
}

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en-US',
    debug: false,
    interpolation: {
      escapeValue: false
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage']
    }
  })

export default i18n
export { tolgee }
