/**
 * ClaimHeader Component - Displays claim header information
 */

import type { Claim, ProcessingStepLog } from '../../types'

interface ClaimHeaderProps {
  claim: Claim
  logs?: ProcessingStepLog[]
}

export default function ClaimHeader({ claim, logs = [] }: ClaimHeaderProps) {
  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      manual_review: 'bg-orange-100 text-orange-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const formatDate = (dateString: string | null) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString()
  }

  // Extract OCR data for claim subject
  const getClaimSubject = () => {
    const ocrStep = logs.find((s: ProcessingStepLog) => s.step_name === 'ocr')
    const ocrData = ocrStep?.output_data?.structured_data?.fields
    if (!ocrData) return null

    const diagnosis = ocrData.diagnosis?.value || ocrData.service?.value
    const amount = ocrData.amount?.value
    const providerName = ocrData.provider_name?.value
    const dateOfService = ocrData.date_of_service?.value

    return { diagnosis, amount, providerName, dateOfService }
  }

  const subject = getClaimSubject()

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-3xl font-bold text-gray-900">{claim.claim_number}</h2>
          <p className="mt-2 text-gray-600">Claim ID: {claim.id}</p>
        </div>
        <span className={`px-4 py-2 text-sm font-semibold rounded-full ${getStatusColor(claim.status)}`}>
          {claim.status.toUpperCase()}
        </span>
      </div>

      {/* Claim Subject from OCR */}
      {subject && (subject.diagnosis || subject.amount) && (
        <div className="mt-4 p-4 bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg">
          <p className="text-xs text-gray-600 font-medium mb-1">CLAIM SUBJECT</p>
          <p className="text-lg font-semibold text-gray-900">
            {subject.diagnosis || 'Medical Service'}
            {subject.amount && <span className="ml-2 text-blue-600">(${subject.amount})</span>}
          </p>
          {subject.providerName && (
            <p className="text-sm text-gray-600 mt-1">Provider: {subject.providerName}</p>
          )}
          {subject.dateOfService && (
            <p className="text-sm text-gray-600">Service Date: {subject.dateOfService}</p>
          )}
        </div>
      )}

      {/* Claim Details */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <p className="text-sm text-gray-600">User ID</p>
          <p className="text-lg font-medium text-gray-900">{claim.user_id}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Claim Type</p>
          <p className="text-lg font-medium text-gray-900">{claim.claim_type || 'N/A'}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Submitted At</p>
          <p className="text-lg font-medium text-gray-900">{formatDate(claim.submitted_at)}</p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Document Path</p>
          <p className="text-lg font-medium text-gray-900 truncate">{claim.document_path}</p>
        </div>
        {claim.processed_at && (
          <>
            <div>
              <p className="text-sm text-gray-600">Processed At</p>
              <p className="text-lg font-medium text-gray-900">{formatDate(claim.processed_at)}</p>
            </div>
            <div>
              <p className="text-sm text-gray-600">Total Processing Time</p>
              <p className="text-lg font-medium text-gray-900">
                {claim.total_processing_time_ms
                  ? `${(claim.total_processing_time_ms / 1000).toFixed(2)}s`
                  : 'N/A'}
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
