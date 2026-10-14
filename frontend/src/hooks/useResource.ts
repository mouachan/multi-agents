import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Load async data. `reload()` refetches silently (keeps the current data on screen),
 * which is what polling uses — no spinner flicker.
 */
export function useResource<T>(loader: () => Promise<T>, deps: unknown[]) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  const run = useCallback(async (silent: boolean) => {
    if (!silent) setLoading(true)
    try {
      const value = await loaderRef.current()
      setData(value)
      setError(null)
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || 'Request failed')
    } finally {
      if (!silent) setLoading(false)
    }
  }, [])

  useEffect(() => {
    setData(null)
    run(false)
  }, deps) // eslint-disable-line react-hooks/exhaustive-deps

  const reload = useCallback(() => run(true), [run])
  return { data, loading, error, reload, setData }
}

/** Call `fn` every `intervalMs` while `active`. */
export function usePolling(active: boolean, fn: () => void, intervalMs = 2500) {
  const fnRef = useRef(fn)
  fnRef.current = fn
  useEffect(() => {
    if (!active) return
    const id = window.setInterval(() => fnRef.current(), intervalMs)
    return () => window.clearInterval(id)
  }, [active, intervalMs])
}
