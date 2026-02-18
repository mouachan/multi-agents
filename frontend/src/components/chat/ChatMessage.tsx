import Markdown from 'react-markdown'
import type { ChatMessage as ChatMessageType, SuggestedAction } from '../../types/chat'
import { useTranslation } from '../../i18n/LanguageContext'

interface ChatMessageProps {
  message: ChatMessageType
  onActionClick?: (action: SuggestedAction) => void
}

function AgentAvatar({ agentId }: { agentId?: string }) {
  const config: Record<string, { bg: string; label: string }> = {
    orchestrator: { bg: 'bg-blue-600', label: 'HUB' },
    claims: { bg: 'bg-blue-500', label: 'SI' },
    tenders: { bg: 'bg-amber-500', label: 'AO' },
  }
  const c = config[agentId || 'orchestrator'] || config.orchestrator
  return (
    <div className={`w-8 h-8 rounded-lg ${c.bg} flex items-center justify-center flex-shrink-0`}>
      <span className="text-white text-xs font-bold">{c.label}</span>
    </div>
  )
}

export default function ChatMessage({ message, onActionClick }: ChatMessageProps) {
  const isUser = message.role === 'user'
  const isSystem = message.role === 'system'
  const { t } = useTranslation()

  const agentDisplayName = (agentId?: string): string => {
    if (!agentId) return t('agentNames.orchestrator')
    return t(`agentNames.${agentId}`) || agentId
  }

  if (isSystem) {
    return (
      <div className="flex justify-center my-3">
        <div className="bg-gray-100 text-gray-500 text-xs px-4 py-1.5 rounded-full">
          {message.content}
        </div>
      </div>
    )
  }

  if (isUser) {
    return (
      <div className="flex justify-end mb-4">
        <div className="flex items-end gap-2 max-w-[70%]">
          <div className="bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2.5 shadow-sm">
            <div className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</div>
            {message.created_at && (
              <div className="text-[10px] text-blue-200 mt-1 text-right">
                {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>
          <div className="w-8 h-8 rounded-lg bg-gray-300 flex items-center justify-center flex-shrink-0">
            <svg className="w-4 h-4 text-gray-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
            </svg>
          </div>
        </div>
      </div>
    )
  }

  // Assistant message
  return (
    <div className="flex justify-start mb-4">
      <div className="flex items-start gap-2 max-w-[75%]">
        <AgentAvatar agentId={message.agent_id} />
        <div>
          {/* Agent name */}
          <div className="text-xs font-medium text-gray-500 mb-1 ml-1">
            {agentDisplayName(message.agent_id)}
          </div>

          <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-md px-4 py-2.5 shadow-sm">
            <div className="text-sm text-gray-800 leading-relaxed prose prose-sm max-w-none prose-a:text-blue-600 prose-a:underline">
              <Markdown
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                }}
              >
                {message.content}
              </Markdown>
            </div>

            {message.created_at && (
              <div className="text-[10px] text-gray-400 mt-1">
                {new Date(message.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            )}
          </div>

          {/* Suggested actions */}
          {message.suggested_actions && message.suggested_actions.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5 ml-1">
              {message.suggested_actions.map((action, idx) => (
                <button
                  key={idx}
                  onClick={() => onActionClick?.(action)}
                  className="text-xs bg-blue-50 text-blue-700 border border-blue-200 rounded-lg px-3 py-1.5 hover:bg-blue-100 hover:border-blue-300 transition-colors"
                >
                  {action.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
