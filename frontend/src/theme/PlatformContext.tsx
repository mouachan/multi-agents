import { createContext, useCallback, useContext, useState, type ReactNode } from 'react'

/** Platform facts surfaced in the top bar (model served by OGX, from the last chat turn). */
interface PlatformContextValue {
  modelId: string | null
  setModelId: (modelId: string | null | undefined) => void
}

const PlatformContext = createContext<PlatformContextValue | undefined>(undefined)
const STORAGE_KEY = 'platform-model-id'

export function PlatformProvider({ children }: { children: ReactNode }) {
  const [modelId, setModel] = useState<string | null>(() => localStorage.getItem(STORAGE_KEY))

  const setModelId = useCallback((value: string | null | undefined) => {
    if (!value) return
    setModel(value)
    localStorage.setItem(STORAGE_KEY, value)
  }, [])

  return <PlatformContext.Provider value={{ modelId, setModelId }}>{children}</PlatformContext.Provider>
}

export function usePlatform(): PlatformContextValue {
  const ctx = useContext(PlatformContext)
  if (!ctx) throw new Error('usePlatform must be used within PlatformProvider')
  return ctx
}
