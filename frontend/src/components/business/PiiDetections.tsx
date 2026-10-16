import { Lock, ShieldCheck } from 'lucide-react'
import { useTranslation } from '../../i18n/LanguageContext'
import { formatDateTime } from '../../lib/format'
import type { PersonalDataFinding } from '../../types/case'
import { Badge } from '../ui/Badge'
import { Card, CardHeader } from '../ui/Card'

/** Types of personal data NeMo Guardrails (Presidio) found in a claim — never the values (backend/app/services/pii_report.py). */
export function PiiDetections({ detections }: { detections: PersonalDataFinding[] }) {
  const { t, locale } = useTranslation()
  return (
    <Card>
      <CardHeader
        icon={<ShieldCheck className="h-4 w-4" />}
        title={t('pii.title')}
        subtitle={t('pii.subtitle')}
        actions={<Badge tone={detections.length ? 'violet' : 'success'}>{detections.length}</Badge>}
      />
      <div className="p-4">
        {detections.length === 0 ? (
          <p className="text-sm text-ink-muted">{t('pii.none')}</p>
        ) : (
          <ul className="space-y-2">
            {detections.map((d) => (
              <li key={d.id} className="flex items-center justify-between gap-3 rounded-xl bg-surface-muted px-3 py-2">
                <div className="flex min-w-0 items-center gap-2">
                  <Lock className="h-3.5 w-3.5 shrink-0 text-violet-500" />
                  <span className="truncate text-sm font-medium text-ink">{d.detection_type}{d.count && d.count > 1 ? ` ×${d.count}` : ''}</span>
                  {d.source_step && <span className="truncate text-[11px] text-ink-subtle">· {d.source_step}</span>}
                </div>
                <span className="shrink-0 text-[11px] text-ink-subtle">{formatDateTime(d.detected_at, locale)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </Card>
  )
}
