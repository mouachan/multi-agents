/**
 * StepOutputDisplay - Business-friendly display for processing step outputs
 *
 * Renders step output data in a user-friendly format based on step type.
 * Handles both rich data (from real-time processing) and summary data (from saved decisions).
 */

interface StepOutputDisplayProps {
  stepName: string
  outputData: any
}

/** Human-readable step labels */
const STEP_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  document_ocr: { label: 'Document Analysis', icon: '1', color: 'blue' },
  ocr_document: { label: 'Document Analysis (OCR)', icon: '1', color: 'blue' },
  retrieve_user_info: { label: 'User & Contract Info', icon: '2', color: 'indigo' },
  retrieve_similar_claims: { label: 'Similar Claims', icon: '3', color: 'purple' },
  search_knowledge_base: { label: 'Knowledge Base Search', icon: '4', color: 'amber' },
  claim_analysis: { label: 'Risk Assessment', icon: '2', color: 'indigo' },
  tender_analysis: { label: 'Go/No-Go Evaluation', icon: '2', color: 'indigo' },
  decision: { label: 'Final Decision', icon: '5', color: 'emerald' },
}

export default function StepOutputDisplay({ stepName, outputData }: StepOutputDisplayProps) {
  if (!outputData) return null

  const step = stepName.toLowerCase()

  // Decision step — show recommendation, confidence bar, and reasoning
  if (step.includes('decision')) {
    const recommendation = outputData.recommendation
    const confidence = outputData.confidence
    const reasoning = outputData.reasoning

    if (!recommendation && !confidence && !reasoning) {
      return <StepDescription description={outputData.description} />
    }

    const recConfig: Record<string, { label: string; bg: string; text: string }> = {
      approve: { label: 'Approved', bg: 'bg-green-100', text: 'text-green-800' },
      deny: { label: 'Denied', bg: 'bg-red-100', text: 'text-red-800' },
      manual_review: { label: 'Manual Review Required', bg: 'bg-amber-100', text: 'text-amber-800' },
      go: { label: 'Go', bg: 'bg-green-100', text: 'text-green-800' },
      no_go: { label: 'No Go', bg: 'bg-red-100', text: 'text-red-800' },
      a_approfondir: { label: 'Further Analysis Needed', bg: 'bg-amber-100', text: 'text-amber-800' },
    }
    const rec = recConfig[recommendation] || { label: recommendation, bg: 'bg-gray-100', text: 'text-gray-800' }

    const confidencePct = typeof confidence === 'number'
      ? Math.round(confidence * (confidence <= 1 ? 100 : 1))
      : null

    const confidenceColor = confidencePct !== null
      ? confidencePct >= 80 ? 'bg-green-500' : confidencePct >= 60 ? 'bg-amber-500' : 'bg-red-500'
      : 'bg-gray-400'

    return (
      <div className="mt-3 bg-gray-50 rounded-lg border border-gray-200 p-4 space-y-3">
        {/* Recommendation badge */}
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Recommendation</span>
          <span className={`px-3 py-1 rounded-full text-sm font-semibold ${rec.bg} ${rec.text}`}>
            {rec.label}
          </span>
        </div>

        {/* Confidence bar */}
        {confidencePct !== null && (
          <div>
            <div className="flex items-center justify-between mb-1">
              <span className="text-sm font-medium text-gray-700">Confidence</span>
              <span className="text-sm font-semibold text-gray-900">{confidencePct}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className={`h-2 rounded-full transition-all duration-500 ${confidenceColor}`}
                style={{ width: `${confidencePct}%` }}
              />
            </div>
          </div>
        )}

        {/* Reasoning */}
        {reasoning && (
          <div>
            <p className="text-sm font-medium text-gray-700 mb-1">Reasoning</p>
            <p className="text-sm text-gray-600 leading-relaxed">{reasoning}</p>
          </div>
        )}
      </div>
    )
  }

  // OCR step — show extracted info or description
  if (step.includes('ocr')) {
    const fields = outputData.structured_data?.fields || {}
    const rawText = outputData.raw_ocr_text || outputData.raw_text || ''

    // Rich OCR data available
    if (Object.keys(fields).length > 0 || rawText) {
      return (
        <div className="mt-3 space-y-2">
          {Object.keys(fields).length > 0 && (
            <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
              <p className="text-sm font-semibold text-blue-900 mb-2">Extracted Information</p>
              <div className="grid grid-cols-2 gap-3">
                {Object.entries(fields).map(([key, value]: [string, any]) => (
                  <div key={key}>
                    <p className="text-xs text-gray-600 capitalize">{key.replace(/_/g, ' ')}</p>
                    <p className="text-sm font-medium text-gray-900">
                      {value?.value || value || 'N/A'}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          )}
          {rawText && (
            <details className="bg-gray-50 p-3 rounded border border-gray-200">
              <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800 font-medium">
                View Full OCR Text ({rawText.length} characters)
              </summary>
              <pre className="mt-2 text-xs text-gray-700 whitespace-pre-wrap max-h-40 overflow-auto">
                {rawText.substring(0, 2000)}
                {rawText.length > 2000 && '...'}
              </pre>
            </details>
          )}
        </div>
      )
    }

    // Summary only
    return <StepDescription description={outputData.description} />
  }

  // Analysis step (claim_analysis / tender_analysis) — description
  if (step.includes('analysis')) {
    return <StepDescription description={outputData.description} />
  }

  // User Info Output
  if (step.includes('user') || step.includes('retrieve_user')) {
    const userInfo = outputData.user_info || {}
    const contracts = outputData.contracts || []
    const hasUserInfo = Object.keys(userInfo).length > 0
    const hasContracts = contracts.length > 0

    return (
      <details className="mt-3 bg-indigo-50 p-3 rounded-lg border border-indigo-200">
        <summary className="text-sm font-semibold text-indigo-900 cursor-pointer hover:text-indigo-700">
          User Information ({contracts.length} contract{contracts.length !== 1 ? 's' : ''})
        </summary>
        <div className="mt-3">
          {hasUserInfo ? (
            <div className="space-y-2 mb-3">
              {userInfo.user_id && (
                <div>
                  <p className="text-xs text-gray-600">User ID</p>
                  <p className="text-sm font-medium text-gray-900">{userInfo.user_id}</p>
                </div>
              )}
              {userInfo.email && (
                <div>
                  <p className="text-xs text-gray-600">Email</p>
                  <p className="text-sm font-medium text-gray-900">{userInfo.email}</p>
                </div>
              )}
              {userInfo.phone_number && (
                <div>
                  <p className="text-xs text-gray-600">Phone</p>
                  <p className="text-sm font-medium text-gray-900">{userInfo.phone_number}</p>
                </div>
              )}
              {userInfo.date_of_birth && (
                <div>
                  <p className="text-xs text-gray-600">Date of Birth</p>
                  <p className="text-sm font-medium text-gray-900">{userInfo.date_of_birth}</p>
                </div>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-600 mb-3">No user information found</p>
          )}
          {hasContracts ? (
            <div className="mt-3 pt-3 border-t border-indigo-300">
              <p className="text-xs text-gray-600 mb-2">Contracts: {contracts.length}</p>
              <div className="space-y-2">
                {contracts.slice(0, 3).map((contract: any, idx: number) => (
                  <div key={idx} className="bg-white p-2 rounded border border-indigo-100">
                    <p className="text-sm font-semibold text-gray-900">
                      {contract.contract_number || `Contract #${idx + 1}`}
                    </p>
                    {contract.contract_type && (
                      <p className="text-xs text-gray-600">Type: {contract.contract_type}</p>
                    )}
                    {contract.coverage_amount && (
                      <p className="text-xs text-gray-600">
                        Coverage: ${Number(contract.coverage_amount).toLocaleString()}
                      </p>
                    )}
                    {contract.is_active !== undefined && (
                      <p className="text-xs text-indigo-700">
                        Status: {contract.is_active ? 'Active' : 'Inactive'}
                      </p>
                    )}
                  </div>
                ))}
                {contracts.length > 3 && (
                  <p className="text-xs text-gray-600 italic">+ {contracts.length - 3} more contracts</p>
                )}
              </div>
            </div>
          ) : (
            !hasUserInfo && <p className="text-sm text-gray-600">No contracts found</p>
          )}
        </div>
      </details>
    )
  }

  // Similar Claims Output
  if (step.includes('similar')) {
    const claims = outputData.claims || outputData.similar_claims || []

    return (
      <details className="mt-3 bg-purple-50 p-3 rounded-lg border border-purple-200">
        <summary className="text-sm font-semibold text-purple-900 cursor-pointer hover:text-purple-700">
          Similar Claims Found: {claims.length}
        </summary>
        <div className="mt-3">
          {claims.length > 0 ? (
            <div className="space-y-2">
              {claims.slice(0, 3).map((claim: any, idx: number) => (
                <div key={idx} className="bg-white p-3 rounded border border-purple-100">
                  <p className="text-sm font-semibold text-gray-900">
                    {claim.claim_number || `Claim #${idx + 1}`}
                  </p>
                  {claim.claim_type && (
                    <p className="text-xs text-gray-600 mt-1">Type: {claim.claim_type}</p>
                  )}
                  {claim.decision && (
                    <p className="text-xs text-gray-600">
                      Decision: <span className="font-medium">{claim.decision}</span>
                    </p>
                  )}
                  {claim.similarity_score && (
                    <p className="text-xs text-purple-700">
                      Match: {(claim.similarity_score * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              ))}
              {claims.length > 3 && (
                <p className="text-xs text-gray-600 italic">
                  + {claims.length - 3} more similar claims
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No similar claims found</p>
          )}
        </div>
      </details>
    )
  }

  // Knowledge Base / Articles Output
  if (step.includes('knowledge') || step.includes('search')) {
    const articles = outputData.articles || outputData.results || []

    return (
      <details className="mt-3 bg-amber-50 p-3 rounded-lg border border-amber-200">
        <summary className="text-sm font-semibold text-amber-900 cursor-pointer hover:text-amber-700">
          Knowledge Base Results: {articles.length}
        </summary>
        <div className="mt-3">
          {articles.length > 0 ? (
            <div className="space-y-2">
              {articles.slice(0, 3).map((article: any, idx: number) => (
                <div key={idx} className="bg-white p-3 rounded border border-amber-100">
                  <p className="text-sm font-semibold text-gray-900">
                    {article.title || article.section || `Article ${idx + 1}`}
                  </p>
                  {article.content && (
                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                      {article.content}
                    </p>
                  )}
                  {article.relevance_score && (
                    <p className="text-xs text-amber-700 mt-1">
                      Relevance: {(article.relevance_score * 100).toFixed(0)}%
                    </p>
                  )}
                </div>
              ))}
              {articles.length > 3 && (
                <p className="text-xs text-gray-600 italic">
                  + {articles.length - 3} more articles
                </p>
              )}
            </div>
          ) : (
            <p className="text-sm text-gray-600">No relevant articles found</p>
          )}
        </div>
      </details>
    )
  }

  // Simple description fallback (for steps with just a description field)
  if (outputData.description && Object.keys(outputData).length === 1) {
    return <StepDescription description={outputData.description} />
  }

  // Final fallback: Show formatted JSON for truly unknown data
  return (
    <details className="mt-2">
      <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
        View Output Data
      </summary>
      <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs overflow-auto max-h-60">
        {JSON.stringify(outputData, null, 2)}
      </pre>
    </details>
  )
}

/** Simple step description display */
function StepDescription({ description }: { description?: string }) {
  if (!description) return null
  return (
    <p className="mt-1 text-sm text-gray-500 italic">{description}</p>
  )
}

export { STEP_LABELS }
