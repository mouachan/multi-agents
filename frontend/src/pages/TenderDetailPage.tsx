import { useParams, Link } from 'react-router-dom'
import { useTender } from '../hooks/useTender'
import { useTenderPolling } from '../hooks/useTenderPolling'
import TenderHeader from '../components/tender/TenderHeader'
import TenderActions from '../components/tender/TenderActions'
import TenderDecision from '../components/tender/TenderDecision'
import TenderProcessingSteps from '../components/tender/TenderProcessingSteps'
import ReviewChatPanel from '../components/ReviewChatPanel'

export default function TenderDetailPage() {
  const { tenderId } = useParams<{ tenderId: string }>()

  const { tender, status, decision, logs, loading, error, reload } = useTender(tenderId)

  useTenderPolling(tender, {
    enabled: true,
    interval: 2000,
    onPoll: reload
  })

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-amber-600"></div>
      </div>
    )
  }

  if (error || !tender) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'Tender not found'}</p>
        <Link to="/tenders" className="text-amber-600 hover:text-amber-800 mt-2 inline-block">
          Retour aux AOs
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <Link to="/tenders" className="text-amber-600 hover:text-amber-800 flex items-center">
        <svg className="h-5 w-5 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
        </svg>
        Retour aux Appels d'Offres
      </Link>

      <TenderHeader tender={tender} logs={logs} />
      <TenderActions tender={tender} onProcessStart={reload} />
      <TenderProcessingSteps tender={tender} status={status} logs={logs} />
      {decision && <TenderDecision tender={tender} decision={decision} />}

      {tender.status === 'manual_review' && (
        <div className="bg-white shadow rounded-lg p-6">
          <ReviewChatPanel
            claimId={tender.id}
            reviewerId={`reviewer_${Date.now()}`}
            reviewerName="Review Agent"
            onActionSubmitted={(action) => {
              console.log('Action submitted:', action)
              reload()
            }}
          />
        </div>
      )}
    </div>
  )
}
