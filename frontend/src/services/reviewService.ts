/**
 * Review Service - Business logic for Human-in-the-Loop reviews
 *
 * Handles review actions and agent interactions.
 */

import { reviewApi } from './api'

export interface ReviewAction {
  action: 'approve' | 'reject' | 'comment' | 'request_info'
  comment: string
  reviewerId: string
  reviewerName: string
}

export class ReviewService {
  /**
   * Submit a review action (approve/reject/comment)
   */
  async submitAction(claimId: string, action: ReviewAction): Promise<void> {
    await reviewApi.submitAction(claimId, action)
  }

  /**
   * Ask the agent a question
   */
  async askAgent(
    claimId: string,
    question: string,
    reviewerId: string,
    reviewerName: string
  ): Promise<string> {
    const response = await reviewApi.askAgent(claimId, question, reviewerId, reviewerName)
    return response.answer
  }

  /**
   * Check if action is final (approve/reject)
   */
  isFinalAction(action: string): boolean {
    return action === 'approve' || action === 'reject'
  }

  /**
   * Get action display label
   */
  getActionLabel(action: string): string {
    const labels: Record<string, string> = {
      approve: 'Approve',
      reject: 'Reject',
      comment: 'Add Comment',
      request_info: 'Request Info'
    }
    return labels[action] || action
  }
}

// Singleton instance
export const reviewService = new ReviewService()
