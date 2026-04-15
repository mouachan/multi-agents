import axios from 'axios'
import type {
  Reclamation,
  ReclamationStatusResponse,
  ReclamationDecision,
  ReclamationStatistics,
  TrackingEvent,
} from '../types/reclamation'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000,
})

export const postalApi = {
  listReclamations: async (page = 1, pageSize = 20, status?: string) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() })
    if (status) params.append('status', status)
    const response = await apiClient.get(`/postal/?${params}`)
    return response.data
  },

  getReclamation: async (reclamationId: string): Promise<Reclamation> => {
    const response = await apiClient.get(`/postal/${reclamationId}`)
    return response.data
  },

  createReclamation: async (data: Partial<Reclamation>) => {
    const response = await apiClient.post('/postal/', data)
    return response.data
  },

  processReclamation: async (reclamationId: string) => {
    const response = await apiClient.post(`/postal/${reclamationId}/process`, {})
    return response.data
  },

  getReclamationStatus: async (reclamationId: string): Promise<ReclamationStatusResponse> => {
    const response = await apiClient.get(`/postal/${reclamationId}/status`)
    return response.data
  },

  getReclamationDecision: async (reclamationId: string): Promise<ReclamationDecision> => {
    const response = await apiClient.get(`/postal/${reclamationId}/decision`)
    return response.data
  },

  getReclamationLogs: async (reclamationId: string) => {
    const response = await apiClient.get(`/postal/${reclamationId}/logs`)
    return response.data
  },

  getStatistics: async (): Promise<ReclamationStatistics> => {
    const response = await apiClient.get('/postal/statistics/overview')
    return response.data
  },

  getReclamationTracking: async (reclamationId: string): Promise<TrackingEvent[]> => {
    const response = await apiClient.get(`/postal/${reclamationId}/tracking`)
    return response.data
  },
}
