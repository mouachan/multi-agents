import { useState } from 'react'
import { Gavel } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import type { AgentView } from '../../types/review'
import { Button } from '../ui/Button'
import { type Tone } from '../ui/Badge'
import { ErrorBanner } from '../ui/Feedback'
import { ConfirmDialog } from '../ui/Modal'

const TONE_BUTTONS: Partial<Record<Tone, string>> = {
  success: 'ring-emerald-500/40 bg-emerald-500/10 text-emerald-700 dark:text-emerald-300',
  danger: 'ring-red-500/40 bg-red-500/10 text-red-700 dark:text-red-300',
  info: 'ring-sky-500/40 bg-sky-500/10 text-sky-700 dark:text-sky-300',
  warning: 'ring-amber-500/40 bg-amber-500/10 text-amber-700 dark:text-amber-300',
}

/**
 * The reviewer's decision: one of the domain's choices (the agent's suggestion is preselected), a
 * justification — required when going against the agent — and a confirmation showing the outcome.
 */
export function DecisionForm({ number, choices, agent, tones, onDecide }: {
  number: string
  choices: { decision: string; status: string }[]
  agent: AgentView
  tones: Record<string, Tone>
  onDecide: (decision: string, justification: string) => Promise<void>
}) {
  const { t } = useTranslation()
  const [choice, setChoice] = useState(agent.suggestion ?? '')
  const [justification, setJustification] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const againstAgent = !!agent.suggestion && choice !== agent.suggestion
  const missingJustification = againstAgent && !justification.trim()
  const outcome = choices.find((c) => c.decision === choice)?.status

  const decide = async () => {
    setConfirming(false)
    setSaving(true)
    setError(null)
    try {
      await onDecide(choice, justification.trim())
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || t('review.decideFailed'))
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {choices.map(({ decision }) => (
          <button
            key={decision}
            type="button"
            onClick={() => setChoice(decision)}
            className={cn(
              'rounded-xl px-4 py-2 text-sm font-semibold ring-1 ring-inset transition-colors',
              choice === decision ? TONE_BUTTONS[tones[decision]] ?? 'ring-brand-500/40 bg-brand-500/10 text-brand-700'
                : 'ring-line text-ink-muted hover:bg-surface-muted',
            )}
          >
            {t(`decision.${decision}`, decision)}
            {decision === agent.suggestion && <span className="ml-1.5 text-[10px] font-normal opacity-70">({t('review.agentChoice')})</span>}
          </button>
        ))}
      </div>
      <textarea
        className="input min-h-[72px]"
        value={justification}
        onChange={(e) => setJustification(e.target.value)}
        placeholder={againstAgent ? t('review.justificationRequired') : t('review.justificationOptional')}
      />
      {error && <ErrorBanner>{error}</ErrorBanner>}
      <Button
        variant="primary" size="md" className="w-full" icon={<Gavel className="h-4 w-4" />}
        loading={saving} disabled={!choice || missingJustification} onClick={() => setConfirming(true)}
      >
        {t('review.decide')}
      </Button>
      <ConfirmDialog
        open={confirming}
        title={t('review.confirmTitle')}
        message={`${number} → ${t(`decision.${choice}`, choice)} (${t(`status.${outcome}`, outcome ?? '')})`}
        confirmLabel={t('review.decide')}
        cancelLabel={t('ui.cancel')}
        onCancel={() => setConfirming(false)}
        onConfirm={decide}
      />
    </div>
  )
}
