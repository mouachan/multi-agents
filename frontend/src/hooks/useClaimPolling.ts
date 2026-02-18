/**
 * useClaimPolling Hook - Manages automatic polling for processing claims
 */

import { useEffect, useRef } from 'react'
import type { Claim } from '../types'

interface UseClaimPollingOptions {
  enabled: boolean
  interval?: number
  onPoll: () => void
}

export function useClaimPolling(claim: Claim | null, options: UseClaimPollingOptions) {
  const { enabled, interval = 2000, onPoll } = options
  const intervalRef = useRef<number | null>(null)

  useEffect(() => {
    // Only poll if enabled and claim is processing
    if (!enabled || !claim || claim.status !== 'processing') {
      // Clear any existing interval
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
      return
    }

    // Start polling
    intervalRef.current = setInterval(onPoll, interval) as unknown as number

    // Cleanup on unmount or when dependencies change
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current)
        intervalRef.current = null
      }
    }
  }, [enabled, claim?.status, interval, onPoll])

  return {
    isPolling: intervalRef.current !== null
  }
}
