import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { claimsApi } from '../services/api'
import { tendersApi } from '../services/tenderApi'
import { useAgents } from '../hooks/useAgents'
import AgentCard from '../components/common/AgentCard'
import { useTranslation } from '../i18n/LanguageContext'
import type { ClaimStatistics } from '../types'
import type { TenderStatistics } from '../types/tender'

export default function HomePage() {
  const navigate = useNavigate()
  const { agents } = useAgents()
  const { t } = useTranslation()
  const [claimStats, setClaimStats] = useState<ClaimStatistics | null>(null)
  const [tenderStats, setTenderStats] = useState<TenderStatistics | null>(null)
  const [loading, setLoading] = useState(true)
  const [chatInput, setChatInput] = useState('')

  useEffect(() => {
    loadStatistics()
  }, [])

  const loadStatistics = async () => {
    try {
      setLoading(true)
      const [claims, tenders] = await Promise.allSettled([
        claimsApi.getStatistics(),
        tendersApi.getStatistics()
      ])
      if (claims.status === 'fulfilled') setClaimStats(claims.value)
      if (tenders.status === 'fulfilled') setTenderStats(tenders.value)
    } finally {
      setLoading(false)
    }
  }

  const handleChatSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!chatInput.trim()) return
    navigate('/chat')
  }

  const getAgentStats = (agentId: string) => {
    if (agentId === 'claims' && claimStats) {
      return {
        total: claimStats.total_claims,
        pending: claimStats.pending_claims,
        processing: claimStats.processing_claims,
        completed: claimStats.completed_claims,
      }
    }
    if (agentId === 'tenders' && tenderStats) {
      return {
        total: tenderStats.total_tenders,
        pending: tenderStats.pending_tenders,
        processing: tenderStats.processing_tenders,
        completed: tenderStats.completed_tenders,
      }
    }
    return undefined
  }

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header with chat input */}
      <div className="bg-white shadow rounded-lg p-6">
        <h2 className="text-3xl font-bold text-gray-900">{t('home.title')}</h2>
        <p className="mt-2 text-gray-600 mb-4">
          {t('home.subtitle')}
        </p>
        <form onSubmit={handleChatSubmit} className="flex gap-3">
          <input
            type="text"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            placeholder={t('home.placeholder')}
            className="flex-1 border border-gray-300 rounded-lg px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
          <button
            type="submit"
            className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            {t('home.start')}
          </button>
        </form>
      </div>

      {/* Agent Cards - dynamic from registry */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {agents.map((agent) => (
          <AgentCard
            key={agent.id}
            agent={agent}
            stats={getAgentStats(agent.id)}
            onViewClick={() => navigate(agent.path)}
            onChatClick={() => navigate(`/chat?agent=${agent.id}`)}
          />
        ))}
      </div>

      {/* Shared Infrastructure */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">{t('home.infrastructure')}</h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">{t('home.llamastack')}</h4>
            <p className="text-sm text-gray-600">{t('home.llamastackDesc')}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">{t('home.ocrServer')}</h4>
            <p className="text-sm text-gray-600">{t('home.ocrServerDesc')}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">{t('home.ragServer')}</h4>
            <p className="text-sm text-gray-600">{t('home.ragServerDesc')}</p>
          </div>
          <div className="border border-gray-200 rounded-lg p-4">
            <h4 className="font-semibold text-gray-900 mb-2">{t('home.piiGuardrails')}</h4>
            <p className="text-sm text-gray-600">{t('home.piiGuardrailsDesc')}</p>
          </div>
        </div>
      </div>

      <div className="text-center">
        <button
          onClick={loadStatistics}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-2 px-6 rounded-lg transition-colors"
        >
          {t('home.refreshStats')}
        </button>
      </div>
    </div>
  )
}
