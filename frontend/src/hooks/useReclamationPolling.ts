import { useEffect, useRef } from 'react'
import type { Reclamation } from '../types/reclamation'

interface UseReclamationPollingOptions {
  enabled: boolean
  interval?: number
  onPoll: () => void
}

export function useReclamationPolling(reclamation: Reclamation | null, options: UseReclamationPollingOptions) {
  const { enabled, interval = 2000, onPoll } = options
  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled || !reclamation || reclamation.status !== 'processing') {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    intervalRef.current = setInterval(onPoll, interval) as unknown as number

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, reclamation?.status, interval, onPoll])

  return { isPolling: intervalRef.current !== null }
}
