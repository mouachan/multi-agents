import type { ReactNode } from 'react'
import { AlertTriangle, Inbox, Loader2 } from 'lucide-react'
import { cn } from '../../lib/cn'

export function Spinner({ className }: { className?: string }) {
  return <Loader2 className={cn('h-5 w-5 animate-spin text-brand-500', className)} />
}

export function PageLoader() {
  return (
    <div className="flex h-64 items-center justify-center">
      <Spinner className="h-8 w-8" />
    </div>
  )
}

export function EmptyState({ icon, title, description, action, className }: {
  icon?: ReactNode; title: ReactNode; description?: ReactNode; action?: ReactNode; className?: string
}) {
  return (
    <div className={cn('flex flex-col items-center justify-center gap-2 px-6 py-12 text-center', className)}>
      <div className="mb-1 flex h-11 w-11 items-center justify-center rounded-2xl bg-surface-muted text-ink-subtle">
        {icon ?? <Inbox className="h-5 w-5" />}
      </div>
      <p className="text-sm font-semibold text-ink">{title}</p>
      {description && <p className="max-w-sm text-sm text-ink-muted">{description}</p>}
      {action && <div className="mt-2">{action}</div>}
    </div>
  )
}

export function ErrorBanner({ children, onRetry, retryLabel }: { children: ReactNode; onRetry?: () => void; retryLabel?: string }) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/5 px-4 py-3 text-sm text-red-700 dark:text-red-300">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
      <div className="flex-1">{children}</div>
      {onRetry && (
        <button onClick={onRetry} className="text-xs font-semibold underline-offset-2 hover:underline">
          {retryLabel ?? 'Retry'}
        </button>
      )}
    </div>
  )
}

export function ProgressBar({ value, className, tone = 'bg-brand-500' }: { value: number; className?: string; tone?: string }) {
  const pct = Math.max(0, Math.min(100, value))
  return (
    <div className={cn('h-1.5 w-full overflow-hidden rounded-full bg-surface-sunken', className)}>
      <div className={cn('h-full rounded-full transition-all duration-500', tone)} style={{ width: `${pct}%` }} />
    </div>
  )
}
