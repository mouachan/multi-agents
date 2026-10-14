import type { ReactNode } from 'react'
import { AlertTriangle, Cpu, Gavel } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { Card, CardHeader } from '../ui/Card'
import { MaskedText } from '../ui/Markdown'
import type { Tone } from '../ui/Badge'

const TONE_STYLES: Record<Tone, string> = {
  success: 'from-emerald-500/15 text-emerald-700 dark:text-emerald-300 ring-emerald-500/25',
  danger: 'from-red-500/15 text-red-700 dark:text-red-300 ring-red-500/25',
  warning: 'from-amber-500/15 text-amber-700 dark:text-amber-300 ring-amber-500/25',
  info: 'from-sky-500/15 text-sky-700 dark:text-sky-300 ring-sky-500/25',
  violet: 'from-violet-500/15 text-violet-700 dark:text-violet-300 ring-violet-500/25',
  orange: 'from-orange-500/15 text-orange-700 dark:text-orange-300 ring-orange-500/25',
  brand: 'from-brand-500/15 text-brand-700 dark:text-brand-300 ring-brand-500/25',
  neutral: 'from-slate-500/10 text-ink ring-line',
}

/** Agent decision: verdict, confidence, reasoning (PII placeholders rendered as badges). */
export function DecisionCard({ label, tone, confidence, reasoning, manualReview, model, extra }: {
  label: ReactNode
  tone: Tone
  confidence?: number | null
  reasoning?: string | null
  manualReview?: boolean
  model?: string | null
  extra?: ReactNode
}) {
  const { t } = useTranslation()
  const pct = confidence == null ? null : Math.round((confidence <= 1 ? confidence * 100 : confidence))
  return (
    <Card>
      <CardHeader icon={<Gavel className="h-4 w-4" />} title={t('ui.decision')} actions={model ? <span className="inline-flex items-center gap-1 text-[11px] text-ink-subtle"><Cpu className="h-3 w-3" />{model}</span> : undefined} />
      <div className="space-y-4 p-5">
        <div className={cn('rounded-2xl bg-gradient-to-br to-transparent p-4 ring-1 ring-inset', TONE_STYLES[tone])}>
          <p className="label !text-current opacity-70">{t('ui.agentRecommendation')}</p>
          <p className="mt-1 text-2xl font-semibold tracking-tight">{label}</p>
          {pct != null && (
            <div className="mt-3">
              <div className="mb-1 flex justify-between text-xs">
                <span className="opacity-80">{t('ui.confidence')}</span>
                <span className="font-semibold tabular-nums">{pct}%</span>
              </div>
              <div className="h-1.5 overflow-hidden rounded-full bg-black/10 dark:bg-white/10">
                <div className="h-full rounded-full bg-current opacity-70" style={{ width: `${pct}%` }} />
              </div>
            </div>
          )}
        </div>
        {manualReview && (
          <div className="flex items-center gap-2 rounded-xl bg-violet-500/10 px-3 py-2 text-xs font-medium text-violet-700 dark:text-violet-300">
            <AlertTriangle className="h-3.5 w-3.5" /> {t('ui.requiresManualReview')}
          </div>
        )}
        {reasoning && (
          <div>
            <p className="label mb-1.5">{t('ui.reasoning')}</p>
            <p className="whitespace-pre-wrap text-sm leading-relaxed text-ink-muted"><MaskedText text={reasoning} /></p>
          </div>
        )}
        {extra}
      </div>
    </Card>
  )
}
