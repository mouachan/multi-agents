import { tendersApi } from './tenderApi'
import type { Tender, TenderStatusResponse, TenderDecision, ProcessingStepLog } from '../types/tender'

export interface TenderData {
  tender: Tender
  status: TenderStatusResponse | null
  decision: TenderDecision | null
  logs: ProcessingStepLog[]
}

export class TenderService {
  async loadTenderData(tenderId: string): Promise<TenderData> {
    const [tender, status] = await Promise.all([
      tendersApi.getTender(tenderId),
      tendersApi.getTenderStatus(tenderId).catch(() => null)
    ])

    let decision: TenderDecision | null = null
    let logs: ProcessingStepLog[] = []

    if (['processing', 'completed', 'manual_review', 'failed'].includes(tender.status)) {
      try {
        const logsData = await tendersApi.getTenderLogs(tenderId)
        logs = logsData.logs || []
      } catch (err) {
        console.error('Error loading tender logs:', err)
      }
    }

    if (['completed', 'manual_review', 'failed'].includes(tender.status)) {
      try {
        decision = await tendersApi.getTenderDecision(tenderId)
      } catch (err) {
        console.error('Error loading tender decision:', err)
      }
    }

    return { tender, status, decision, logs }
  }

  shouldPoll(tender: Tender): boolean {
    return tender.status === 'processing'
  }

  canProcess(tender: Tender): boolean {
    return tender.status === 'pending' || tender.status === 'failed'
  }

  async processTender(tenderId: string): Promise<void> {
    await tendersApi.processTender(tenderId)
  }
}

export const tenderService = new TenderService()
