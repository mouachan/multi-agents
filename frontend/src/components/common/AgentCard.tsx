import type { AgentInfo } from '../../types/chat'
import { useTranslation } from '../../i18n/LanguageContext'

interface AgentCardProps {
  agent: AgentInfo
  stats?: {
    total: number
    pending: number
    processing: number
    completed: number
  }
  onChatClick?: () => void
  onViewClick?: () => void
}

const colorMap: Record<string, { border: string; bg: string; text: string; button: string; hover: string }> = {
  blue: {
    border: 'border-blue-500',
    bg: 'bg-blue-500',
    text: 'text-blue-700',
    button: 'bg-blue-600 hover:bg-blue-700',
    hover: 'bg-blue-50',
  },
  amber: {
    border: 'border-amber-500',
    bg: 'bg-amber-500',
    text: 'text-amber-700',
    button: 'bg-amber-600 hover:bg-amber-700',
    hover: 'bg-amber-50',
  },
  yellow: {
    border: 'border-yellow-500',
    bg: 'bg-yellow-500',
    text: 'text-yellow-700',
    button: 'bg-yellow-600 hover:bg-yellow-700',
    hover: 'bg-yellow-50',
  },
  green: {
    border: 'border-green-500',
    bg: 'bg-green-500',
    text: 'text-green-700',
    button: 'bg-green-600 hover:bg-green-700',
    hover: 'bg-green-50',
  },
  emerald: {
    border: 'border-emerald-500',
    bg: 'bg-emerald-500',
    text: 'text-emerald-700',
    button: 'bg-emerald-600 hover:bg-emerald-700',
    hover: 'bg-emerald-50',
  },
  purple: {
    border: 'border-purple-500',
    bg: 'bg-purple-500',
    text: 'text-purple-700',
    button: 'bg-purple-600 hover:bg-purple-700',
    hover: 'bg-purple-50',
  },
}

export default function AgentCard({ agent, stats, onChatClick, onViewClick }: AgentCardProps) {
  const colors = colorMap[agent.color] || colorMap.blue
  const { t, locale } = useTranslation()
  const agentName = locale === 'fr' && agent.name_fr ? agent.name_fr : agent.name
  const agentDesc = locale === 'fr' && agent.description_fr ? agent.description_fr : agent.description

  return (
    <div className={`bg-white shadow rounded-lg p-6 border-t-4 ${colors.border}`}>
      <div className="flex items-center mb-4">
        <div className={`flex-shrink-0 ${colors.bg} rounded-md p-3`}>
          <svg className="h-6 w-6 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            {agent.icon === 'building' ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            ) : agent.icon === 'package' ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" />
            ) : agent.icon === 'info' ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            ) : agent.icon === 'truck' ? (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16V6a1 1 0 00-1-1H4a1 1 0 00-1 1v10a1 1 0 001 1h1m8-1a1 1 0 01-1 1H9m4-1V8a1 1 0 011-1h2.586a1 1 0 01.707.293l3.414 3.414a1 1 0 01.293.707V16a1 1 0 01-1 1h-1m-6-1a1 1 0 001 1h1M5 17a2 2 0 104 0m-4 0a2 2 0 114 0m6 0a2 2 0 104 0m-4 0a2 2 0 114 0" />
            ) : (
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            )}
          </svg>
        </div>
        <div className="ml-4">
          <h3 className="text-xl font-bold text-gray-900">{agentName}</h3>
          <p className="text-sm text-gray-500">{agentDesc}</p>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className={`${colors.hover} rounded-lg p-3 text-center`}>
            <p className={`text-2xl font-bold ${colors.text}`}>{stats.total}</p>
            <p className="text-xs text-gray-600">{t('common.total')}</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-yellow-700">{stats.pending}</p>
            <p className="text-xs text-gray-600">{t('agentCard.pending')}</p>
          </div>
          <div className="bg-orange-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-orange-700">{stats.processing}</p>
            <p className="text-xs text-gray-600">{t('agentCard.processing')}</p>
          </div>
          <div className="bg-green-50 rounded-lg p-3 text-center">
            <p className="text-2xl font-bold text-green-700">{stats.completed}</p>
            <p className="text-xs text-gray-600">{t('agentCard.completed')}</p>
          </div>
        </div>
      )}

      <div className="flex gap-2">
        {onViewClick && (
          <button
            onClick={onViewClick}
            className={`flex-1 text-center ${colors.button} text-white font-medium py-3 px-4 rounded-lg transition-colors`}
          >
            {t('agentCard.view')}
          </button>
        )}
        {onChatClick && (
          <button
            onClick={onChatClick}
            className="flex-1 text-center bg-gray-100 hover:bg-gray-200 text-gray-700 font-medium py-3 px-4 rounded-lg transition-colors"
          >
            {t('agentCard.chat')}
          </button>
        )}
      </div>
    </div>
  )
}
