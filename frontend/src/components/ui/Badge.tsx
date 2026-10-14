import type { ReactNode } from 'react'
import { cn } from '../../lib/cn'

export type Tone = 'neutral' | 'brand' | 'success' | 'warning' | 'danger' | 'info' | 'violet' | 'orange'

const TONES: Record<Tone, { badge: string; dot: string }> = {
  neutral: { badge: 'bg-slate-500/10 text-slate-700 ring-slate-500/20 dark:text-slate-300', dot: 'bg-slate-400' },
  brand: { badge: 'bg-brand-500/10 text-brand-700 ring-brand-500/20 dark:text-brand-300', dot: 'bg-brand-500' },
  success: { badge: 'bg-emerald-500/10 text-emerald-700 ring-emerald-500/20 dark:text-emerald-300', dot: 'bg-emerald-500' },
  warning: { badge: 'bg-amber-500/10 text-amber-700 ring-amber-500/25 dark:text-amber-300', dot: 'bg-amber-500' },
  danger: { badge: 'bg-red-500/10 text-red-700 ring-red-500/20 dark:text-red-300', dot: 'bg-red-500' },
  info: { badge: 'bg-sky-500/10 text-sky-700 ring-sky-500/20 dark:text-sky-300', dot: 'bg-sky-500' },
  violet: { badge: 'bg-violet-500/10 text-violet-700 ring-violet-500/20 dark:text-violet-300', dot: 'bg-violet-500' },
  orange: { badge: 'bg-orange-500/10 text-orange-700 ring-orange-500/20 dark:text-orange-300', dot: 'bg-orange-500' },
}

interface BadgeProps {
  tone?: Tone
  dot?: boolean
  pulse?: boolean
  icon?: ReactNode
  className?: string
  title?: string
  children: ReactNode
}

export function Badge({ tone = 'neutral', dot, pulse, icon, className, title, children }: BadgeProps) {
  const t = TONES[tone]
  return (
    <span
      title={title}
      className={cn(
        'inline-flex items-center gap-1.5 whitespace-nowrap rounded-full px-2 py-0.5 text-[11px] font-semibold ring-1 ring-inset',
        t.badge, className,
      )}
    >
      {dot && (
        <span className="relative flex h-1.5 w-1.5">
          {pulse && <span className={cn('absolute inline-flex h-full w-full animate-ping rounded-full opacity-60', t.dot)} />}
          <span className={cn('relative inline-flex h-1.5 w-1.5 rounded-full', t.dot)} />
        </span>
      )}
      {icon}
      {children}
    </span>
  )
}
