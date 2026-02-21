import type { Tender, TenderStatusResponse, ProcessingStepLog } from '../../types/tender'
import { useTranslation } from '../../i18n/LanguageContext'

interface TenderProcessingStepsProps {
  tender: Tender
  status: TenderStatusResponse | null
  logs: ProcessingStepLog[]
}

function formatAmount(amount: number | null | undefined) {
  if (!amount && amount !== 0) return 'N/A'
  return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount)
}

function formatSimilarity(score: number | null | undefined) {
  if (!score && score !== 0) return '-'
  return `${(score * 100).toFixed(0)}%`
}

// ---- OCR Rendering (collapsible) ----
function OcrResult({ data, t }: { data: Record<string, any>; t: (key: string) => string }) {
  if (!data?.success) {
    return <p className="text-sm text-red-600">{t('tenderSteps.ocrFailed')}</p>
  }

  const structured = data.structured_data || {}
  const fields = structured.fields || structured
  const rawText = data.raw_text || ''
  const pages = data.pages_processed || data.page_count || 1
  const time = data.processing_time_seconds

  const keyInfo: Record<string, string> = {}
  if (typeof fields === 'object' && Object.keys(fields).length > 0) {
    for (const [k, v] of Object.entries(fields)) {
      if (v && typeof v === 'object' && 'value' in (v as any)) {
        keyInfo[k] = String((v as any).value)
      } else if (v && typeof v !== 'object') {
        keyInfo[k] = String(v)
      }
    }
  }

  return (
    <details className="bg-blue-50 p-3 rounded-lg border border-blue-200">
      <summary className="text-sm font-semibold text-blue-900 cursor-pointer hover:text-blue-700">
        {t('tenderSteps.ocrExtraction')} - {pages} page(s){time ? ` - ${time.toFixed(1)}s` : ''}
        {data.confidence ? ` - ${t('tenderDecision.confidence')} ${(data.confidence * 100).toFixed(0)}%` : ''}
      </summary>
      <div className="mt-3 space-y-2">
        {Object.keys(keyInfo).length > 0 && (
          <div className="grid grid-cols-2 gap-3">
            {Object.entries(keyInfo).map(([key, value]) => (
              <div key={key}>
                <p className="text-xs text-gray-500 capitalize">{key.replace(/_/g, ' ')}</p>
                <p className="text-sm font-medium text-gray-900">{value}</p>
              </div>
            ))}
          </div>
        )}
        {rawText && (
          <details className="bg-gray-50 p-2 rounded border border-gray-200">
            <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800 font-medium">
              {t('tenderSteps.extractedText')} ({rawText.length} {t('tenderSteps.chars')})
            </summary>
            <pre className="mt-2 text-xs text-gray-700 whitespace-pre-wrap max-h-40 overflow-auto">
              {rawText.substring(0, 2000)}
              {rawText.length > 2000 && '...'}
            </pre>
          </details>
        )}
      </div>
    </details>
  )
}

// ---- References Rendering (collapsible cards) ----
function ReferencesResult({ data, t }: { data: Record<string, any>; t: (key: string) => string }) {
  const refs = data?.references || []
  if (!data?.success || refs.length === 0) {
    return <p className="text-sm text-gray-500 italic">{t('tenderSteps.noSimilarRefs')}</p>
  }

  return (
    <details className="bg-purple-50 p-3 rounded-lg border border-purple-200" open>
      <summary className="text-sm font-semibold text-purple-900 cursor-pointer hover:text-purple-700">
        {t('tenderSteps.similarRefs')} : {data.total_found}
      </summary>
      <div className="mt-3 space-y-2">
        {refs.slice(0, 5).map((ref: any, i: number) => (
          <div key={i} className="bg-white p-3 rounded border border-purple-100">
            <div className="flex items-center justify-between">
              <p className="text-sm font-semibold text-gray-900">{ref.project_name}</p>
              <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                (ref.similarity || 0) >= 0.3 ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
              }`}>
                {formatSimilarity(ref.similarity)}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
              {ref.maitre_ouvrage && <span>{ref.maitre_ouvrage}</span>}
              {ref.nature_travaux && <span>{ref.nature_travaux}</span>}
              {ref.montant && <span>{formatAmount(ref.montant)}</span>}
              {ref.region && <span>{ref.region}</span>}
            </div>
            {ref.description && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ref.description}</p>
            )}
          </div>
        ))}
        {refs.length > 5 && (
          <p className="text-xs text-gray-500 italic">+ {refs.length - 5} {t('tenderSteps.others')}</p>
        )}
      </div>
    </details>
  )
}

// ---- Historical Tenders Rendering (collapsible cards) ----
function HistoricalResult({ data, t }: { data: Record<string, any>; t: (key: string) => string }) {
  const tenders = data?.historical_tenders || []
  if (!data?.success || tenders.length === 0) {
    return <p className="text-sm text-gray-500 italic">{t('tenderSteps.noHistorical')}</p>
  }

  const winRate = data.win_rate_percentage || 0
  const won = tenders.filter((tt: any) => tt.resultat === 'gagne').length
  const lost = tenders.filter((tt: any) => tt.resultat !== 'gagne').length

  return (
    <details className="bg-amber-50 p-3 rounded-lg border border-amber-200" open>
      <summary className="text-sm font-semibold text-amber-900 cursor-pointer hover:text-amber-700">
        {t('tenderSteps.historicalAO')} : {data.total_found} -
        <span className={`ml-1 ${winRate >= 50 ? 'text-green-700' : winRate >= 25 ? 'text-amber-700' : 'text-red-700'}`}>
          {t('tenderSteps.successRate')} {winRate.toFixed(0)}%
        </span>
        <span className="ml-1 text-xs font-normal text-gray-600">({won} {t('tenderSteps.won')} / {lost} {t('tenderSteps.lost')})</span>
      </summary>
      <div className="mt-3 space-y-2">
        {tenders.slice(0, 5).map((tt: any, i: number) => (
          <div key={i} className={`bg-white p-3 rounded border ${
            tt.resultat === 'gagne' ? 'border-l-4 border-l-green-500 border-green-100' : 'border-l-4 border-l-red-400 border-red-100'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  tt.resultat === 'gagne' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {tt.resultat === 'gagne' ? 'WON' : 'LOST'}
                </span>
                <p className="text-sm font-semibold text-gray-900">{tt.ao_number}</p>
              </div>
              <span className={`text-xs font-bold ${(tt.similarity || 0) >= 0.3 ? 'text-green-600' : 'text-gray-400'}`}>
                {formatSimilarity(tt.similarity)}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
              {tt.nature_travaux && <span>{tt.nature_travaux}</span>}
              {tt.montant_estime && <span>{formatAmount(tt.montant_estime)}</span>}
              {tt.note_technique != null && <span>Notes: {tt.note_technique}/{tt.note_prix}</span>}
              {tt.region && <span>{tt.region}</span>}
            </div>
            {tt.raison_resultat && (
              <p className="text-xs text-gray-500 mt-1 italic">{tt.raison_resultat}</p>
            )}
          </div>
        ))}
        {tenders.length > 5 && (
          <p className="text-xs text-gray-500 italic">+ {tenders.length - 5} {t('tenderSteps.others')}</p>
        )}
      </div>
    </details>
  )
}

// ---- Capabilities Rendering (collapsible cards by category) ----
function CapabilitiesResult({ data, t }: { data: Record<string, any>; t: (key: string) => string }) {
  const caps = data?.capabilities || []

  if (!data?.success || caps.length === 0) {
    return <p className="text-sm text-gray-500 italic">{t('tenderSteps.noCapabilities')}</p>
  }

  // Group by category
  const byCategory: Record<string, any[]> = {}
  for (const cap of caps) {
    const cat = cap.category || 'autre'
    if (!byCategory[cat]) byCategory[cat] = []
    byCategory[cat].push(cap)
  }

  const categoryLabels: Record<string, string> = {
    certification: t('tenderSteps.certifications'),
    materiel: t('tenderSteps.equipment'),
    personnel: t('tenderSteps.personnel'),
  }

  return (
    <details className="bg-green-50 p-3 rounded-lg border border-green-200" open>
      <summary className="text-sm font-semibold text-green-900 cursor-pointer hover:text-green-700">
        {t('tenderSteps.internalCaps')} : {data.total_found} ({data.categories_found?.length || Object.keys(byCategory).length} {t('tenderSteps.categories')})
      </summary>
      <div className="mt-3 space-y-3">
        {Object.entries(byCategory).map(([category, items]) => {
          const catLabel = categoryLabels[category] || category
          return (
            <div key={category}>
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
                {catLabel} ({items.length})
              </p>
              <div className="space-y-1">
                {items.slice(0, 5).map((cap: any, i: number) => (
                  <div key={i} className="bg-white p-2 rounded border border-green-100 flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-900">{cap.name}</p>
                      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500 mt-0.5">
                        {cap.valid_until && <span>{cap.valid_until}</span>}
                        {cap.region && <span>{cap.region}</span>}
                        {cap.availability && <span>{cap.availability}</span>}
                      </div>
                    </div>
                    <span className="text-xs text-gray-400 ml-2">{formatSimilarity(cap.similarity)}</span>
                  </div>
                ))}
                {items.length > 5 && (
                  <p className="text-xs text-gray-500 italic">+ {items.length - 5} {t('tenderSteps.others')}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </details>
  )
}

// ---- Step Content Router ----
function StepContent({ step, t }: { step: ProcessingStepLog; t: (key: string) => string }) {
  if (!step.output_data) return null

  switch (step.step_name) {
    case 'ocr_document':
      return <OcrResult data={step.output_data} t={t} />
    case 'retrieve_similar_references':
      return <ReferencesResult data={step.output_data} t={t} />
    case 'retrieve_historical_tenders':
      return <HistoricalResult data={step.output_data} t={t} />
    case 'retrieve_capabilities':
      return <CapabilitiesResult data={step.output_data} t={t} />
    default:
      return (
        <details className="bg-gray-50 p-3 rounded border border-gray-200">
          <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800 font-medium">
            {t('tenderSteps.data')} ({step.step_name})
          </summary>
          <pre className="mt-2 text-xs text-gray-700 overflow-auto max-h-48">
            {JSON.stringify(step.output_data, null, 2)}
          </pre>
        </details>
      )
  }
}

// ---- Step Icon ----
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

export default function TenderProcessingSteps({ tender, status, logs }: TenderProcessingStepsProps) {
  const { t } = useTranslation()

  const STEP_LABELS: Record<string, string> = {
    ocr_document: t('tenderSteps.ocrExtraction'),
    retrieve_similar_references: t('tenderSteps.similarReferences'),
    retrieve_historical_tenders: t('tenderSteps.historicalTenders'),
    retrieve_capabilities: t('tenderSteps.internalCapabilities'),
  }

  if (!['processing', 'completed', 'manual_review', 'failed'].includes(tender.status) && logs.length === 0) {
    return null
  }

  const steps = (status?.processing_steps && status.processing_steps.length > 0)
    ? status.processing_steps
    : logs

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">{t('tenderSteps.title')}</h3>

      {status && tender.status === 'processing' && (
        <div className="mb-4 p-4 bg-amber-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-amber-800">{t('tenderSteps.analysisInProgress')}</p>
            <p className="text-sm font-bold text-amber-800">{status.progress_percentage || 0}%</p>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-amber-600 h-2 rounded-full transition-all duration-300"
              style={{ width: `${status.progress_percentage || 0}%` }}
            ></div>
          </div>
        </div>
      )}

      <div className="space-y-4">
        {steps.map((step: ProcessingStepLog, index: number) => {
          const label = STEP_LABELS[step.step_name] || step.step_name

          return (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <StepIcon status={step.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-900">{label}</p>
                    <div className="flex items-center gap-2">
                      {step.duration_ms != null && (
                        <span className="text-xs text-amber-600 font-medium">
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
                        {step.status === 'completed' ? t('tenderSteps.ok') : step.status === 'failed' ? t('tenderSteps.error') : step.status}
                      </span>
                    </div>
                  </div>

                  {step.error_message && (
                    <p className="text-xs text-red-600 mt-1">{step.error_message}</p>
                  )}

                  <div className="mt-3">
                    <StepContent step={step} t={t} />
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {steps.length === 0 && (
          <div className="p-6 bg-gray-50 rounded-lg text-center">
            <svg className="h-8 w-8 text-gray-400 mx-auto mb-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <p className="text-gray-600">{t('tenderSteps.waitingForAnalysis')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
