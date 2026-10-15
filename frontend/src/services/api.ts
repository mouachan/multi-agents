import { http } from './http'
import type {
  Claim,
  ClaimDecision,
  ClaimStatistics,
  ClaimStatusResponse,
  ProcessClaimRequest,
  ProcessingStepLog,
} from '../types'
import type { Tender, TenderDecision, TenderStatistics, TenderStatusResponse } from '../types/tender'
import type {
  Reclamation,
  ReclamationDecision,
  ReclamationStatistics,
  ReclamationStatusResponse,
  TrackingEvent,
} from '../types/reclamation'
import type { SandboxDemoResult, SandboxInfo, SandboxScenario } from '../types/sandbox'

export const API_BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

/** The lists are small (tens of rows): load them in one page, filter/sort client-side. */
const ALL = { page: 1, page_size: 100 }

export interface PiiDetection {
  id: string
  detection_type: string
  severity?: string
  action_taken?: string
  detected_at?: string
  record_metadata?: Record<string, any>
}

export const claimsApi = {
  list: async (): Promise<Claim[]> => (await http.get('/claims/', { params: ALL })).data.claims ?? [],
  get: async (id: string): Promise<Claim> => (await http.get(`/claims/${id}`)).data,
  process: async (id: string, request: ProcessClaimRequest = { skip_ocr: false, enable_rag: true }) =>
    (await http.post(`/claims/${id}/process`, request)).data,
  status: async (id: string): Promise<ClaimStatusResponse> => (await http.get(`/claims/${id}/status`)).data,
  logs: async (id: string): Promise<ProcessingStepLog[]> => (await http.get(`/claims/${id}/logs`)).data.logs ?? [],
  decision: async (id: string): Promise<ClaimDecision> => (await http.get(`/claims/${id}/decision`)).data,
  statistics: async (): Promise<ClaimStatistics> => (await http.get('/claims/statistics/overview')).data,
  guardrails: async (id: string): Promise<PiiDetection[]> =>
    (await http.get(`/claims/${id}/guardrails`)).data.detections ?? [],
  documentUrl: (id: string, lang: string) => `${API_BASE_URL}/claims/documents/${id}/view?lang=${lang}`,
}

export const tendersApi = {
  list: async (): Promise<Tender[]> => (await http.get('/tenders/', { params: ALL })).data.tenders ?? [],
  get: async (id: string): Promise<Tender> => (await http.get(`/tenders/${id}`)).data,
  process: async (id: string) => (await http.post(`/tenders/${id}/process`, {})).data,
  status: async (id: string): Promise<TenderStatusResponse> => (await http.get(`/tenders/${id}/status`)).data,
  logs: async (id: string): Promise<ProcessingStepLog[]> => (await http.get(`/tenders/${id}/logs`)).data.logs ?? [],
  decision: async (id: string): Promise<TenderDecision> => (await http.get(`/tenders/${id}/decision`)).data,
  statistics: async (): Promise<TenderStatistics> => (await http.get('/tenders/statistics/overview')).data,
  documentUrl: (id: string, lang: string) => `${API_BASE_URL}/tenders/documents/${id}/view?lang=${lang}`,
}

export const postalApi = {
  list: async (): Promise<Reclamation[]> => (await http.get('/postal/', { params: ALL })).data.items ?? [],
  get: async (id: string): Promise<Reclamation> => (await http.get(`/postal/${id}`)).data,
  process: async (id: string) => (await http.post(`/postal/${id}/process`, {})).data,
  status: async (id: string): Promise<ReclamationStatusResponse> => (await http.get(`/postal/${id}/status`)).data,
  logs: async (id: string): Promise<ProcessingStepLog[]> => (await http.get(`/postal/${id}/logs`)).data.logs ?? [],
  decision: async (id: string): Promise<ReclamationDecision> => (await http.get(`/postal/${id}/decision`)).data,
  statistics: async (): Promise<ReclamationStatistics> => (await http.get('/postal/statistics/overview')).data,
  tracking: async (id: string): Promise<TrackingEvent[]> => (await http.get(`/postal/${id}/tracking`)).data,
  documentUrl: (id: string, lang: string) => `${API_BASE_URL}/postal/${id}/document/view?lang=${lang}`,
}

export const reviewApi = {
  submitAction: async (
    entityType: string,
    entityId: string,
    action: { action: string; comment: string; reviewerId: string; reviewerName: string },
  ) => (await http.post(`/review/${entityType}/${entityId}/action`, action)).data,

  askAgent: async (entityType: string, entityId: string, question: string, reviewerId: string, reviewerName: string) =>
    (await http.post(`/review/${entityType}/${entityId}/ask-agent`, {
      question, reviewer_id: reviewerId, reviewer_name: reviewerName,
    })).data,
}

export interface DatabaseStats {
  users: number
  contracts: number
  claims_by_status: Record<string, number>
  claims_total: number
  knowledge_base: number
  knowledge_base_embeddings: string
  claim_documents_embeddings: string
}

export const sandboxApi = {
  info: async (): Promise<SandboxInfo> => (await http.get('/sandbox/policy')).data,
  demo: async (scenario: SandboxScenario): Promise<SandboxDemoResult> =>
    (await http.post(`/sandbox/demo/${scenario}`)).data,
}

export const adminApi = {
  databaseStats: async (): Promise<DatabaseStats> => (await http.get('/admin/database-stats')).data.data,
  resetDatabase: async () => (await http.post('/admin/reset-database')).data,
}
