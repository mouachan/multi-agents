import type { ReactNode } from 'react'
import { Card } from '../ui/Card'
import { StatusBadge } from '../ui/StatusBadge'

interface EntityHeroProps {
  number: string
  status: string
  icon: ReactNode
  iconClass: string
  kind?: ReactNode
  title?: ReactNode
  description?: ReactNode
  fields: { label: ReactNode; value: ReactNode }[]
  actions?: ReactNode
  children?: ReactNode
}

/** Header card of a claim / tender / complaint detail page. */
export function EntityHero({ number, status, icon, iconClass, kind, title, description, fields, actions, children }: EntityHeroProps) {
  return (
    <Card className="overflow-hidden">
      <div className="flex flex-wrap items-start justify-between gap-4 p-5">
        <div className="flex min-w-0 items-start gap-3.5">
          <div className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl ${iconClass}`}>{icon}</div>
          <div className="min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h1 className="font-mono text-xl font-semibold tracking-tight text-ink">{number}</h1>
              <StatusBadge status={status} />
              {kind}
            </div>
            {title && <p className="mt-1 text-base font-medium text-ink">{title}</p>}
            {description && <p className="mt-1 max-w-3xl text-sm leading-relaxed text-ink-muted">{description}</p>}
          </div>
        </div>
        {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
      </div>
      {fields.length > 0 && (
        <dl className="grid grid-cols-2 gap-x-6 gap-y-4 border-t border-line bg-surface-muted/40 px-5 py-4 md:grid-cols-4">
          {fields.map((f, i) => (
            <div key={i} className="min-w-0">
              <dt className="label">{f.label}</dt>
              <dd className="mt-1 truncate text-sm font-medium text-ink">{f.value}</dd>
            </div>
          ))}
        </dl>
      )}
      {children}
    </Card>
  )
}
