/**
 * useClaim Hook - Manages claim data fetching and state
 */

import { useState, useEffect, useCallback } from 'react'
import { claimService, type ClaimData } from '../services/claimService'
import type { Claim, ClaimStatusResponse, ClaimDecision, ProcessingStepLog } from '../types'

export function useClaim(claimId: string | undefined) {
  const [claim, setClaim] = useState<Claim | null>(null)
  const [status, setStatus] = useState<ClaimStatusResponse | null>(null)
  const [decision, setDecision] = useState<ClaimDecision | null>(null)
  const [logs, setLogs] = useState<ProcessingStepLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!claimId) {
      setError('No claim ID provided')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)

      const data: ClaimData = await claimService.loadClaimData(claimId)

      setClaim(data.claim)
      setStatus(data.status)
      setDecision(data.decision)
      setLogs(data.logs)
    } catch (err) {
      setError('Failed to load claim data')
      console.error('Error loading claim:', err)
    } finally {
      setLoading(false)
    }
  }, [claimId])

  useEffect(() => {
    loadData()
  }, [loadData])

  return {
    claim,
    status,
    decision,
    logs,
    loading,
    error,
    reload: loadData
  }
}
