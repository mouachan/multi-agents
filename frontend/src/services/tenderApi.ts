import axios from 'axios'
import type {
  Tender,
  TenderStatusResponse,
  TenderDecision,
  TenderStatistics,
} from '../types/tender'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000,
})

export const tendersApi = {
  listTenders: async (page = 1, pageSize = 20, status?: string) => {
    const params = new URLSearchParams({ page: page.toString(), page_size: pageSize.toString() })
    if (status) params.append('status', status)
    const response = await apiClient.get(`/tenders/?${params}`)
    return response.data
  },

  getTender: async (tenderId: string): Promise<Tender> => {
    const response = await apiClient.get(`/tenders/${tenderId}`)
    return response.data
  },

  processTender: async (tenderId: string) => {
    const response = await apiClient.post(`/tenders/${tenderId}/process`, {})
    return response.data
  },

  getTenderStatus: async (tenderId: string): Promise<TenderStatusResponse> => {
    const response = await apiClient.get(`/tenders/${tenderId}/status`)
    return response.data
  },

  getTenderLogs: async (tenderId: string) => {
    const response = await apiClient.get(`/tenders/${tenderId}/logs`)
    return response.data
  },

  getTenderDecision: async (tenderId: string): Promise<TenderDecision> => {
    const response = await apiClient.get(`/tenders/${tenderId}/decision`)
    return response.data
  },

  getStatistics: async (): Promise<TenderStatistics> => {
    const response = await apiClient.get('/tenders/statistics/overview')
    return response.data
  },
}
