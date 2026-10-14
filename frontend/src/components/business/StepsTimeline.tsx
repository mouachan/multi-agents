import type { ReactNode } from 'react'
import { CheckCircle2, Loader2, ListChecks, XCircle } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { formatDuration } from '../../lib/format'
import type { ProcessingStepLog } from '../../types'
import { Card, CardHeader } from '../ui/Card'
import { EmptyState, ProgressBar } from '../ui/Feedback'

const label = (name: string) => name.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())

/** Processing steps of an agent run, with live progress while it runs. */
export function StepsTimeline({ steps, processing, progress, renderOutput, title }: {
  steps: ProcessingStepLog[]
  processing: boolean
  progress?: number
  renderOutput?: (step: ProcessingStepLog) => ReactNode
  title?: ReactNode
}) {
  const { t } = useTranslation()
  if (!steps.length && !processing) return null
  return (
    <Card>
      <CardHeader
        icon={<ListChecks className="h-4 w-4" />}
        title={title ?? t('processingSteps.title')}
        actions={processing && progress != null ? <span className="font-mono text-xs text-sky-600">{Math.round(progress)}%</span> : undefined}
      />
      {processing && progress != null && <ProgressBar value={progress} className="rounded-none" tone="bg-sky-500" />}
      <div className="p-5">
        {steps.length === 0 ? (
          <EmptyState icon={<Loader2 className="h-5 w-5 animate-spin" />} title={t('ui.processingRunning')} className="py-6" />
        ) : (
          <ol>
            {steps.map((step, i) => {
              const done = step.status === 'completed'
              const failed = step.status === 'failed'
              const last = i === steps.length - 1
              return (
                <li key={i} className="relative flex gap-3.5 pb-5 last:pb-0">
                  {!last && <span className="absolute left-[15px] top-9 h-[calc(100%-2rem)] w-px bg-line" />}
                  <span className={cn(
                    'relative z-10 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl ring-1 ring-inset',
                    done ? 'bg-emerald-500/10 text-emerald-600 ring-emerald-500/25 dark:text-emerald-400'
                      : failed ? 'bg-red-500/10 text-red-600 ring-red-500/25'
                        : 'bg-sky-500/10 text-sky-600 ring-sky-500/25',
                  )}>
                    {done ? <CheckCircle2 className="h-4 w-4" /> : failed ? <XCircle className="h-4 w-4" /> : <Loader2 className="h-4 w-4 animate-spin" />}
                  </span>
                  <div className="min-w-0 flex-1 pt-1">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="text-sm font-semibold text-ink">{label(step.step_name)}</p>
                      <span className="text-[11px] text-ink-subtle">
                        {step.agent_name}{step.duration_ms != null && ` · ${formatDuration(step.duration_ms)}`}
                      </span>
                    </div>
                    {step.error_message && <p className="mt-1 text-xs text-red-600">{step.error_message}</p>}
                    {step.output_data && renderOutput && <div className="legacy">{renderOutput(step)}</div>}
                  </div>
                </li>
              )
            })}
          </ol>
        )}
      </div>
    </Card>
  )
}
