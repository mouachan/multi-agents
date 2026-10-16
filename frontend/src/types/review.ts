/** Human review of the cases the agent hands over to a person (backend/app/services/review.py). */
import type { Case, Decision, Domain } from './case'

/** A case waiting for a reviewer (review inbox) */
export interface InboxItem {
  domain: Domain
  id: string
  number: string
  waiting_since?: string | null
  confidence?: number | null
  /** what the agent would choose if it had to */
  suggestion?: string | null
  /** the main reason it handed the case over */
  reason: string
}

/** What the agent concluded and why it needs a human */
export interface AgentView {
  decision: string
  confidence?: number | null
  reasoning?: string | null
  suggestion?: string | null
  reasons: string[]
  checks: string[]
}

export type JournalEntry =
  | { type: 'question'; question: string; answer: string; by: string; at: string; trace?: { mlflow_url?: string | null } }
  | { type: 'decision'; decision: string; agent_decision?: string; justification?: string; by: string; at: string }

export interface ReviewBrief {
  case: Case
  awaiting_review: boolean
  agent: AgentView
  /** what a reviewer can decide, and the status the case then gets */
  choices: { decision: string; status: string }[]
  decision: Decision
  journal: JournalEntry[]
}
