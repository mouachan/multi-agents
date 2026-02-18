import { useEffect, useRef } from 'react'
import type { Tender } from '../types/tender'

interface UseTenderPollingOptions {
  enabled: boolean
  interval?: number
  onPoll: () => void
}

export function useTenderPolling(tender: Tender | null, options: UseTenderPollingOptions) {
  const { enabled, interval = 2000, onPoll } = options
  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    if (!enabled || !tender || tender.status !== 'processing') {
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
  }, [enabled, tender?.status, interval, onPoll])

  return { isPolling: intervalRef.current !== null }
}
