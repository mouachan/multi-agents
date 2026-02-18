import { useState, useEffect, useCallback } from 'react'
import { tenderService, type TenderData } from '../services/tenderService'
import type { Tender, TenderStatusResponse, TenderDecision, ProcessingStepLog } from '../types/tender'

export function useTender(tenderId: string | undefined) {
  const [tender, setTender] = useState<Tender | null>(null)
  const [status, setStatus] = useState<TenderStatusResponse | null>(null)
  const [decision, setDecision] = useState<TenderDecision | null>(null)
  const [logs, setLogs] = useState<ProcessingStepLog[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadData = useCallback(async () => {
    if (!tenderId) {
      setError('No tender ID provided')
      setLoading(false)
      return
    }

    try {
      setLoading(true)
      setError(null)
      const data: TenderData = await tenderService.loadTenderData(tenderId)
      setTender(data.tender)
      setStatus(data.status)
      setDecision(data.decision)
      setLogs(data.logs)
    } catch (err) {
      setError('Failed to load tender data')
      console.error('Error loading tender:', err)
    } finally {
      setLoading(false)
    }
  }, [tenderId])

  useEffect(() => {
    loadData()
  }, [loadData])

  return { tender, status, decision, logs, loading, error, reload: loadData }
}
