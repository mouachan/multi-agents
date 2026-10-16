import { useState } from 'react'
import { CheckSquare, HelpCircle, Square } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import type { AgentView } from '../../types/review'
import { Badge, type Tone } from '../ui/Badge'
import { MaskedText } from '../ui/Markdown'

/** Why the agent hands the case over: its conclusion, confidence, reasons, and what to check. */
export function AgentBrief({ agent, tones }: { agent: AgentView; tones: Record<string, Tone> }) {
  const { t } = useTranslation()
  const [checked, setChecked] = useState<Set<number>>(new Set())
  const toggle = (i: number) => setChecked((s) => (s.has(i) ? new Set([...s].filter((x) => x !== i)) : new Set(s).add(i)))
  const pct = agent.confidence == null ? null : Math.round(agent.confidence * 100)

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2 text-sm text-ink">
        <HelpCircle className="h-4 w-4 text-violet-500" />
        {agent.suggestion ? (
          <>
            {t('review.agentLeans')}
            <Badge tone={tones[agent.suggestion] ?? 'neutral'}>{t(`decision.${agent.suggestion}`, agent.suggestion)}</Badge>
          </>
        ) : t('review.agentUndecided')}
        {pct != null && <span className="text-xs text-ink-subtle">· {t('ui.confidence')} {pct}%</span>}
      </div>

      {agent.reasons.length > 0 && (
        <div>
          <p className="label mb-1.5">{t('review.reasons')}</p>
          <ul className="list-inside list-disc space-y-1 text-sm text-ink-muted">
            {agent.reasons.map((reason, i) => <li key={i}><MaskedText text={reason} /></li>)}
          </ul>
        </div>
      )}

      {agent.checks.length > 0 && (
        <div>
          <p className="label mb-1.5">{t('review.checks')}</p>
          <ul className="space-y-1">
            {agent.checks.map((check, i) => (
              <li key={i}>
                <button type="button" onClick={() => toggle(i)} className="flex items-start gap-2 text-left text-sm text-ink-muted hover:text-ink">
                  {checked.has(i) ? <CheckSquare className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" /> : <Square className="mt-0.5 h-4 w-4 shrink-0" />}
                  <span className={checked.has(i) ? 'line-through opacity-70' : ''}><MaskedText text={check} /></span>
                </button>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}
