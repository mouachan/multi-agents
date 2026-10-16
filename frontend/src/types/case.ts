/**
 * Cases of the business domains, as the backend API returns them (backend/app/services/cases.py and
 * decisions.py). Every domain has the same shape; a case also carries the columns of its own domain
 * (claim_type, tender_number, numero_suivi...), read through `field()`.
 */

/** A business domain = one A2A agent (claims-agent, tenders-agent, postal-agent) */
export type Domain = 'claims' | 'tenders' | 'postal'

export interface ProcessingStep {
  step_name: string
  status: 'completed' | 'failed' | string
  duration_ms?: number | null
  output_data?: Record<string, any> | null
  error_message?: string | null
}

/** A fact the reviewer can rely on: a label key (review.facts.<key>), a value, a unit */
export interface Fact {
  key: string
  value: string | number | boolean
  unit?: string
}

/** A record related to the case: precedent, reference, capability, contract... */
export interface EvidenceItem {
  title: string
  detail?: string
  badge?: string | null
  score?: number | null
}

/** Facts of a processing, taken from the agent's tool outputs without any LLM (domain's evidence()) */
export interface EvidenceSection {
  key: string
  facts: Fact[]
  items: EvidenceItem[]
}

export interface TraceLink {
  mlflow_trace_id?: string | null
  mlflow_url?: string | null
}

export interface Case {
  id: string
  domain: Domain
  number: string
  status: string
  submitted_at?: string | null
  processed_at?: string | null
  total_processing_time_ms?: number | null
  metadata: Record<string, any>
  processing_steps: ProcessingStep[]
  evidence: EvidenceSection[]
  trace?: TraceLink | null
  /** the domain's own columns (claim_type, user_name, tender_type, numero_suivi, client_nom...) */
  [column: string]: any
}

export interface Decision {
  id: string
  /** the current decision: the reviewer's when there is one, else the agent's */
  decision: string
  confidence?: number | null
  reasoning?: string | null
  reasoning_en?: string | null
  decided_at?: string | null
  llm_model?: string | null
  requires_manual_review: boolean
  agent: { decision: string; confidence?: number | null; reasoning?: string | null; decided_at?: string | null }
  reviewer: null | { decision: string; user: string; name?: string; decided_at: string; justification?: string | null }
  review: { reasons?: string[]; checks?: string[]; suggestion?: string }
}

export interface Statistics {
  total: number
  by_status: Record<string, number>
  average_processing_time_ms?: number | null
}

export interface TrackingEvent {
  id: string
  event_type: string
  event_date: string
  location?: string | null
  detail?: string | null
  code_postal?: string | null
  is_final?: boolean
  metadata?: Record<string, any>
}

/** A type of personal data found in a claim (never the value itself) */
export interface PersonalDataFinding {
  id: string
  detected_at?: string
  detection_type: string
  count?: number
  source_step?: string
}
