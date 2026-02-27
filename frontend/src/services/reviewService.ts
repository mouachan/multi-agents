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

}

// Singleton instance
export const reviewService = new ReviewService()
