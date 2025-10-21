import { Tolgee, DevTools, FormatSimple } from "@tolgee/react";
import { I18nextPlugin } from "@tolgee/i18next";

const tolgee = Tolgee()
  .use(DevTools()) // In-context translation UI
  .use(FormatSimple())
  .use(I18nextPlugin())
  .init({
    apiUrl: import.meta.env.VITE_TOLGEE_API_URL,
    apiKey: import.meta.env.VITE_TOLGEE_API_KEY,
    projectId: import.meta.env.VITE_TOLGEE_PROJECT_ID,
    
    defaultLanguage: 'en-US',
    
    staticData: {
      'zh-TW': () => import('./locales/zh-TW.json'),
      'en-US': () => import('./locales/en-US.json'),
    },
    
    enableDevTools: import.meta.env.DEV,
  });

export default tolgee;
