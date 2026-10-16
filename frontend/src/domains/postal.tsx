import { Package } from 'lucide-react'
import { TrackingTimeline } from '../components/business/TrackingTimeline'
import { Badge } from '../components/ui/Badge'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { formatDate, formatDateTime, formatDuration, formatMoney, numericKey } from '../lib/format'
import { casesApi } from '../services/api'
import type { Locale } from '../i18n/translations'
import type { Case } from '../types/case'
import type { DomainUI } from './types'

const TYPES = ['colis_endommage', 'colis_perdu', 'non_livre', 'mauvaise_adresse', 'vol_point_relais', 'retard_livraison']
const description = (c: Case, locale: Locale) => (locale === 'en' && c.metadata?.description_en) || c.description

/** Tracking timeline of the complaint's parcel */
function Tracking({ case: c }: { case: Case }) {
  const { data } = useResource(() => casesApi('postal').tracking(c.id), [c.id])
  return <TrackingTimeline events={data ?? []} />
}

export const postal: DomainUI = {
  name: 'postal',
  path: '/postal',
  i18n: 'postal',
  icon: Package,
  iconClass: 'bg-rose-500/10 text-rose-600 dark:text-rose-400',
  agentId: 'courrier_reclamation',
  statuses: ['pending', 'processing', 'completed', 'escalated', 'rejected', 'failed'],
  reviewStatus: 'escalated',
  decisionTones: { rembourser: 'success', reexpedier: 'info', rejeter: 'danger', escalader: 'orange' },

  columns: (t, locale) => [
    { key: 'number', header: t('postal.reclamationNumber'), sortValue: (c) => numericKey(c.number), cell: (c) => <span className="font-mono text-xs font-semibold">{c.number}</span> },
    { key: 'client', header: t('postal.clientName'), sortValue: (c) => c.client_nom, cell: (c) => (
      <div className="min-w-0">
        <p className="truncate font-medium">{c.client_nom}</p>
        <p className="max-w-[340px] truncate text-xs text-ink-subtle">{description(c, locale)}</p>
      </div>
    ) },
    { key: 'type', header: t('postal.reclamationType'), sortValue: (c) => c.reclamation_type, cell: (c) => <Badge tone="orange">{t(`postal.type_${c.reclamation_type}`)}</Badge> },
    { key: 'tracking', header: t('postal.trackingNumber'), sortValue: (c) => c.numero_suivi, cell: (c) => <span className="font-mono text-xs text-ink-muted">{c.numero_suivi}</span> },
    { key: 'value', header: t('postal.declaredValue'), className: 'text-right', sortValue: (c) => Number(c.valeur_declaree ?? -1), cell: (c) => <span className="tabular-nums">{formatMoney(c.valeur_declaree, locale, 2)}</span> },
    { key: 'status', header: t('case.status'), sortValue: (c) => c.status, cell: (c) => <StatusBadge status={c.status} /> },
    { key: 'submitted', header: t('case.submitted'), sortValue: (c) => c.submitted_at || '', cell: (c) => <span className="text-ink-muted">{formatDate(c.submitted_at, locale)}</span> },
  ],
  searchText: (c) => [c.number, c.client_nom, c.client_email, c.numero_suivi, c.description].join(' '),
  extraFilter: (_cases, t) => ({
    label: t('ui.allTypes'),
    options: TYPES.map((v) => ({ value: v, label: t(`postal.type_${v}`) })),
    apply: (c, v) => c.reclamation_type === v,
  }),

  hero: (c, t, locale) => ({
    kind: <Badge tone="orange">{t(`postal.type_${c.reclamation_type}`)}</Badge>,
    description: description(c, locale),
    fields: [
      { label: t('postal.clientName'), value: c.client_nom },
      { label: t('postal.clientEmail'), value: c.client_email },
      { label: t('postal.trackingNumber'), value: <span className="font-mono">{c.numero_suivi}</span> },
      { label: t('postal.declaredValue'), value: formatMoney(c.valeur_declaree, locale, 2) },
      { label: t('postal.clientPhone'), value: c.client_telephone || '—' },
      { label: t('case.submittedAt'), value: formatDateTime(c.submitted_at, locale) },
      { label: t('case.duration'), value: formatDuration(c.total_processing_time_ms) },
    ],
  }),
  Extras: Tracking,
}
