import { AlertTriangle, ArrowRight, Clock, Cpu, Hash, Square, User, Workflow } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { useNow } from '../../hooks/useNow'
import { agentVisual } from '../../lib/agents'
import { cn } from '../../lib/cn'
import { formatDuration, formatTime } from '../../lib/format'
import type { ChatMessage, SuggestedAction } from '../../types/chat'
import { Markdown } from '../ui/Markdown'
import { AgentAvatar } from './AgentAvatar'
import { ToolChips } from './ToolChips'

interface MessageBubbleProps {
  message: ChatMessage
  selected?: boolean
  onSelectTrace?: (messageId: string) => void
  onActionClick?: (action: SuggestedAction) => void
}

function ThinkingIndicator({ startedAt }: { startedAt: number }) {
  const { t } = useTranslation()
  const now = useNow(true, 1000)
  return (
    <div className="flex items-center gap-2 py-1 text-sm text-ink-muted">
      <span className="flex gap-1">
        {[0, 1, 2].map((i) => (
          <span key={i} className="h-1.5 w-1.5 animate-pulse-dot rounded-full bg-brand-500" style={{ animationDelay: `${i * 0.18}s` }} />
        ))}
      </span>
      {t('conv.thinking')} <span className="tabular-nums text-ink-subtle">{formatDuration(now - startedAt)}</span>
    </div>
  )
}

export function MessageBubble({ message, selected, onSelectTrace, onActionClick }: MessageBubbleProps) {
  const { t, locale } = useTranslation()

  if (message.role === 'system') {
    return (
      <div className="my-3 flex justify-center">
        <span className="chip">{message.content}</span>
      </div>
    )
  }

  if (message.role === 'user') {
    return (
      <div className="flex animate-fade-in justify-end gap-2.5">
        <div className="max-w-[80%] rounded-2xl rounded-br-md bg-brand-600 px-4 py-2.5 text-sm leading-relaxed text-white shadow-sm">
          <p className="whitespace-pre-wrap">{message.content}</p>
          {message.created_at && (
            <p className="mt-1 text-right text-[10px] text-white/60">{formatTime(message.created_at, locale)}</p>
          )}
        </div>
        <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-surface-sunken text-ink-muted ring-1 ring-line">
          <User className="h-4 w-4" />
        </div>
      </div>
    )
  }

  const v = agentVisual(message.agent_id)
  const agentName = t(`agentNames.${message.agent_id || 'orchestrator'}`)
  const streaming = !!message.streaming
  const empty = !message.content
  const hasTrace = !!message.trace && message.trace.steps.length > 0
  const usage = message.token_usage

  return (
    <div className="flex animate-fade-in gap-2.5">
      <AgentAvatar agentId={message.agent_id} />
      <div className="min-w-0 max-w-[85%] flex-1">
        <div className="mb-1 flex items-center gap-2">
          <span className={cn('text-xs font-semibold', v.accent.text)}>{agentName}</span>
          {hasTrace && onSelectTrace && (
            <button
              onClick={() => onSelectTrace(message.id)}
              className={cn(
                'inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium transition-colors',
                selected ? 'bg-brand-500/15 text-brand-700 dark:text-brand-300' : 'text-ink-subtle hover:bg-surface-muted hover:text-ink-muted',
              )}
            >
              <Workflow className="h-3 w-3" />
              {t('a2a.trace')}
            </button>
          )}
        </div>

        <ToolChips toolCalls={message.tool_calls ?? []} />

        <div
          className={cn(
            'rounded-2xl rounded-tl-md border bg-surface px-4 py-3 shadow-card transition-shadow',
            selected ? 'border-brand-500/40 ring-4 ring-brand-500/10' : 'border-line',
          )}
        >
          {empty && streaming && <ThinkingIndicator startedAt={message.trace?.startedAt ?? Date.now()} />}
          {!empty && (
            <div className="text-[14px] text-ink">
              <Markdown>{message.content}</Markdown>
              {streaming && <span className="ml-0.5 inline-block h-4 w-1.5 translate-y-0.5 animate-pulse rounded-sm bg-brand-500" />}
            </div>
          )}
          {empty && !streaming && !message.error && (
            <p className="text-sm italic text-ink-subtle">{message.stopped ? t('conv.stopped') : t('conv.noAnswer')}</p>
          )}
          {message.error && (
            <div className="mt-1 flex items-center gap-2 text-xs text-red-600 dark:text-red-400">
              <AlertTriangle className="h-3.5 w-3.5" /> {message.error}
            </div>
          )}
          {message.stopped && !empty && (
            <div className="mt-2 flex items-center gap-1.5 text-[11px] text-ink-subtle">
              <Square className="h-3 w-3" /> {t('conv.stopped')}
            </div>
          )}

          {!streaming && (message.processing_time_ms || usage?.total_tokens || message.model_id) && (
            <div className="mt-2.5 flex flex-wrap items-center gap-x-3 gap-y-1 border-t border-line pt-2 text-[11px] text-ink-subtle">
              {message.created_at && <span>{formatTime(message.created_at, locale)}</span>}
              {!!message.processing_time_ms && (
                <span className="inline-flex items-center gap-1"><Clock className="h-3 w-3" />{formatDuration(message.processing_time_ms)}</span>
              )}
              {!!usage?.total_tokens && (
                <span className="inline-flex items-center gap-1" title={`${usage.prompt_tokens} + ${usage.completion_tokens}`}>
                  <Hash className="h-3 w-3" />{usage.total_tokens.toLocaleString()} tokens
                </span>
              )}
              {message.model_id && (
                <span className="inline-flex items-center gap-1"><Cpu className="h-3 w-3" />{message.model_id}</span>
              )}
            </div>
          )}
        </div>

        {!streaming && !!message.suggested_actions?.length && onActionClick && (
          <div className="mt-2 flex flex-wrap gap-1.5">
            {message.suggested_actions.map((a, i) => (
              <button
                key={i}
                onClick={() => onActionClick(a)}
                className="chip transition-colors hover:border-brand-500/40 hover:text-brand-700 dark:hover:text-brand-300"
              >
                {a.label}
                <ArrowRight className="h-3 w-3" />
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}
