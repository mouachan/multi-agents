/**
 * StepOutputDisplay - Pretty display for processing step outputs
 *
 * Instead of raw JSON, shows user-friendly formatted data
 */

interface StepOutputDisplayProps {
  stepName: string
  outputData: any
}

export default function StepOutputDisplay({ stepName, outputData }: StepOutputDisplayProps) {
  if (!outputData) return null

  // Debug: log what we receive for retrieve_user_info
  if (stepName.toLowerCase().includes('user')) {
    console.log('StepOutputDisplay - retrieve_user_info:', { stepName, outputData })
  }

  // OCR Output
  if (stepName.toLowerCase().includes('ocr')) {
    const fields = outputData.structured_data?.fields || {}
    const rawText = outputData.raw_ocr_text || outputData.raw_text || ''

    return (
      <div className="mt-3 space-y-2">
        {Object.keys(fields).length > 0 && (
          <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
            <p className="text-sm font-semibold text-blue-900 mb-2">📄 Extracted Information</p>
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
              📝 View Full OCR Text ({rawText.length} characters)
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

  // User Info Output
  if (stepName.toLowerCase().includes('user') || stepName.toLowerCase().includes('retrieve_user')) {
    const userInfo = outputData.user_info || {}
    const contracts = outputData.contracts || []
    const hasUserInfo = Object.keys(userInfo).length > 0
    const hasContracts = contracts.length > 0

    return (
      <details className="mt-3 bg-indigo-50 p-3 rounded-lg border border-indigo-200">
        <summary className="text-sm font-semibold text-indigo-900 cursor-pointer hover:text-indigo-700">
          👤 User Information ({contracts.length} contract{contracts.length !== 1 ? 's' : ''})
        </summary>
        <div className="mt-3">
          {/* User Info */}
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

          {/* Contracts */}
          {hasContracts ? (
            <div className="mt-3 pt-3 border-t border-indigo-300">
              <p className="text-xs text-gray-600 mb-2">📄 Contracts: {contracts.length}</p>
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
  if (stepName.toLowerCase().includes('similar') || stepName.toLowerCase().includes('claims')) {
    const claims = outputData.claims || outputData.similar_claims || []

    return (
      <details className="mt-3 bg-purple-50 p-3 rounded-lg border border-purple-200">
        <summary className="text-sm font-semibold text-purple-900 cursor-pointer hover:text-purple-700">
          🔍 Similar Claims Found: {claims.length}
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
  if (stepName.toLowerCase().includes('knowledge') || stepName.toLowerCase().includes('search')) {
    const articles = outputData.articles || outputData.results || []

    return (
      <details className="mt-3 bg-amber-50 p-3 rounded-lg border border-amber-200">
        <summary className="text-sm font-semibold text-amber-900 cursor-pointer hover:text-amber-700">
          📚 Knowledge Base Results: {articles.length}
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

  // Fallback: Show formatted JSON for unknown steps
  return (
    <details className="mt-2">
      <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-800 font-medium">
        📋 View Output Data
      </summary>
      <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs overflow-auto max-h-60">
        {JSON.stringify(outputData, null, 2)}
      </pre>
    </details>
  )
}
