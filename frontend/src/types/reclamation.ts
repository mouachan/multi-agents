// Type definitions for Reclamation (Courrier & Colis) module

export type ReclamationStatus = 'pending' | 'processing' | 'completed' | 'rejected' | 'manual_review' | 'escalated'

export type ReclamationType = 'colis_endommage' | 'colis_perdu' | 'non_livre' | 'mauvaise_adresse' | 'vol_point_relais' | 'retard_livraison'

export type ReclamationDecisionType = 'rembourser' | 'reexpedier' | 'rejeter' | 'escalader'

export interface Reclamation {
  id: string
  reclamation_number: string
  numero_suivi: string
  reclamation_type: ReclamationType
  client_nom: string
  client_email: string
  client_telephone?: string
  description: string
  valeur_declaree?: number
  document_path?: string
  status: ReclamationStatus
  submitted_at: string
  processed_at?: string
  total_processing_time_ms?: number
  is_archived: boolean
  metadata?: Record<string, any>
  agent_logs?: AgentLogEntry[]
  created_at: string
}

export interface AgentLogEntry {
  type: 'reviewer_question' | 'agent_answer' | 'approve' | 'reject' | 'request_info' | 'comment'
  timestamp: string
  reviewer_id?: string
  reviewer_name?: string
  message: string
}

export interface ReclamationDecision {
  id: string
  reclamation_id: string
  decision: ReclamationDecisionType
  confidence?: number
  reasoning?: string
  initial_decision: ReclamationDecisionType
  initial_confidence?: number
  initial_reasoning?: string
  llm_model?: string
  requires_manual_review: boolean
  decided_at: string
}

export interface TrackingEvent {
  id: string
  numero_suivi: string
  event_type: string
  event_date: string
  location?: string
  detail?: string
  code_postal?: string
  is_final: boolean
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

export interface ReclamationStatusResponse {
  reclamation_id: string
  status: ReclamationStatus
  current_step?: string
  progress_percentage: number
  processing_steps: ProcessingStepLog[]
}

export interface ReclamationStatistics {
  total: number
  by_status: Record<string, number>
  by_type: Record<string, number>
  avg_processing_time_ms?: number
}
