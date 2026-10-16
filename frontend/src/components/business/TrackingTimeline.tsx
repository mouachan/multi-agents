import { MapPin, Truck } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { cn } from '../../lib/cn'
import { formatDateTime } from '../../lib/format'
import type { TrackingEvent } from '../../types/case'
import { Badge } from '../ui/Badge'
import { Card, CardHeader } from '../ui/Card'

export function TrackingTimeline({ events }: { events: TrackingEvent[] }) {
  const { t, locale } = useTranslation()
  if (!events.length) return null
  const sorted = [...events].sort((a, b) => new Date(a.event_date).getTime() - new Date(b.event_date).getTime())
  return (
    <Card>
      <CardHeader icon={<Truck className="h-4 w-4" />} title={t('postal.trackingTimeline')} />
      <ol className="p-5">
        {sorted.map((e, i) => (
          <li key={e.id || i} className="relative flex gap-3 pb-4 last:pb-0">
            {i < sorted.length - 1 && <span className="absolute left-[7px] top-5 h-[calc(100%-0.75rem)] w-px bg-line" />}
            <span className={cn('relative z-10 mt-1 h-3.5 w-3.5 shrink-0 rounded-full border-2', e.is_final ? 'border-teal-500 bg-teal-500' : 'border-teal-500/60 bg-surface')} />
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-baseline justify-between gap-2">
                <p className="text-sm font-medium text-ink">{e.event_type}</p>
                <span className="text-[11px] text-ink-subtle">{formatDateTime(e.event_date, locale)}</span>
              </div>
              {(e.location || e.code_postal) && (
                <p className="mt-0.5 flex items-center gap-1 text-xs text-ink-muted"><MapPin className="h-3 w-3" />{[e.location, e.code_postal].filter(Boolean).join(' · ')}</p>
              )}
              {e.detail && <p className="mt-0.5 text-xs text-ink-subtle">{locale === 'en' && e.metadata?.detail_en ? e.metadata.detail_en : e.detail}</p>}
              {e.is_final && <Badge tone="info" className="mt-1">{t('postal.finalEvent')}</Badge>}
            </div>
          </li>
        ))}
      </ol>
    </Card>
  )
}
