/**
 * ClaimHeader Component - Displays claim header with business-friendly information
 */

import { useState } from 'react'
import type { Claim, ProcessingStepLog } from '../../types'
import { useTranslation } from '../../i18n/LanguageContext'

interface ClaimHeaderProps {
  claim: Claim
  logs?: ProcessingStepLog[]
}

/** Claim type configuration */
const CLAIM_TYPE_CONFIG: Record<string, { label: string; bg: string; text: string; ring: string }> = {
  auto: { label: 'Auto', bg: 'bg-blue-100', text: 'text-blue-800', ring: 'ring-blue-500' },
  medical: { label: 'Medical', bg: 'bg-emerald-100', text: 'text-emerald-800', ring: 'ring-emerald-500' },
  home: { label: 'Home', bg: 'bg-orange-100', text: 'text-orange-800', ring: 'ring-orange-500' },
  construction_all_risk: { label: 'Construction', bg: 'bg-purple-100', text: 'text-purple-800', ring: 'ring-purple-500' },
}

export default function ClaimHeader({ claim, logs = [] }: ClaimHeaderProps) {
  const { t, locale } = useTranslation()
  const [showPdf, setShowPdf] = useState(false)

  const STATUS_CONFIG: Record<string, { label: string; bg: string; text: string }> = {
    pending: { label: t('common.pending'), bg: 'bg-gray-100', text: 'text-gray-700' },
    processing: { label: t('common.processing'), bg: 'bg-blue-100', text: 'text-blue-700' },
    completed: { label: t('common.completed'), bg: 'bg-green-100', text: 'text-green-700' },
    denied: { label: t('common.denied'), bg: 'bg-red-100', text: 'text-red-700' },
    failed: { label: t('common.failed'), bg: 'bg-red-100', text: 'text-red-700' },
    manual_review: { label: t('common.manual_review'), bg: 'bg-amber-100', text: 'text-amber-700' },
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return null
    return new Date(dateString).toLocaleDateString(locale === 'fr' ? 'fr-FR' : 'en-US', {
      year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
    })
  }

  const claimType = claim.claim_type?.toLowerCase() || ''
  const typeConfig = CLAIM_TYPE_CONFIG[claimType] || {
    label: claim.claim_type || 'Unknown',
    bg: 'bg-gray-100', text: 'text-gray-800', ring: 'ring-gray-500'
  }

  const statusConfig = STATUS_CONFIG[claim.status] || STATUS_CONFIG.pending

  // Extract OCR data for claim subject
  const ocrStep = logs.find((s: ProcessingStepLog) => s.step_name === 'ocr' || s.step_name === 'ocr_document')
  const ocrData = ocrStep?.output_data?.structured_data?.fields
  const diagnosis = ocrData?.diagnosis?.value || ocrData?.service?.value
  const amount = ocrData?.amount?.value
  const providerName = ocrData?.provider_name?.value

  // Extract useful metadata
  const metadata = claim.metadata || {}
  const projectRef = metadata.project_reference
  const description = metadata.description

  // Display claim_number.pdf as document name instead of internal file ID
  const documentName = `${claim.claim_number}.pdf`

  // Build the API URL for document viewing
  const apiBaseUrl = import.meta.env.VITE_API_URL || '/api/v1'
  const documentViewUrl = `${apiBaseUrl}/claims/documents/${claim.id}/view`

  // Duration: use total_processing_time_ms if available, otherwise compute from submitted_at/processed_at
  const computeDuration = (): string | null => {
    if (claim.total_processing_time_ms) {
      if (claim.total_processing_time_ms < 1000) return `${claim.total_processing_time_ms}ms`
      return `${(claim.total_processing_time_ms / 1000).toFixed(1)}s`
    }
    if (claim.submitted_at && claim.processed_at) {
      const diffMs = new Date(claim.processed_at).getTime() - new Date(claim.submitted_at).getTime()
      // Only show fallback if reasonable (< 1 hour = actual processing, not days between submission and review)
      if (diffMs > 0 && diffMs < 3600000) {
        if (diffMs < 1000) return `${diffMs}ms`
        if (diffMs < 60000) return `${(diffMs / 1000).toFixed(1)}s`
        return `${(diffMs / 60000).toFixed(1)}min`
      }
    }
    return null
  }

  const duration = computeDuration()

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Top bar with claim number, type, status */}
      <div className="px-6 py-4 border-b border-gray-100 flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-2xl font-bold text-gray-900">{claim.claim_number}</h2>
          <span className={`px-3 py-1 text-xs font-semibold rounded-full ${typeConfig.bg} ${typeConfig.text}`}>
            {typeConfig.label}
          </span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowPdf(!showPdf)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {showPdf ? t('claims.hideDocument') : t('claims.viewDocument')}
          </button>
          <span className={`px-4 py-1.5 text-sm font-semibold rounded-full ${statusConfig.bg} ${statusConfig.text}`}>
            {statusConfig.label}
          </span>
        </div>
      </div>

      {/* PDF Viewer */}
      {showPdf && (
        <div className="border-b border-gray-200">
          <iframe
            src={documentViewUrl}
            className="w-full"
            style={{ height: '600px' }}
            title={documentName}
          />
        </div>
      )}

      {/* Claim Subject from OCR (if available) */}
      {(diagnosis || amount || description) && (
        <div className="px-6 py-3 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
          <p className="text-sm font-semibold text-gray-900">
            {diagnosis || description || t('claims.claimSubject')}
            {amount && <span className="ml-2 text-blue-600">(${amount})</span>}
          </p>
          {providerName && (
            <p className="text-xs text-gray-600 mt-0.5">{t('claims.provider')}: {providerName}</p>
          )}
          {projectRef && (
            <p className="text-xs text-gray-600 mt-0.5">Project: {projectRef}</p>
          )}
        </div>
      )}

      {/* Main info grid */}
      <div className="px-6 py-5">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-y-4 gap-x-6">
          {/* User */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t('claims.claimant')}</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">{claim.user_name || claim.user_id}</p>
          </div>

          {/* Submitted */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t('claims.submittedAt')}</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">
              {formatDate(claim.submitted_at) || t('common.na')}
            </p>
          </div>

          {/* Processed */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t('claims.processed')}</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">
              {claim.processed_at ? formatDate(claim.processed_at) : '-'}
            </p>
          </div>

          {/* Processing time */}
          <div>
            <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">{t('claims.duration')}</p>
            <p className="mt-1 text-sm font-semibold text-gray-900">
              {duration || '-'}
            </p>
          </div>
        </div>

        {/* Document section */}
        <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2 min-w-0">
          <svg className="h-5 w-5 text-gray-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
              d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
          </svg>
          <span className="text-sm text-gray-600 truncate">{documentName}</span>
        </div>
      </div>
    </div>
  )
}
