import { claimsApi, postalApi, tendersApi, type PiiDetection } from '../services/api'
import type { Claim, ClaimDecision, ClaimStatusResponse, ProcessingStepLog } from '../types'
import type { Tender, TenderDecision, TenderStatusResponse } from '../types/tender'
import type { Reclamation, ReclamationDecision, ReclamationStatusResponse, TrackingEvent } from '../types/reclamation'
import { usePolling, useResource } from './useResource'

const PROCESSED = ['processing', 'completed', 'manual_review', 'failed', 'denied', 'rejected', 'escalated']
const DECIDED = ['completed', 'manual_review', 'failed', 'denied', 'rejected', 'escalated']
const optional = <T,>(p: Promise<T>): Promise<T | null> => p.catch(() => null)

export interface ClaimData {
  claim: Claim
  status: ClaimStatusResponse | null
  decision: ClaimDecision | null
  logs: ProcessingStepLog[]
  detections: PiiDetection[]
}

export function useClaimData(id?: string) {
  const res = useResource<ClaimData>(async () => {
    const claim = await claimsApi.get(id!)
    const [status, logs, decision, detections] = await Promise.all([
      optional(claimsApi.status(id!)),
      PROCESSED.includes(claim.status) ? claimsApi.logs(id!).catch(() => []) : Promise.resolve([]),
      DECIDED.includes(claim.status) ? optional(claimsApi.decision(id!)) : Promise.resolve(null),
      claimsApi.guardrails(id!).catch(() => []),
    ])
    return { claim, status, decision, logs, detections }
  }, [id])
  usePolling(res.data?.claim.status === 'processing', res.reload)
  return res
}

export interface TenderData {
  tender: Tender
  status: TenderStatusResponse | null
  decision: TenderDecision | null
  logs: ProcessingStepLog[]
}

export function useTenderData(id?: string) {
  const res = useResource<TenderData>(async () => {
    const tender = await tendersApi.get(id!)
    const [status, logs, decision] = await Promise.all([
      optional(tendersApi.status(id!)),
      PROCESSED.includes(tender.status) ? tendersApi.logs(id!).catch(() => []) : Promise.resolve([]),
      DECIDED.includes(tender.status) ? optional(tendersApi.decision(id!)) : Promise.resolve(null),
    ])
    return { tender, status, decision, logs }
  }, [id])
  usePolling(res.data?.tender.status === 'processing', res.reload)
  return res
}

export interface ReclamationData {
  reclamation: Reclamation
  status: ReclamationStatusResponse | null
  decision: ReclamationDecision | null
  logs: ProcessingStepLog[]
  tracking: TrackingEvent[]
}

export function useReclamationData(id?: string) {
  const res = useResource<ReclamationData>(async () => {
    const reclamation = await postalApi.get(id!)
    const [status, logs, decision, tracking] = await Promise.all([
      optional(postalApi.status(id!)),
      PROCESSED.includes(reclamation.status) ? postalApi.logs(id!).catch(() => []) : Promise.resolve([]),
      DECIDED.includes(reclamation.status) ? optional(postalApi.decision(id!)) : Promise.resolve(null),
      postalApi.tracking(id!).catch(() => []),
    ])
    return { reclamation, status, decision, logs, tracking }
  }, [id])
  usePolling(res.data?.reclamation.status === 'processing', res.reload)
  return res
}
