import { useState } from 'react'
import type { Tender } from '../../types/tender'
import { tenderService } from '../../services/tenderService'

interface TenderActionsProps {
  tender: Tender
  onProcessStart?: () => void
}

export default function TenderActions({ tender, onProcessStart }: TenderActionsProps) {
  const [processing, setProcessing] = useState(false)

  const handleProcessTender = async () => {
    try {
      setProcessing(true)
      await tenderService.processTender(tender.id)
      onProcessStart?.()
    } catch (error) {
      console.error('Error processing tender:', error)
      alert('Failed to process tender')
    } finally {
      setProcessing(false)
    }
  }

  if (!tenderService.canProcess(tender)) {
    return null
  }

  return (
    <div className="mt-6">
      <button
        onClick={handleProcessTender}
        disabled={processing}
        className="bg-amber-600 hover:bg-amber-700 text-white font-medium py-3 px-8 rounded-lg transition-colors disabled:opacity-50"
      >
        {processing ? 'Analyse en cours...' : "Analyser l'AO"}
      </button>
    </div>
  )
}
