import type { SuggestedAction } from '../../types/chat'
import { useTranslation } from '../../i18n/LanguageContext'

interface SuggestedActionsProps {
  actions: SuggestedAction[]
  onActionClick: (action: SuggestedAction) => void
}

export default function SuggestedActions({ actions, onActionClick }: SuggestedActionsProps) {
  const { t } = useTranslation()
  if (!actions || actions.length === 0) return null

  return (
    <div className="flex flex-wrap gap-2 p-3 bg-blue-50 rounded-lg border border-blue-100">
      <span className="text-xs text-blue-600 font-medium w-full mb-1">
        {t('chat.suggestedActions')}
      </span>
      {actions.map((action, idx) => (
        <button
          key={idx}
          onClick={() => onActionClick(action)}
          className="text-sm bg-white text-blue-700 border border-blue-200 rounded-lg px-4 py-2 hover:bg-blue-100 hover:border-blue-300 transition-colors shadow-sm"
        >
          {action.label}
        </button>
      ))}
    </div>
  )
}
