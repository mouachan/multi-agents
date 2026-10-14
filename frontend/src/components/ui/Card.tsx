import type { HTMLAttributes, ReactNode } from 'react'
import { cn } from '../../lib/cn'

export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('card', className)} {...props} />
}

interface CardHeaderProps {
  title: ReactNode
  subtitle?: ReactNode
  icon?: ReactNode
  actions?: ReactNode
  className?: string
}

export function CardHeader({ title, subtitle, icon, actions, className }: CardHeaderProps) {
  return (
    <div className={cn('card-header', className)}>
      <div className="flex min-w-0 items-center gap-2.5">
        {icon && <span className="text-ink-subtle">{icon}</span>}
        <div className="min-w-0">
          <h3 className="card-title truncate">{title}</h3>
          {subtitle && <p className="truncate text-xs text-ink-subtle">{subtitle}</p>}
        </div>
      </div>
      {actions && <div className="flex shrink-0 items-center gap-1.5">{actions}</div>}
    </div>
  )
}

export function CardBody({ className, ...props }: HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('p-5', className)} {...props} />
}

/** Label / value pair used in detail headers */
export function Field({ label, children, className }: { label: ReactNode; children: ReactNode; className?: string }) {
  return (
    <div className={cn('min-w-0', className)}>
      <dt className="label">{label}</dt>
      <dd className="mt-1 truncate text-sm font-medium text-ink">{children}</dd>
    </div>
  )
}
