import { useTranslation } from '../../i18n/LanguageContext'
import { Badge, type Tone } from './Badge'

const STATUS_TONES: Record<string, Tone> = {
  pending: 'warning',
  pending_info: 'neutral',
  processing: 'info',
  completed: 'success',
  denied: 'danger',
  failed: 'danger',
  rejected: 'danger',
  manual_review: 'violet',
  escalated: 'orange',
}

/** Status pill shared by claims, tenders and postal complaints. */
export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const { t } = useTranslation()
  const label = t(`status.${status}`)
  return (
    <Badge tone={STATUS_TONES[status] || 'neutral'} dot pulse={status === 'processing'} className={className}>
      {label === `status.${status}` ? status : label}
    </Badge>
  )
}

export function statusTone(status: string): Tone {
  return STATUS_TONES[status] || 'neutral'
}
