import { CheckCircle2, UserCheck } from 'lucide-react'
import type { DomainUI } from '../../domains'
import { useResource } from '../../hooks/useResource'
import { useTranslation } from '../../i18n/LanguageContext'
import { formatDateTime } from '../../lib/format'
import { reviewApi } from '../../services/api'
import type { JournalEntry } from '../../types/review'
import { Badge } from '../ui/Badge'
import { Card, CardHeader } from '../ui/Card'
import { ErrorBanner, PageLoader } from '../ui/Feedback'
import { MaskedText } from '../ui/Markdown'
import { AgentBrief } from './AgentBrief'
import { AskAgent } from './AskAgent'
import { DecisionForm } from './DecisionForm'

type Question = Extract<JournalEntry, { type: 'question' }>

/**
 * Human review of a case (backend/app/services/review.py): why the agent hands it over, questions to
 * the agent, then the reviewer's decision. The facts of the processing are in the evidence card.
 */
export function ReviewPanel({ ui, caseId, onDecided }: { ui: DomainUI; caseId: string; onDecided: () => void }) {
  const { t, locale } = useTranslation()
  const { data: brief, error, reload, setData } = useResource(() => reviewApi.brief(ui.name, caseId), [ui.name, caseId])

  if (error) return <ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error}</ErrorBanner>
  if (!brief) return <PageLoader />

  const questions = brief.journal.filter((entry): entry is Question => entry.type === 'question')
  const reviewer = brief.decision.reviewer

  const ask = async (question: string) => {
    const entry = await reviewApi.ask(ui.name, caseId, question, locale)
    setData({ ...brief, journal: [...brief.journal, entry] })
  }
  const decide = async (decision: string, justification: string) => {
    await reviewApi.decide(ui.name, caseId, decision, justification)
    await reload()
    onDecided()
  }

  return (
    <Card className="ring-2 ring-violet-500/20">
      <CardHeader
        icon={<UserCheck className="h-4 w-4 text-violet-500" />}
        title={t('review.title')}
        subtitle={brief.awaiting_review ? t('review.waiting') : undefined}
      />
      <div className="space-y-6 p-5">
        {reviewer && (
          <div className="flex items-start gap-2 rounded-xl bg-emerald-500/10 p-3 text-sm text-emerald-800 dark:text-emerald-200">
            <CheckCircle2 className="mt-0.5 h-4 w-4 shrink-0" />
            <div>
              <p>
                {t('review.decidedBy')} <b>{reviewer.user}</b> · {formatDateTime(reviewer.decided_at, locale)} :{' '}
                <Badge tone={ui.decisionTones[reviewer.decision] ?? 'neutral'}>{t(`decision.${reviewer.decision}`, reviewer.decision)}</Badge>
              </p>
              {reviewer.justification && <p className="mt-1 opacity-80"><MaskedText text={reviewer.justification} /></p>}
            </div>
          </div>
        )}

        <section>
          <p className="mb-3 text-sm font-semibold text-ink">1. {t('review.why')}</p>
          <AgentBrief agent={brief.agent} tones={ui.decisionTones} />
        </section>

        <section>
          <p className="mb-3 text-sm font-semibold text-ink">2. {t('review.askTitle')}</p>
          <AskAgent exchanges={questions} onAsk={ask} />
        </section>

        <section>
          <p className="mb-3 text-sm font-semibold text-ink">3. {reviewer ? t('review.changeDecision') : t('review.yourDecision')}</p>
          <DecisionForm number={brief.case.number} choices={brief.choices} agent={brief.agent}
            tones={ui.decisionTones} onDecide={decide} />
        </section>
      </div>
    </Card>
  )
}
