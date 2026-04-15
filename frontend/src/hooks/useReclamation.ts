import { useState, useEffect, useCallback } from 'react'
import { postalService, type ReclamationData } from '../services/postalService'
import type { Reclamation, ReclamationStatusResponse, ReclamationDecision, ProcessingStepLog, TrackingEvent } from '../types/reclamation'

export function useReclamation(reclamationId: string | undefined) {
  const [reclamation, setReclamation] = useState<Reclamation | null>(null)
  const [status, setStatus] = useState<ReclamationStatusResponse | null>(null)
  const [decision, setDecision] = useState<ReclamationDecision | null>(null)
  const [logs, setLogs] = useState<ProcessingStepLog[]>([])
  const [tracking, setTracking] = useState<TrackingEvent[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!reclamationId) {
      setError('No reclamation ID provided')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data: ReclamationData = await postalService.loadReclamationData(reclamationId)
      setReclamation(data.reclamation)
      setStatus(data.status)
      setDecision(data.decision)
      setLogs(data.logs)
      setTracking(data.tracking)
    } catch (err) {
      setError('Failed to load reclamation data')
      console.error('Error loading reclamation:', err)
    } finally {
      setLoading(false)
    }
  }, [reclamationId])

  useEffect(() => {
    loadData()
  }, [loadData])

  return { reclamation, status, decision, logs, tracking, loading, error, reload: loadData }
}
