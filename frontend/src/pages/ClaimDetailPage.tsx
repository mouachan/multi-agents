/**
 * ClaimDetailPage - Refactored v1.5
 *
 * Clean architecture with separation of concerns:
 * - Hooks handle data fetching and state
 * - Services handle business logic
 * - Components handle UI rendering
 */

import { useParams, Link } from 'react-router-dom'
import { useClaim } from '../hooks/useClaim'
import { useClaimPolling } from '../hooks/useClaimPolling'
import ClaimHeader from '../components/claim/ClaimHeader'
import ClaimActions from '../components/claim/ClaimActions'
import ClaimDecision from '../components/claim/ClaimDecision'
import ProcessingSteps from '../components/claim/ProcessingSteps'
import ReviewChatPanel from '../components/ReviewChatPanel'
import GuardrailsAlert from '../components/claim/GuardrailsAlert'

export default function ClaimDetailPage() {
  const { claimId } = useParams<{ claimId: string }>()

  // Custom hook manages all claim data and state
  const { claim, status, decision, logs, loading, error, reload } = useClaim(claimId)

  // Custom hook manages polling for processing claims
  useClaimPolling(claim, {
    enabled: true,
    interval: 2000,
    onPoll: reload
  })

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (error || !claim) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Claim not found'}</p>
        <Link to="/claims" className="text-blue-600 hover:text-blue-800 mt-2 inline-block">
          ← Back to Claims
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Navigation */}
      <Link to="/claims" className="text-blue-600 hover:text-blue-800 flex items-center">
        <svg className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Back to Claims
      </Link>

      {/* Claim Header */}
      <ClaimHeader claim={claim} logs={logs} />

      {/* Guardrails PII Detections */}
      <GuardrailsAlert claimId={claim.id} />

      {/* Process Actions */}
      <ClaimActions claim={claim} onProcessStart={reload} />

      {/* Processing Steps */}
      <ProcessingSteps claim={claim} status={status} logs={logs} />

      {/* Decision */}
      {decision && <ClaimDecision claim={claim} decision={decision} />}

      {/* Human-in-the-Loop Review Panel */}
      {claim.status === 'manual_review' && (
        <div className="bg-white shadow rounded-lg p-6">
          <ReviewChatPanel
            claimId={claim.id}
            reviewerId={`reviewer_${Date.now()}`}
            reviewerName="Review Agent"
            onActionSubmitted={(action) => {
              console.log('Action submitted:', action)
              reload()
            }}
          />
        </div>
      )}
    </div>
  )
}
