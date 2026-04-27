import { useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { useReclamation } from '../hooks/useReclamation'
import { useReclamationPolling } from '../hooks/useReclamationPolling'
import { postalService } from '../services/postalService'
import { useTranslation } from '../i18n/LanguageContext'
import type { ReclamationStatus, ReclamationDecisionType, ProcessingStepLog, TrackingEvent } from '../types/reclamation'

export default function PostalDetailPage() {
  const { reclamationId } = useParams<{ reclamationId: string }>()
  const { t, locale } = useTranslation()
  const { reclamation, status, decision, logs, tracking, loading, error, reload } = useReclamation(reclamationId)
  const [processing, setProcessing] = useState(false)
  const [processError, setProcessError] = useState<string | null>(null)
  const [showPdf, setShowPdf] = useState(false)

  useReclamationPolling(reclamation, {
    enabled: true,
    interval: 2000,
    onPoll: reload
  })

  const handleProcess = async () => {
    if (!reclamationId) return
    try {
      setProcessing(true)
      setProcessError(null)
      await postalService.processReclamation(reclamationId)
      reload()
    } catch (err) {
      console.error('Error processing reclamation:', err)
      setProcessError(t('postal.failedToProcess'))
    } finally {
      setProcessing(false)
    }
  }

  const getStatusColor = (s: ReclamationStatus) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      processing: 'bg-blue-100 text-blue-800',
      completed: 'bg-green-100 text-green-800',
      rejected: 'bg-red-100 text-red-800',
      escalated: 'bg-orange-100 text-orange-800',
      manual_review: 'bg-yellow-100 text-yellow-800',
    }
    return colors[s] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (s: ReclamationStatus) => {
    const labels: Record<string, string> = {
      pending: t('postal.statusPending'),
      processing: t('postal.statusProcessing'),
      completed: t('postal.statusCompleted'),
      rejected: t('postal.statusRejected'),
      escalated: t('postal.statusEscalated'),
      manual_review: t('postal.statusManualReview'),
    }
    return labels[s] || s.toUpperCase()
  }

  const getDecisionColor = (dec: ReclamationDecisionType | undefined) => {
    switch (dec) {
      case 'rembourser': return 'text-green-600'
      case 'reexpedier': return 'text-blue-600'
      case 'rejeter': return 'text-red-600'
      case 'escalader': return 'text-orange-600'
      default: return 'text-gray-600'
    }
  }

  const getDecisionBorder = (dec: ReclamationDecisionType | undefined) => {
    switch (dec) {
      case 'rembourser': return 'border-green-500 bg-green-50'
      case 'reexpedier': return 'border-blue-500 bg-blue-50'
      case 'rejeter': return 'border-red-500 bg-red-50'
      case 'escalader': return 'border-orange-500 bg-orange-50'
      default: return 'border-gray-300 bg-gray-50'
    }
  }

  const getDecisionLabel = (dec: ReclamationDecisionType | undefined) => {
    switch (dec) {
      case 'rembourser': return t('postal.decision_rembourser')
      case 'reexpedier': return t('postal.decision_reexpedier')
      case 'rejeter': return t('postal.decision_rejeter')
      case 'escalader': return t('postal.decision_escalader')
      default: return 'N/A'
    }
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return t('common.na')
    return new Date(dateString).toLocaleString(locale === 'fr' ? 'fr-FR' : 'en-US')
  }

  const formatAmount = (amount: number | null | undefined) => {
    if (!amount) return t('common.na')
    return new Intl.NumberFormat(locale === 'fr' ? 'fr-FR' : 'en-US', { style: 'currency', currency: 'EUR', maximumFractionDigits: 2 }).format(amount)
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-yellow-600"></div>
      </div>
    )
  }

  if (error || !reclamation) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || t('postal.reclamationNotFound')}</p>
        <Link to="/postal" className="text-yellow-700 hover:text-yellow-900 mt-2 inline-block">
          {t('postal.backToPostal')}
        </Link>
      </div>
    )
  }

  const pdfUrl = `/api/v1/postal/${reclamation.id}/document/view?lang=${locale}`
  const canProcess = postalService.canProcess(reclamation)

  return (
    <div className="space-y-6">
      {/* Back link */}
      <Link to="/postal" className="text-yellow-700 hover:text-yellow-900 flex items-center">
        <svg className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        {t('postal.backToPostal')}
      </Link>

      {/* Header */}
      <div className="bg-white shadow rounded-lg overflow-hidden">
        <div className="px-6 py-4 flex justify-between items-start border-b border-gray-100">
          <div>
            <h2 className="text-2xl font-bold text-gray-900">{reclamation.reclamation_number}</h2>
            <p className="text-sm text-yellow-700 font-medium mt-1">
              {t(`postal.type_${reclamation.reclamation_type}`)}
            </p>
          </div>
          <div className="flex items-center gap-3">
            {reclamation.document_path && (
              <button
                onClick={() => setShowPdf(!showPdf)}
                className="inline-flex items-center gap-2 px-4 py-2 bg-yellow-600 hover:bg-yellow-700 text-white text-sm font-medium rounded-lg transition-colors"
              >
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                {showPdf ? t('postal.hideDocument') : t('postal.viewDocument')}
              </button>
            )}
            <span className={`px-4 py-2 text-sm font-semibold rounded-full ${getStatusColor(reclamation.status)}`}>
              {getStatusLabel(reclamation.status)}
            </span>
          </div>
        </div>

        {/* PDF Viewer */}
        {showPdf && (
          <div className="border-b border-gray-200">
            <iframe
              src={pdfUrl}
              className="w-full"
              style={{ height: '600px' }}
              title={`${reclamation.reclamation_number}.pdf`}
            />
          </div>
        )}

        {/* Description */}
        {reclamation.description && (
          <div className="mx-6 mt-4 p-4 bg-gradient-to-r from-yellow-50 to-amber-50 border border-yellow-200 rounded-lg">
            <p className="text-xs text-yellow-700 font-semibold uppercase tracking-wide mb-1">{t('postal.description')}</p>
            <p className="text-sm text-gray-900">
              {locale === 'en' && reclamation.metadata?.description_en
                ? reclamation.metadata.description_en
                : reclamation.description}
            </p>
          </div>
        )}

        {/* Key info grid */}
        <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          <div>
            <p className="text-xs text-gray-500 font-medium">{t('postal.clientName')}</p>
            <p className="text-sm font-semibold text-gray-900">{reclamation.client_nom}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">{t('postal.clientEmail')}</p>
            <p className="text-sm font-semibold text-gray-900">{reclamation.client_email}</p>
          </div>
          {reclamation.client_telephone && (
            <div>
              <p className="text-xs text-gray-500 font-medium">{t('postal.clientPhone')}</p>
              <p className="text-sm font-semibold text-gray-900">{reclamation.client_telephone}</p>
            </div>
          )}
          <div>
            <p className="text-xs text-gray-500 font-medium">{t('postal.trackingNumber')}</p>
            <p className="text-sm font-semibold text-yellow-700">{reclamation.numero_suivi}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">{t('postal.declaredValue')}</p>
            <p className="text-sm font-bold text-yellow-700">{formatAmount(reclamation.valeur_declaree)}</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 font-medium">{t('postal.submittedOn')}</p>
            <p className="text-sm font-semibold text-gray-900">{formatDate(reclamation.submitted_at)}</p>
          </div>
          {reclamation.processed_at && (
            <div>
              <p className="text-xs text-gray-500 font-medium">{t('postal.processedIn')}</p>
              <p className="text-sm font-semibold text-gray-900">
                {reclamation.total_processing_time_ms
                  ? `${(reclamation.total_processing_time_ms / 1000).toFixed(1)}s`
                  : formatDate(reclamation.processed_at)}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Process button */}
      {canProcess && (
        <div className="bg-white shadow rounded-lg p-6">
          <button
            onClick={handleProcess}
            disabled={processing}
            className="w-full bg-yellow-600 hover:bg-yellow-700 disabled:bg-yellow-400 text-white font-medium py-3 px-6 rounded-lg transition-colors"
          >
            {processing ? t('postal.processingReclamation') : t('postal.processReclamation')}
          </button>
          {processError && (
            <p className="mt-2 text-sm text-red-600">{processError}</p>
          )}
        </div>
      )}

      {/* Tracking Timeline */}
      {tracking.length > 0 && (
        <TrackingTimeline events={tracking} t={t} formatDate={formatDate} locale={locale} />
      )}

      {/* Processing Steps */}
      {(['processing', 'completed', 'rejected', 'manual_review', 'escalated'].includes(reclamation.status) || logs.length > 0) && (
        <PostalProcessingSteps
          reclamation={reclamation}
          status={status}
          logs={logs}
          t={t}
        />
      )}

      {/* Decision */}
      {decision && (
        <div className="bg-white shadow rounded-lg p-6">
          <h3 className="text-xl font-bold text-gray-900 mb-4">{t('postalDecision.title')}</h3>

          <div className="mb-6">
            <div className={`border-2 rounded-lg p-6 ${getDecisionBorder(decision.initial_decision)}`}>
              <p className="text-sm font-medium text-gray-500 mb-2">{t('postalDecision.systemDecision')}</p>
              <p className={`text-4xl font-bold ${getDecisionColor(decision.initial_decision)}`}>
                {getDecisionLabel(decision.initial_decision)}
              </p>
              {decision.initial_confidence != null && (
                <div className="mt-3">
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-600">{t('postalDecision.confidence')}</span>
                    <span className="text-sm font-medium">{(decision.initial_confidence * 100).toFixed(1)}%</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-yellow-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${decision.initial_confidence * 100}%` }}
                    ></div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {decision.initial_reasoning && (
            <div className="mt-6">
              <p className="text-sm text-gray-600 mb-2">{t('postalDecision.reasoning')}</p>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-gray-900 whitespace-pre-wrap">
                  {locale === 'en' && decision.metadata?.reasoning_en
                    ? decision.metadata.reasoning_en
                    : (decision.initial_reasoning || decision.reasoning || 'N/A')}
                </p>
              </div>
            </div>
          )}

          {decision.requires_manual_review && (
            <div className="mt-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 font-medium">{t('postalDecision.requiresManualReview')}</p>
            </div>
          )}

          {decision.llm_model && (
            <div className="mt-4">
              <p className="text-sm text-gray-600">{t('postalDecision.llmModel')}: {decision.llm_model}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

// ---- Tracking Timeline Component ----
function TrackingTimeline({ events, t, formatDate, locale }: { events: TrackingEvent[]; t: (key: string) => string; formatDate: (d: string | null | undefined) => string; locale: string }) {
  const sortedEvents = [...events].sort((a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime())

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">{t('postal.trackingTimeline')}</h3>
      <div className="relative">
        <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-yellow-200"></div>
        <div className="space-y-4">
          {sortedEvents.map((event, index) => (
            <div key={event.id || index} className="relative flex items-start ml-4 pl-6">
              <div className={`absolute -left-1.5 w-4 h-4 rounded-full border-2 ${
                event.is_final
                  ? 'bg-yellow-600 border-yellow-600'
                  : 'bg-white border-yellow-400'
              }`}></div>
              <div className="flex-1 bg-gray-50 rounded-lg p-3 border border-gray-200">
                <div className="flex items-center justify-between mb-1">
                  <span className="text-sm font-semibold text-gray-900">{event.event_type}</span>
                  <span className="text-xs text-gray-500">{formatDate(event.event_date)}</span>
                </div>
                <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
                  {event.location && <span>{event.location}</span>}
                  {event.code_postal && <span>{event.code_postal}</span>}
                </div>
                {event.detail && (
                  <p className="text-xs text-gray-500 mt-1">
                    {locale === 'en' && event.metadata?.detail_en
                      ? event.metadata.detail_en
                      : event.detail}
                  </p>
                )}
                {event.is_final && (
                  <span className="inline-block mt-1 text-xs px-2 py-0.5 bg-yellow-100 text-yellow-800 rounded-full font-medium">
                    {t('postal.finalEvent')}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// ---- Processing Steps Component ----
function StepIcon({ status }: { status: string }) {
  if (status === 'completed') {
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
        <svg className="h-5 w-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
        </svg>
      </div>
    )
  }
  if (status === 'failed') {
    return (
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-red-100 flex items-center justify-center">
        <svg className="h-5 w-5 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
        </svg>
      </div>
    )
  }
  return (
    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gray-100 flex items-center justify-center">
      <svg className="h-5 w-5 text-gray-400 animate-spin" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    </div>
  )
}

function PostalProcessingSteps({ reclamation, status, logs, t }: {
  reclamation: { status: string }
  status: { progress_percentage: number; processing_steps: ProcessingStepLog[] } | null
  logs: ProcessingStepLog[]
  t: (key: string) => string
}) {
  const steps = (status?.processing_steps && status.processing_steps.length > 0)
    ? status.processing_steps
    : logs

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">{t('postal.processingSteps')}</h3>

      {status && reclamation.status === 'processing' && (
        <div className="mb-4 p-4 bg-yellow-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-yellow-800">{t('postal.processingInProgress')}</p>
            <p className="text-sm font-bold text-yellow-800">{status.progress_percentage || 0}%</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-yellow-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${status.progress_percentage || 0}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {steps.map((step: ProcessingStepLog, index: number) => (
          <div key={index} className="border border-gray-200 rounded-lg p-4">
            <div className="flex items-start gap-3">
              <StepIcon status={step.status} />
              <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-gray-900">{step.step_name}</p>
                  <div className="flex items-center gap-2">
                    {step.duration_ms != null && (
                      <span className="text-xs text-yellow-600 font-medium">
                        {step.duration_ms < 1000
                          ? `${step.duration_ms}ms`
                          : `${(step.duration_ms / 1000).toFixed(1)}s`}
                      </span>
                    )}
                    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${
                      step.status === 'completed'
                        ? 'bg-green-100 text-green-700'
                        : step.status === 'failed'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-gray-100 text-gray-600'
                    }`}>
                      {step.status === 'completed' ? 'OK' : step.status === 'failed' ? t('common.error') : step.status}
                    </span>
                  </div>
                </div>

                {step.error_message && (
                  <p className="text-xs text-red-600 mt-1">{step.error_message}</p>
                )}

                {step.output_data && (
                  <details className="mt-3 bg-gray-50 p-3 rounded border border-gray-200">
                    <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800 font-medium">
                      {t('postal.viewData')}
                    </summary>
                    <pre className="mt-2 text-xs text-gray-700 overflow-auto max-h-48">
                      {JSON.stringify(step.output_data, null, 2)}
                    </pre>
                  </details>
                )}
              </div>
            </div>
          </div>
        ))}

        {steps.length === 0 && (
          <div className="p-6 bg-gray-50 rounded-lg text-center">
            <svg className="h-8 w-8 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-600">{t('postal.waitingForProcessing')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
