import { postalApi } from './postalApi'
import type { Reclamation, ReclamationStatusResponse, ReclamationDecision, ProcessingStepLog, TrackingEvent } from '../types/reclamation'

export interface ReclamationData {
  reclamation: Reclamation
  status: ReclamationStatusResponse | null
  decision: ReclamationDecision | null
  logs: ProcessingStepLog[]
  tracking: TrackingEvent[]
}

export class PostalService {
  async loadReclamationData(reclamationId: string): Promise<ReclamationData> {
    const [reclamation, status] = await Promise.all([
      postalApi.getReclamation(reclamationId),
      postalApi.getReclamationStatus(reclamationId).catch(() => null)
    ])

    let decision: ReclamationDecision | null = null
    let logs: ProcessingStepLog[] = []
    let tracking: TrackingEvent[] = []

    // Load logs if reclamation has been processed
    if (['processing', 'completed', 'rejected', 'manual_review', 'escalated'].includes(reclamation.status)) {
      try {
        const logsData = await postalApi.getReclamationLogs(reclamationId)
        logs = logsData.logs || []
      } catch (err) {
        console.error('Error loading reclamation logs:', err)
      }
    }

    // Load decision if processed
    if (['completed', 'rejected', 'manual_review', 'escalated'].includes(reclamation.status)) {
      try {
        decision = await postalApi.getReclamationDecision(reclamationId)
      } catch (err) {
        console.error('Error loading reclamation decision:', err)
      }
    }

    // Load tracking events
    try {
      tracking = await postalApi.getReclamationTracking(reclamationId)
    } catch (err) {
      console.error('Error loading tracking events:', err)
    }

    return { reclamation, status, decision, logs, tracking }
  }

  canProcess(reclamation: Reclamation): boolean {
    return reclamation.status === 'pending' || reclamation.status === 'rejected'
  }

  async processReclamation(reclamationId: string): Promise<void> {
    await postalApi.processReclamation(reclamationId)
  }
}

export const postalService = new PostalService()
