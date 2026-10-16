import { useState, type FormEvent } from 'react'
import { Bot, ExternalLink, Send, User } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { formatDateTime } from '../../lib/format'
import type { JournalEntry } from '../../types/review'
import { Button } from '../ui/Button'
import { ErrorBanner } from '../ui/Feedback'
import { Markdown } from '../ui/Markdown'

type Question = Extract<JournalEntry, { type: 'question' }>

/**
 * Questions to the domain's agent about the case. The agent answers with its read-only tools, under
 * the same guardrails as the processing; every exchange is kept in the case journal (and in MLflow).
 */
export function AskAgent({ exchanges, onAsk }: { exchanges: Question[]; onAsk: (question: string) => Promise<void> }) {
  const { t, locale } = useTranslation()
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    if (!question.trim()) return
    setAsking(true)
    setError(null)
    try {
      await onAsk(question.trim())
      setQuestion('')
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message || t('review.askFailed'))
    } finally {
      setAsking(false)
    }
  }

  return (
    <div className="space-y-3">
      {exchanges.map((x, i) => (
        <div key={i} className="space-y-2">
          <div className="flex gap-2 text-sm">
            <User className="mt-0.5 h-4 w-4 shrink-0 text-ink-subtle" />
            <div>
              <p className="text-ink">{x.question}</p>
              <p className="text-[11px] text-ink-subtle">{x.by} · {formatDateTime(x.at, locale)}</p>
            </div>
          </div>
          <div className="ml-6 flex gap-2 rounded-xl bg-violet-500/5 p-3 text-sm ring-1 ring-inset ring-violet-500/15">
            <Bot className="mt-0.5 h-4 w-4 shrink-0 text-violet-500" />
            <div className="min-w-0 flex-1">
              <Markdown>{x.answer}</Markdown>
              {x.trace?.mlflow_url && (
                <a href={x.trace.mlflow_url} target="_blank" rel="noreferrer" className="mt-1 inline-flex items-center gap-1 text-[11px] text-brand-600">
                  MLflow <ExternalLink className="h-3 w-3" />
                </a>
              )}
            </div>
          </div>
        </div>
      ))}
      {error && <ErrorBanner>{error}</ErrorBanner>}
      <form onSubmit={submit} className="flex gap-2">
        <input className="input" value={question} onChange={(e) => setQuestion(e.target.value)} placeholder={t('review.askPlaceholder')} disabled={asking} />
        <Button type="submit" variant="soft" size="md" icon={<Send className="h-4 w-4" />} loading={asking} disabled={!question.trim()}>
          {asking ? t('review.asking') : t('review.ask')}
        </Button>
      </form>
      <p className="text-[11px] text-ink-subtle">{t('review.askHint')}</p>
    </div>
  )
}
