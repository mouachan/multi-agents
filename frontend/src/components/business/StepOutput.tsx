import { useTranslation } from '../../i18n/LanguageContext'
import type { ProcessingStep } from '../../types/case'
import { SandboxRun } from '../sandbox/SandboxRun'

const OCR_PREVIEW = 600

/** What a processing step returned: the sandbox run of a computation, the start of an OCR text,
 *  otherwise the raw output (the facts that matter are in the evidence card). */
export function StepOutput({ step }: { step: ProcessingStep }) {
  const { t } = useTranslation()
  const output = step.output_data || {}

  if (output.sandbox_run || step.step_name === 'run_python') {
    return <SandboxRun className="mt-2" code={output.code} result={output.sandbox_run ?? output} />
  }
  if (typeof output.raw_text === 'string') {
    return (
      <p className="mt-2 whitespace-pre-wrap rounded-lg bg-surface-muted p-2.5 text-xs text-ink-muted">
        {output.raw_text.slice(0, OCR_PREVIEW)}{output.raw_text.length > OCR_PREVIEW ? '…' : ''}
      </p>
    )
  }
  return (
    <details className="mt-2 rounded-lg border border-line bg-surface-muted p-2.5">
      <summary className="cursor-pointer text-xs font-medium text-ink-muted">{t('case.viewOutput')}</summary>
      <pre className="mt-2 max-h-56 overflow-auto text-[11px] text-ink-muted">{JSON.stringify(output, null, 2)}</pre>
    </details>
  )
}
