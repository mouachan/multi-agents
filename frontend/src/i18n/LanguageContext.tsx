import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { translations, type Locale } from './translations'

interface LanguageContextType {
  locale: Locale
  setLocale: (locale: Locale) => void
  t: (key: string) => string
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined)

function detectBrowserLanguage(): Locale {
  const lang = navigator.language || ''
  return lang.startsWith('fr') ? 'fr' : 'en'
}

function getNestedValue(obj: Record<string, any>, path: string): string | undefined {
  const parts = path.split('.')
  let current: any = obj
  for (const part of parts) {
    if (current == null || typeof current !== 'object') return undefined
    current = current[part]
  }
  return typeof current === 'string' ? current : undefined
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(() => {
    const saved = localStorage.getItem('app-locale')
    if (saved === 'fr' || saved === 'en') return saved
    return detectBrowserLanguage()
  })

  useEffect(() => {
    localStorage.setItem('app-locale', locale)
    document.documentElement.lang = locale
  }, [locale])

  const setLocale = (newLocale: Locale) => {
    setLocaleState(newLocale)
  }

  const t = (key: string): string => {
    const value = getNestedValue(translations[locale], key)
    if (value !== undefined) return value
    // Fallback to other locale
    const fallback = getNestedValue(translations[locale === 'fr' ? 'en' : 'fr'], key)
    if (fallback !== undefined) return fallback
    // Return key as last resort
    return key
  }

  return (
    <LanguageContext.Provider value={{ locale, setLocale, t }}>
      {children}
    </LanguageContext.Provider>
  )
}

export function useTranslation() {
  const context = useContext(LanguageContext)
  if (!context) {
    throw new Error('useTranslation must be used within a LanguageProvider')
  }
  return context
}
