// Type definitions for Tender (Appels d'Offres) module

export type TenderStatus = 'pending' | 'processing' | 'completed' | 'failed' | 'manual_review'

export type TenderDecisionType = 'go' | 'no_go' | 'a_approfondir'

export interface Tender {
  id: string
  tender_number: string
  entity_id: string
  tender_type?: string
  maitre_ouvrage?: string
  objet_marche?: string
  montant_estime?: number
  delai_execution?: string
  date_limite_reponse?: string
  document_path: string
  status: TenderStatus
  submitted_at: string
  processed_at?: string
  total_processing_time_ms?: number
  metadata?: Record<string, any>
  agent_logs?: AgentLogEntry[]
  created_at: string
  updated_at: string
}

export interface AgentLogEntry {
  type: 'reviewer_question' | 'agent_answer' | 'approve' | 'reject' | 'request_info' | 'comment'
  timestamp: string
  reviewer_id?: string
  reviewer_name?: string
  message: string
}

export interface TenderDecision {
  id: string
  tender_id: string
  initial_decision: TenderDecisionType
  initial_confidence?: number
  initial_reasoning?: string
  initial_decided_at?: string
  final_decision?: TenderDecisionType
  final_decision_by?: string
  final_decision_by_name?: string
  final_decision_at?: string
  final_decision_notes?: string
  decision: TenderDecisionType
  confidence?: number
  reasoning?: string
  risk_analysis?: {
    technical?: string
    financial?: string
    resource?: string
    competition?: string
  }
  similar_references?: any[]
  historical_ao_analysis?: Record<string, any>
  internal_capabilities?: Record<string, any>
  strengths?: string[]
  weaknesses?: string[]
  win_probability_estimate?: number
  estimated_margin_percentage?: number
  recommended_actions?: string[]
  llm_model?: string
  requires_manual_review: boolean
  decided_at: string
}

export interface ProcessingStepLog {
  step_name: string
  agent_name: string
  status: string
  duration_ms?: number | null
  started_at?: string | null
  completed_at?: string | null
  output_data?: Record<string, any>
  error_message?: string | null
}

export interface TenderStatusResponse {
  tender_id: string
  status: TenderStatus
  current_step?: string
  progress_percentage: number
  processing_steps: ProcessingStepLog[]
}

export interface TenderStatistics {
  total_tenders: number
  pending_tenders: number
  processing_tenders: number
  completed_tenders: number
  failed_tenders: number
  manual_review_tenders: number
  average_processing_time_ms?: number
}
