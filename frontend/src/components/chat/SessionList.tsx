import { useState } from 'react'
import { MessageSquarePlus, Pencil, Trash2 } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { formatDate, formatTime } from '../../lib/format'
import type { ChatSession } from '../../types/chat'
import { Button, IconButton } from '../ui/Button'
import { ConfirmDialog, PromptDialog } from '../ui/Modal'
import { AgentAvatar } from './AgentAvatar'

const NAMES_KEY = 'chat-session-names'
const WELCOME = /^(Welcome! I'm the multi-agent|Bienvenue ! Je suis l'orchestrateur|Session started with agent|Session demarree avec l'agent)/

function loadNames(): Record<string, string> {
  try {
    return JSON.parse(localStorage.getItem(NAMES_KEY) || '{}')
  } catch {
    return {}
  }
}

interface SessionListProps {
  sessions: ChatSession[]
  currentId?: string
  onSelect: (id: string) => void
  onNew: () => void
  onDelete: (id: string) => Promise<void>
  onDeleteAll: () => Promise<void>
}

export function SessionList({ sessions, currentId, onSelect, onNew, onDelete, onDeleteAll }: SessionListProps) {
  const { t, locale } = useTranslation()
  const [names, setNames] = useState<Record<string, string>>(loadNames)
  const [renaming, setRenaming] = useState<ChatSession | null>(null)
  const [deleting, setDeleting] = useState<ChatSession | null>(null)
  const [deletingAll, setDeletingAll] = useState(false)

  const title = (s: ChatSession) => {
    if (names[s.session_id]) return names[s.session_id]
    const last = (s.last_message || '').replace(/[*_`#>|]/g, '').replace(/\s+/g, ' ').trim()
    if (!last || WELCOME.test(last)) return t('conv.newChat')
    return last.slice(0, 60)
  }

  const rename = (id: string, value: string) => {
    const next = { ...names, [id]: value }
    setNames(next)
    localStorage.setItem(NAMES_KEY, JSON.stringify(next))
  }

  const today = new Date().toDateString()
  const when = (s: ChatSession) => {
    const d = s.updated_at || s.created_at
    if (!d) return ''
    return new Date(d).toDateString() === today ? formatTime(d, locale) : formatDate(d, locale)
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center justify-between gap-2 px-3 pb-2 pt-3">
        <h3 className="label">{t('conv.sessions')}</h3>
        {sessions.length > 0 && (
          <button onClick={() => setDeletingAll(true)} className="text-[11px] font-medium text-ink-subtle hover:text-red-600">
            {t('conv.deleteAll')}
          </button>
        )}
      </div>
      <div className="px-3 pb-2">
        <Button variant="primary" size="sm" className="w-full" icon={<MessageSquarePlus className="h-4 w-4" />} onClick={onNew}>
          {t('conv.newChat')}
        </Button>
      </div>
      <div className="flex-1 space-y-0.5 overflow-y-auto px-2 pb-3">
        {sessions.length === 0 && <p className="px-2 py-6 text-center text-xs text-ink-subtle">{t('conv.noSessions')}</p>}
        {sessions.map((s) => {
          const active = s.session_id === currentId
          return (
            <div
              key={s.session_id}
              onClick={() => onSelect(s.session_id)}
              className={cn(
                'group flex cursor-pointer items-center gap-2.5 rounded-xl px-2 py-2 transition-colors',
                active ? 'bg-brand-500/10' : 'hover:bg-surface-muted',
              )}
            >
              <AgentAvatar agentId={s.agent_id} size="sm" />
              <div className="min-w-0 flex-1">
                <p className={cn('truncate text-xs font-medium', active ? 'text-brand-700 dark:text-brand-300' : 'text-ink')}>{title(s)}</p>
                <p className="truncate text-[10px] text-ink-subtle">{t(`agentNames.${s.agent_id || 'orchestrator'}`)} · {when(s)}</p>
              </div>
              <div className="flex opacity-0 transition-opacity group-hover:opacity-100">
                <IconButton
                  label={t('conv.rename')}
                  className="h-6 w-6"
                  icon={<Pencil className="h-3 w-3" />}
                  onClick={(e) => { e.stopPropagation(); setRenaming(s) }}
                />
                <IconButton
                  label={t('conv.delete')}
                  className="h-6 w-6 hover:text-red-600"
                  icon={<Trash2 className="h-3 w-3" />}
                  onClick={(e) => { e.stopPropagation(); setDeleting(s) }}
                />
              </div>
            </div>
          )
        })}
      </div>

      <PromptDialog
        open={!!renaming}
        title={t('conv.renameTitle')}
        label={t('conv.renameLabel')}
        initialValue={renaming ? title(renaming) : ''}
        confirmLabel={t('ui.save')}
        cancelLabel={t('ui.cancel')}
        onCancel={() => setRenaming(null)}
        onSubmit={(value) => { if (renaming) rename(renaming.session_id, value); setRenaming(null) }}
      />
      <ConfirmDialog
        open={!!deleting}
        danger
        title={t('conv.deleteTitle')}
        message={t('conv.deleteMessage')}
        confirmLabel={t('conv.delete')}
        cancelLabel={t('ui.cancel')}
        onCancel={() => setDeleting(null)}
        onConfirm={async () => { const s = deleting; setDeleting(null); if (s) await onDelete(s.session_id) }}
      />
      <ConfirmDialog
        open={deletingAll}
        danger
        title={t('conv.deleteAllTitle')}
        message={t('conv.deleteAllMessage')}
        confirmLabel={t('conv.deleteAll')}
        cancelLabel={t('ui.cancel')}
        onCancel={() => setDeletingAll(false)}
        onConfirm={async () => { setDeletingAll(false); await onDeleteAll() }}
      />
    </div>
  )
}
