/**
 * Claim Service - Business logic for claims
 *
 * Handles claim processing workflows and decision logic.
 * Separates business logic from UI components.
 */

import { claimsApi } from './api'
import type { Claim, ClaimStatusResponse, ClaimDecision, ProcessingStepLog } from '../types'

export interface ClaimData {
  claim: Claim
  status: ClaimStatusResponse | null
  decision: ClaimDecision | null
  logs: ProcessingStepLog[]
}

export class ClaimService {
  /**
   * Load complete claim data (claim, status, decision, logs)
   */
  async loadClaimData(claimId: string): Promise<ClaimData> {
    const [claim, status] = await Promise.all([
      claimsApi.getClaim(claimId),
      claimsApi.getClaimStatus(claimId).catch(() => null)
    ])

    let decision: ClaimDecision | null = null
    let logs: ProcessingStepLog[] = []

    // Load logs if claim has been processed
    if (['processing', 'completed', 'manual_review', 'failed'].includes(claim.status)) {
      try {
        const logsData = await claimsApi.getClaimLogs(claimId)
        logs = logsData.logs || []
      } catch (err) {
        console.error('Error loading logs:', err)
      }
    }

    // Load decision if processed
    if (['completed', 'manual_review', 'failed'].includes(claim.status)) {
      try {
        decision = await claimsApi.getClaimDecision(claimId)
      } catch (err) {
        console.error('Error loading decision:', err)
      }
    }

    return { claim, status, decision, logs }
  }

  /**
   * Check if claim needs polling (is being processed)
   */
  shouldPoll(claim: Claim): boolean {
    return claim.status === 'processing'
  }

  /**
   * Check if claim can be processed
   */
  canProcess(claim: Claim): boolean {
    return claim.status === 'pending' || claim.status === 'failed'
  }

  /**
   * Check if claim is in manual review
   */
  isManualReview(claim: Claim): boolean {
    return claim.status === 'manual_review'
  }

  /**
   * Check if claim is completed (approved or denied)
   */
  isCompleted(claim: Claim): boolean {
    return claim.status === 'completed' || claim.status === 'failed'
  }

  /**
   * Extract OCR data from processing logs
   */
  extractOcrData(logs: ProcessingStepLog[]): any {
    const ocrStep = logs.find((s) => s.step_name === 'ocr' || s.step_name.includes('ocr'))
    return ocrStep?.output_data?.structured_data?.fields || null
  }

  /**
   * Process a claim
   */
  async processClaim(claimId: string, mode: 'standard' | 'ocr-only' = 'standard'): Promise<void> {
    const skipOcr = false
    const enableRag = mode === 'standard'

    await claimsApi.processClaim(claimId, {
      skip_ocr: skipOcr,
      enable_rag: enableRag
    })
  }
}

// Singleton instance
export const claimService = new ClaimService()
