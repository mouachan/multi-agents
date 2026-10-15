import { Box, CheckCircle2, ShieldX, XCircle } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { formatDuration } from '../../lib/format'
import type { SandboxExecution } from '../../types/sandbox'
import { Badge } from '../ui/Badge'

function Block({ label, text, tone }: { label: string; text: string; tone?: 'error' }) {
  return (
    <div>
      <p className="mb-1 text-[10px] font-semibold uppercase tracking-wide text-ink-subtle">{label}</p>
      <pre
        className={cn(
          'max-h-48 overflow-auto whitespace-pre-wrap break-words rounded-lg border border-line bg-surface-sunken p-2 font-mono text-[11px] leading-relaxed',
          tone === 'error' ? 'text-red-700 dark:text-red-300' : 'text-ink',
        )}
      >
        {text}
      </pre>
    </div>
  )
}

/** One run_python execution in an OpenShell sandbox: code, output, policy denials, timings. */
export function SandboxRun({ code, result, className }: { code?: string; result: SandboxExecution; className?: string }) {
  const { t } = useTranslation()
  const sb = result.sandbox ?? {}
  const denials = result.denials ?? []
  const ok = result.exit_code === 0 && !result.error

  return (
    <div className={cn('space-y-2', className)}>
      <div className="flex flex-wrap items-center gap-1.5">
        <Badge tone={ok ? 'success' : 'danger'} icon={ok ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}>
          {result.error ? t('sandbox.failed') : `exit ${result.exit_code ?? '?'}`}
        </Badge>
        {denials.map((d, i) => (
          <Badge key={i} tone="warning" icon={<ShieldX className="h-3 w-3" />}>
            {t(`sandbox.denied_${d.type}`)}
          </Badge>
        ))}
        {sb.name && (
          <span className="inline-flex items-center gap-1 font-mono text-[10px] text-ink-subtle">
            <Box className="h-3 w-3" />{sb.name}
          </span>
        )}
      </div>

      {(sb.duration_ms != null || sb.policy) && (
        <p className="text-[11px] text-ink-subtle">
          {sb.duration_ms != null && <>{formatDuration(sb.duration_ms)}</>}
          {sb.reused != null && <> · {sb.reused ? t('sandbox.reused') : `${t('sandbox.created')} (${formatDuration(sb.ready_ms ?? 0)})`}</>}
          {sb.policy && <> · {sb.policy}</>}
        </p>
      )}

      {code && <Block label={t('sandbox.code')} text={code} />}
      {result.stdout?.trim() && <Block label={t('sandbox.stdout')} text={result.stdout.trim()} />}
      {result.stderr?.trim() && <Block label={t('sandbox.stderr')} text={result.stderr.trim()} tone="error" />}
      {result.error && <Block label={t('sandbox.error')} text={result.error} tone="error" />}
    </div>
  )
}
