import type { Tender, TenderStatusResponse, ProcessingStepLog } from '../../types/tender'

interface TenderProcessingStepsProps {
  tender: Tender
  status: TenderStatusResponse | null
  logs: ProcessingStepLog[]
}

const STEP_LABELS: Record<string, { label: string; icon: string; color: string }> = {
  ocr_document: { label: 'Extraction du Document (OCR)', icon: 'doc', color: 'blue' },
  retrieve_similar_references: { label: 'References Projets Similaires', icon: 'search', color: 'purple' },
  retrieve_historical_tenders: { label: 'Historique AO (Gagne/Perdu)', icon: 'history', color: 'amber' },
  retrieve_capabilities: { label: 'Capacites Internes VINCI', icon: 'shield', color: 'green' },
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
function OcrResult({ data }: { data: Record<string, any> }) {
  if (!data?.success) {
    return <p className="text-sm text-red-600">Echec de l'extraction OCR</p>
  }

  const structured = data.structured_data || {}
  const fields = structured.fields || structured
  const rawText = data.raw_text || ''
  const pages = data.pages_processed || data.page_count || 1
  const time = data.processing_time_seconds

  // Extract key info from structured data or raw text
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
        Extraction OCR - {pages} page(s){time ? ` en ${time.toFixed(1)}s` : ''}
        {data.confidence ? ` - Confiance ${(data.confidence * 100).toFixed(0)}%` : ''}
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
              Texte extrait ({rawText.length} caracteres)
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
function ReferencesResult({ data }: { data: Record<string, any> }) {
  const refs = data?.references || []
  if (!data?.success || refs.length === 0) {
    return <p className="text-sm text-gray-500 italic">Aucune reference similaire trouvee</p>
  }

  return (
    <details className="bg-purple-50 p-3 rounded-lg border border-purple-200" open>
      <summary className="text-sm font-semibold text-purple-900 cursor-pointer hover:text-purple-700">
        References similaires : {data.total_found}
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
              {ref.maitre_ouvrage && <span>Client: {ref.maitre_ouvrage}</span>}
              {ref.nature_travaux && <span>Nature: {ref.nature_travaux}</span>}
              {ref.montant && <span>Montant: {formatAmount(ref.montant)}</span>}
              {ref.region && <span>Region: {ref.region}</span>}
            </div>
            {ref.description && (
              <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ref.description}</p>
            )}
          </div>
        ))}
        {refs.length > 5 && (
          <p className="text-xs text-gray-500 italic">+ {refs.length - 5} autres references</p>
        )}
      </div>
    </details>
  )
}

// ---- Historical Tenders Rendering (collapsible cards) ----
function HistoricalResult({ data }: { data: Record<string, any> }) {
  const tenders = data?.historical_tenders || []
  if (!data?.success || tenders.length === 0) {
    return <p className="text-sm text-gray-500 italic">Aucun historique d'AO trouve</p>
  }

  const winRate = data.win_rate_percentage || 0
  const won = tenders.filter((t: any) => t.resultat === 'gagne').length
  const lost = tenders.filter((t: any) => t.resultat !== 'gagne').length

  return (
    <details className="bg-amber-50 p-3 rounded-lg border border-amber-200" open>
      <summary className="text-sm font-semibold text-amber-900 cursor-pointer hover:text-amber-700">
        Historique AO : {data.total_found} -
        <span className={`ml-1 ${winRate >= 50 ? 'text-green-700' : winRate >= 25 ? 'text-amber-700' : 'text-red-700'}`}>
          Taux de succes {winRate.toFixed(0)}%
        </span>
        <span className="ml-1 text-xs font-normal text-gray-600">({won} gagnes / {lost} perdus)</span>
      </summary>
      <div className="mt-3 space-y-2">
        {tenders.slice(0, 5).map((t: any, i: number) => (
          <div key={i} className={`bg-white p-3 rounded border ${
            t.resultat === 'gagne' ? 'border-l-4 border-l-green-500 border-green-100' : 'border-l-4 border-l-red-400 border-red-100'
          }`}>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                  t.resultat === 'gagne' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                }`}>
                  {t.resultat === 'gagne' ? 'GAGNE' : 'PERDU'}
                </span>
                <p className="text-sm font-semibold text-gray-900">{t.ao_number}</p>
              </div>
              <span className={`text-xs font-bold ${(t.similarity || 0) >= 0.3 ? 'text-green-600' : 'text-gray-400'}`}>
                {formatSimilarity(t.similarity)}
              </span>
            </div>
            <div className="mt-1 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-600">
              {t.nature_travaux && <span>{t.nature_travaux}</span>}
              {t.montant_estime && <span>Montant: {formatAmount(t.montant_estime)}</span>}
              {t.note_technique != null && <span>Notes: {t.note_technique}/{t.note_prix}</span>}
              {t.region && <span>{t.region}</span>}
            </div>
            {t.raison_resultat && (
              <p className="text-xs text-gray-500 mt-1 italic">{t.raison_resultat}</p>
            )}
          </div>
        ))}
        {tenders.length > 5 && (
          <p className="text-xs text-gray-500 italic">+ {tenders.length - 5} autres AO</p>
        )}
      </div>
    </details>
  )
}

// ---- Capabilities Rendering (collapsible cards by category) ----
function CapabilitiesResult({ data }: { data: Record<string, any> }) {
  const caps = data?.capabilities || []

  if (!data?.success || caps.length === 0) {
    return <p className="text-sm text-gray-500 italic">Aucune capacite trouvee</p>
  }

  // Group by category
  const byCategory: Record<string, any[]> = {}
  for (const cap of caps) {
    const cat = cap.category || 'autre'
    if (!byCategory[cat]) byCategory[cat] = []
    byCategory[cat].push(cap)
  }

  const categoryLabels: Record<string, { label: string; color: string }> = {
    certification: { label: 'Certifications & Qualifications', color: 'blue' },
    materiel: { label: 'Moyens Materiels', color: 'purple' },
    personnel: { label: 'Moyens Humains', color: 'green' },
  }

  return (
    <details className="bg-green-50 p-3 rounded-lg border border-green-200" open>
      <summary className="text-sm font-semibold text-green-900 cursor-pointer hover:text-green-700">
        Capacites internes : {data.total_found} ({data.categories_found?.length || Object.keys(byCategory).length} categories)
      </summary>
      <div className="mt-3 space-y-3">
        {Object.entries(byCategory).map(([category, items]) => {
          const catMeta = categoryLabels[category] || { label: category, color: 'gray' }
          return (
            <div key={category}>
              <p className="text-xs font-semibold text-gray-700 uppercase tracking-wide mb-2">
                {catMeta.label} ({items.length})
              </p>
              <div className="space-y-1">
                {items.slice(0, 5).map((cap: any, i: number) => (
                  <div key={i} className="bg-white p-2 rounded border border-green-100 flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs font-semibold text-gray-900">{cap.name}</p>
                      <div className="flex flex-wrap gap-x-3 gap-y-0.5 text-xs text-gray-500 mt-0.5">
                        {cap.valid_until && <span>Valide: {cap.valid_until}</span>}
                        {cap.region && <span>{cap.region}</span>}
                        {cap.availability && <span>{cap.availability}</span>}
                      </div>
                    </div>
                    <span className="text-xs text-gray-400 ml-2">{formatSimilarity(cap.similarity)}</span>
                  </div>
                ))}
                {items.length > 5 && (
                  <p className="text-xs text-gray-500 italic">+ {items.length - 5} autres</p>
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
function StepContent({ step }: { step: ProcessingStepLog }) {
  if (!step.output_data) return null

  switch (step.step_name) {
    case 'ocr_document':
      return <OcrResult data={step.output_data} />
    case 'retrieve_similar_references':
      return <ReferencesResult data={step.output_data} />
    case 'retrieve_historical_tenders':
      return <HistoricalResult data={step.output_data} />
    case 'retrieve_capabilities':
      return <CapabilitiesResult data={step.output_data} />
    default:
      return (
        <details className="bg-gray-50 p-3 rounded border border-gray-200">
          <summary className="text-xs text-gray-600 cursor-pointer hover:text-gray-800 font-medium">
            Donnees ({step.step_name})
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
  if (!['processing', 'completed', 'manual_review', 'failed'].includes(tender.status) && logs.length === 0) {
    return null
  }

  const steps = (status?.processing_steps && status.processing_steps.length > 0)
    ? status.processing_steps
    : logs

  return (
    <div className="bg-white shadow rounded-lg p-6">
      <h3 className="text-xl font-bold text-gray-900 mb-4">Etapes de Traitement</h3>

      {status && tender.status === 'processing' && (
        <div className="mb-4 p-4 bg-amber-50 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-amber-800">Analyse en cours...</p>
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
          const meta = STEP_LABELS[step.step_name] || { label: step.step_name, color: 'gray' }

          return (
            <div key={index} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <StepIcon status={step.status} />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <p className="text-sm font-semibold text-gray-900">{meta.label}</p>
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
                        {step.status === 'completed' ? 'OK' : step.status === 'failed' ? 'Erreur' : step.status}
                      </span>
                    </div>
                  </div>

                  {step.error_message && (
                    <p className="text-xs text-red-600 mt-1">{step.error_message}</p>
                  )}

                  <div className="mt-3">
                    <StepContent step={step} />
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
            <p className="text-gray-600">En attente du lancement de l'analyse...</p>
          </div>
        )}
      </div>
    </div>
  )
}
