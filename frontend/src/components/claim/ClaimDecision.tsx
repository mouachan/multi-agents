/**
 * ClaimDecision Component - Displays claim decision with conditional logic
 *
 * Shows:
 * - For manual_review: System Decision + Reviewer Decision sections
 * - For completed/failed: Only System Decision (single card)
 */

import type { Claim, ClaimDecision as Decision } from '../../types'

interface ClaimDecisionProps {
  claim: Claim
  decision: Decision
}

export default function ClaimDecision({ claim, decision }: ClaimDecisionProps) {
  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  const isManualReview = claim.status === 'manual_review'

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Claim Decision</h3>

      {isManualReview ? (
        /* Manual Review: Show both System and Reviewer sections */
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          {/* System Decision */}
          <div className="border border-gray-200 rounded-lg p-4">
            <p className="text-sm font-medium text-gray-500 mb-2">🤖 System Decision (Initial)</p>
            <p
              className={`text-3xl font-bold ${
                decision.initial_decision === 'approve'
                  ? 'text-green-600'
                  : decision.initial_decision === 'deny'
                  ? 'text-red-600'
                  : 'text-orange-600'
              }`}
            >
              {decision.initial_decision?.toUpperCase() || 'N/A'}
            </p>
            {decision.initial_confidence !== undefined && decision.initial_confidence !== null && (
              <p className="text-sm text-gray-600 mt-2">
                Confidence: <span className="font-medium">{(decision.initial_confidence * 100).toFixed(1)}%</span>
              </p>
            )}
            {decision.initial_decided_at && (
              <p className="text-xs text-gray-500 mt-1">{formatDate(decision.initial_decided_at)}</p>
            )}
          </div>

          {/* Reviewer Decision */}
          <div
            className={`border-2 rounded-lg p-4 ${
              decision.final_decision
                ? decision.final_decision === 'approve'
                  ? 'border-green-500 bg-green-50'
                  : 'border-red-500 bg-red-50'
                : 'border-orange-300 bg-orange-50'
            }`}
          >
            <p className="text-sm font-medium text-gray-700 mb-2">👤 Final Decision (Reviewer)</p>
            {decision.final_decision ? (
              <>
                <p
                  className={`text-3xl font-bold ${
                    decision.final_decision === 'approve'
                      ? 'text-green-700'
                      : decision.final_decision === 'deny'
                      ? 'text-red-700'
                      : 'text-orange-700'
                  }`}
                >
                  {decision.final_decision.toUpperCase()}
                </p>
                {decision.final_decision_by_name && (
                  <p className="text-sm text-gray-700 mt-2">
                    By: <span className="font-medium">{decision.final_decision_by_name}</span>
                  </p>
                )}
                {decision.final_decision_at && (
                  <p className="text-xs text-gray-600 mt-1">{formatDate(decision.final_decision_at)}</p>
                )}
                {decision.final_decision_notes && (
                  <p className="text-xs text-gray-700 mt-2 italic">"{decision.final_decision_notes}"</p>
                )}
              </>
            ) : (
              <p className="text-lg text-orange-600 font-medium">⚠️ Awaiting manual review...</p>
            )}
          </div>
        </div>
      ) : (
        /* Completed/Failed: Show only System Decision */
        <div className="mb-6">
          <div
            className={`border-2 rounded-lg p-6 ${
              decision.initial_decision === 'approve'
                ? 'border-green-500 bg-green-50'
                : decision.initial_decision === 'deny'
                ? 'border-red-500 bg-red-50'
                : 'border-gray-300 bg-gray-50'
            }`}
          >
            <p className="text-sm font-medium text-gray-500 mb-2">🤖 System Decision</p>
            <p
              className={`text-4xl font-bold ${
                decision.initial_decision === 'approve'
                  ? 'text-green-600'
                  : decision.initial_decision === 'deny'
                  ? 'text-red-600'
                  : 'text-gray-600'
              }`}
            >
              {decision.initial_decision?.toUpperCase() || 'N/A'}
            </p>
            {decision.initial_confidence !== undefined && decision.initial_confidence !== null && (
              <p className="text-sm text-gray-600 mt-2">
                Confidence: <span className="font-medium">{(decision.initial_confidence * 100).toFixed(1)}%</span>
              </p>
            )}
            {decision.initial_decided_at && (
              <p className="text-xs text-gray-500 mt-1">Decided at: {formatDate(decision.initial_decided_at)}</p>
            )}

            {/* Show final decision if reviewer overrode */}
            {decision.final_decision && (
              <div className="mt-4 pt-4 border-t border-gray-300">
                <p className="text-xs text-gray-600 mb-1">Reviewer Override</p>
                <p
                  className={`text-2xl font-bold ${
                    decision.final_decision === 'approve'
                      ? 'text-green-700'
                      : decision.final_decision === 'deny'
                      ? 'text-red-700'
                      : 'text-orange-700'
                  }`}
                >
                  {decision.final_decision.toUpperCase()}
                </p>
                {decision.final_decision_by_name && (
                  <p className="text-sm text-gray-700 mt-1">By: {decision.final_decision_by_name}</p>
                )}
                {decision.final_decision_notes && (
                  <p className="text-sm text-gray-700 mt-1 italic">"{decision.final_decision_notes}"</p>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Estimated Coverage */}
      {decision.relevant_policies?.estimated_coverage && (
        <div className="mb-6">
          <p className="text-sm text-gray-600">Estimated Coverage</p>
          <p className="text-2xl font-bold mt-1 text-blue-600">
            ${Number(decision.relevant_policies.estimated_coverage).toLocaleString()}
          </p>
        </div>
      )}

      {/* System Reasoning */}
      <div className="mt-6">
        <p className="text-sm text-gray-600 mb-2">System Reasoning</p>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-gray-900">{decision.initial_reasoning || decision.reasoning || 'N/A'}</p>
        </div>
      </div>

      {decision.requires_manual_review && isManualReview && (
        <div className="mt-4 p-4 bg-orange-50 border border-orange-200 rounded-lg">
          <p className="text-orange-800 font-medium">⚠️ This claim requires manual review</p>
        </div>
      )}

      {decision.llm_model && (
        <div className="mt-4">
          <p className="text-sm text-gray-600">LLM Model: {decision.llm_model}</p>
        </div>
      )}
    </div>
  )
}
