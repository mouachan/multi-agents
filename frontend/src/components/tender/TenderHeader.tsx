import { useState } from 'react'
import type { Tender, ProcessingStepLog } from '../../types/tender'

interface TenderHeaderProps {
  tender: Tender
  logs?: ProcessingStepLog[]
}

export default function TenderHeader({ tender }: TenderHeaderProps) {
  const [showPdf, setShowPdf] = useState(false)

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pending: 'bg-gray-100 text-gray-800',
      processing: 'bg-amber-100 text-amber-800',
      completed: 'bg-green-100 text-green-800',
      failed: 'bg-red-100 text-red-800',
      manual_review: 'bg-orange-100 text-orange-800'
    }
    return colors[status] || 'bg-gray-100 text-gray-800'
  }

  const getStatusLabel = (status: string) => {
    const labels: Record<string, string> = {
      pending: 'EN ATTENTE',
      processing: 'EN COURS',
      completed: 'TERMINE',
      failed: 'ECHOUE',
      manual_review: 'REVUE MANUELLE'
    }
    return labels[status] || status.toUpperCase()
  }

  const formatDate = (dateString: string | null | undefined) => {
    if (!dateString) return 'N/A'
    return new Date(dateString).toLocaleString('fr-FR')
  }

  const formatAmount = (amount: number | null | undefined) => {
    if (!amount) return 'N/A'
    return new Intl.NumberFormat('fr-FR', { style: 'currency', currency: 'EUR', maximumFractionDigits: 0 }).format(amount)
  }

  // Extract info from tender metadata (JSONB)
  const meta = tender.metadata || {}
  const titre = meta.titre || tender.objet_marche
  const description = meta.description
  const maitreOuvrage = meta.maitre_ouvrage || tender.maitre_ouvrage
  const montant = meta.montant_estime || tender.montant_estime
  const natureTravaux = meta.nature_travaux || tender.tender_type
  const region = meta.region
  const commune = meta.commune
  const dateLimite = meta.date_limite_remise || tender.date_limite_reponse
  const delaiMois = meta.delai_execution_mois || tender.delai_execution
  const maitreOeuvre = meta.maitre_oeuvre
  const lots = meta.lots || []
  const criteres = meta.criteres_attribution
  const exigences = meta.exigences_specifiques || []

  const pdfUrl = `/api/v1/tenders/documents/${tender.id}/view`

  return (
    <div className="bg-white shadow rounded-lg overflow-hidden">
      {/* Top bar */}
      <div className="px-6 py-4 flex justify-between items-start border-b border-gray-100">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">{tender.tender_number}</h2>
          {natureTravaux && (
            <p className="text-sm text-amber-700 font-medium mt-1">{natureTravaux}</p>
          )}
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowPdf(!showPdf)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white text-sm font-medium rounded-lg transition-colors"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            {showPdf ? 'Masquer le PDF' : 'Voir le document AO'}
          </button>
          <span className={`px-4 py-2 text-sm font-semibold rounded-full ${getStatusColor(tender.status)}`}>
            {getStatusLabel(tender.status)}
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
            title="Document AO"
          />
        </div>
      )}

      {/* Titre / Objet du marche */}
      {titre && (
        <div className="mx-6 mt-4 p-4 bg-gradient-to-r from-amber-50 to-orange-50 border border-amber-200 rounded-lg">
          <p className="text-xs text-amber-700 font-semibold uppercase tracking-wide mb-1">Objet du Marche</p>
          <p className="text-lg font-semibold text-gray-900">{titre}</p>
          {description && (
            <p className="text-sm text-gray-600 mt-2 line-clamp-3">{description}</p>
          )}
        </div>
      )}

      {/* Key info grid */}
      <div className="px-6 py-4 grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-gray-500 font-medium">Maitre d'Ouvrage</p>
          <p className="text-sm font-semibold text-gray-900">{maitreOuvrage || 'N/A'}</p>
        </div>
        {maitreOeuvre && (
          <div>
            <p className="text-xs text-gray-500 font-medium">Maitre d'Oeuvre</p>
            <p className="text-sm font-semibold text-gray-900">{maitreOeuvre}</p>
          </div>
        )}
        <div>
          <p className="text-xs text-gray-500 font-medium">Montant Estime</p>
          <p className="text-sm font-bold text-amber-700">{formatAmount(montant)}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 font-medium">Delai d'Execution</p>
          <p className="text-sm font-semibold text-gray-900">{delaiMois ? `${delaiMois} mois` : 'N/A'}</p>
        </div>
        {region && (
          <div>
            <p className="text-xs text-gray-500 font-medium">Region</p>
            <p className="text-sm font-semibold text-gray-900">{region}{commune ? ` - ${commune}` : ''}</p>
          </div>
        )}
        <div>
          <p className="text-xs text-gray-500 font-medium">Date Limite de Remise</p>
          <p className="text-sm font-semibold text-gray-900">{dateLimite || 'N/A'}</p>
        </div>
        <div>
          <p className="text-xs text-gray-500 font-medium">Soumis le</p>
          <p className="text-sm font-semibold text-gray-900">{formatDate(tender.submitted_at)}</p>
        </div>
        {tender.processed_at && (
          <div>
            <p className="text-xs text-gray-500 font-medium">Traite en</p>
            <p className="text-sm font-semibold text-gray-900">
              {tender.total_processing_time_ms
                ? `${(tender.total_processing_time_ms / 1000).toFixed(1)}s`
                : formatDate(tender.processed_at)}
            </p>
          </div>
        )}
      </div>

      {/* Criteres d'attribution */}
      {criteres && (
        <div className="px-6 pb-4">
          <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-2">Criteres d'Attribution</p>
          <div className="flex gap-3">
            {Object.entries(criteres).map(([key, value]) => (
              <div key={key} className="flex items-center gap-1 px-3 py-1 bg-blue-50 border border-blue-200 rounded-full">
                <span className="text-xs font-medium text-blue-800 capitalize">{key}</span>
                <span className="text-xs font-bold text-blue-900">{String(value)}%</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lots */}
      {lots.length > 0 && (
        <div className="px-6 pb-4">
          <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-2">Lots</p>
          <div className="flex flex-wrap gap-2">
            {lots.map((lot: string, i: number) => (
              <span key={i} className="text-xs px-3 py-1 bg-gray-100 text-gray-700 rounded-full">{lot}</span>
            ))}
          </div>
        </div>
      )}

      {/* Exigences specifiques */}
      {exigences.length > 0 && (
        <div className="px-6 pb-4">
          <p className="text-xs text-gray-500 font-semibold uppercase tracking-wide mb-2">Exigences Specifiques</p>
          <div className="flex flex-wrap gap-2">
            {exigences.map((ex: string, i: number) => (
              <span key={i} className="text-xs px-3 py-1 bg-red-50 text-red-700 border border-red-200 rounded-full">{ex}</span>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
