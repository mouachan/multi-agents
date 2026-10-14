import { Bot, MessagesSquare, UserRound } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { formatDateTime } from '../../lib/format'
import type { AgentLogEntry } from '../../types'
import { Card, CardHeader } from '../ui/Card'
import { MaskedText } from '../ui/Markdown'

/** Reviewer <-> agent exchanges recorded on a claim / tender / complaint. */
export function AgentLogs({ logs }: { logs: AgentLogEntry[] }) {
  const { t, locale } = useTranslation()
  if (!logs.length) return null
  return (
    <Card>
      <CardHeader icon={<MessagesSquare className="h-4 w-4" />} title={t('processingSteps.reviewerConversation')} />
      <ul className="space-y-3 p-5">
        {logs.map((log, i) => {
          const agent = log.type === 'agent_answer'
          return (
            <li key={i} className="flex gap-3">
              <span className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ${agent ? 'bg-brand-500/10 text-brand-600 dark:text-brand-300' : 'bg-surface-muted text-ink-muted'}`}>
                {agent ? <Bot className="h-3.5 w-3.5" /> : <UserRound className="h-3.5 w-3.5" />}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-[11px] text-ink-subtle">
                  <span className="font-medium text-ink-muted">{agent ? t('processingSteps.agentResponse') : (log.reviewer_name || t('processingSteps.reviewer'))}</span>
                  {' · '}{log.type.replace(/_/g, ' ')} · {formatDateTime(log.timestamp, locale)}
                </p>
                <p className="mt-0.5 whitespace-pre-wrap text-sm leading-relaxed text-ink"><MaskedText text={log.message} /></p>
              </div>
            </li>
          )
        })}
      </ul>
    </Card>
  )
}
