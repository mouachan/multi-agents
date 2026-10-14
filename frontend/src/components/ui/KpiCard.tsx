import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

interface KpiCardProps {
  label: ReactNode
  value: ReactNode
  hint?: ReactNode
  icon?: ReactNode
  accent?: string // tailwind classes for the icon tile
  active?: boolean
  onClick?: () => void
}

export function KpiCard({ label, value, hint, icon, accent = 'bg-brand-500/10 text-brand-600', active, onClick }: KpiCardProps) {
  const Comp = onClick ? 'button' : 'div'
  return (
    <Comp
      onClick={onClick}
      className={cn(
        'card flex items-center gap-3.5 p-4 text-left transition-all',
        onClick && 'hover:-translate-y-0.5 hover:shadow-elevated',
        active && 'ring-2 ring-brand-500/50',
      )}
    >
      {icon && <div className={cn('flex h-10 w-10 shrink-0 items-center justify-center rounded-xl', accent)}>{icon}</div>}
      <div className="min-w-0">
        <p className="truncate text-xs font-medium text-ink-muted">{label}</p>
        <p className="text-xl font-semibold tabular-nums tracking-tight text-ink">{value}</p>
        {hint && <p className="truncate text-[11px] text-ink-subtle">{hint}</p>}
      </div>
    </Comp>
  )
}
