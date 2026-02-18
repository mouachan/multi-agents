import axios from 'axios'
import type {
  Claim,
  ClaimStatusResponse,
  ClaimDecision,
  ClaimStatistics,
  ProcessClaimRequest,
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes timeout for long-running agent processing
})

// Claims API
export const claimsApi = {
  // List claims with pagination
  listClaims: async (page = 1, pageSize = 20, status?: string, userId?: string) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() })
    if (status) params.append('status', status)
    if (userId) params.append('user_id', userId)

    const response = await apiClient.get(`/claims/?${params}`)
    return response.data
  },

  // Get a specific claim
  getClaim: async (claimId: string): Promise<Claim> => {
    const response = await apiClient.get(`/claims/${claimId}`)
    return response.data
  },

  // Process a claim
  processClaim: async (claimId: string, request: ProcessClaimRequest = {}) => {
    const response = await apiClient.post(`/claims/${claimId}/process`, request)
    return response.data
  },

  // Get claim processing status
  getClaimStatus: async (claimId: string): Promise<ClaimStatusResponse> => {
    const response = await apiClient.get(`/claims/${claimId}/status`)
    return response.data
  },

  // Get claim logs
  getClaimLogs: async (claimId: string) => {
    const response = await apiClient.get(`/claims/${claimId}/logs`)
    return response.data
  },

  // Get claim decision
  getClaimDecision: async (claimId: string): Promise<ClaimDecision> => {
    const response = await apiClient.get(`/claims/${claimId}/decision`)
    return response.data
  },

  // Get statistics
  getStatistics: async (): Promise<ClaimStatistics> => {
    const response = await apiClient.get('/claims/statistics/overview')
    return response.data
  },
}

// Review API (HITL)
export const reviewApi = {
  // Submit review action
  submitAction: async (
    claimId: string,
    action: { action: string; comment: string; reviewerId: string; reviewerName: string }
  ) => {
    const response = await apiClient.post(`/review/${claimId}/action`, action)
    return response.data
  },

  // Ask agent a question
  askAgent: async (
    claimId: string,
    question: string,
    reviewerId: string,
    reviewerName: string
  ) => {
    const response = await apiClient.post(`/review/${claimId}/ask-agent`, {
      question,
      reviewer_id: reviewerId,
      reviewer_name: reviewerName,
    })
    return response.data
  },

  // Get review messages
  getMessages: async (claimId: string) => {
    const response = await apiClient.get(`/review/${claimId}/messages`)
    return response.data
  },
}

export default apiClient
