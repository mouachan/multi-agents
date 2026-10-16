import { ShieldCheck } from 'lucide-react'
import { PiiDetections } from '../components/business/PiiDetections'
import { Badge, type Tone } from '../components/ui/Badge'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { formatDate, formatDateTime, formatDuration, numericKey } from '../lib/format'
import { casesApi } from '../services/api'
import type { Locale } from '../i18n/translations'
import type { Case } from '../types/case'
import type { DomainUI } from './types'

const TYPE_TONES: Record<string, Tone> = { auto: 'info', home: 'orange', medical: 'success', life: 'violet' }
const description = (c: Case, locale: Locale) => (locale === 'en' && c.metadata?.description_en) || c.metadata?.description || ''

/** Personal data found in the claim's documents (types only, never the values) */
function PersonalData({ case: c }: { case: Case }) {
  const { data } = useResource(() => casesApi('claims').personalData(c.id), [c.id, c.status])
  return <PiiDetections detections={data ?? []} />
}

export const claims: DomainUI = {
  name: 'claims',
  path: '/claims',
  i18n: 'claims',
  icon: ShieldCheck,
  iconClass: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400',
  agentId: 'claims',
  statuses: ['pending', 'processing', 'completed', 'manual_review', 'denied', 'failed'],
  reviewStatus: 'manual_review',
  decisionTones: { approve: 'success', deny: 'danger', manual_review: 'violet' },

  columns: (t, locale) => [
    { key: 'number', header: t('claims.claimNumber'), sortValue: (c) => numericKey(c.number), cell: (c) => <span className="font-mono text-xs font-semibold">{c.number}</span> },
    { key: 'claimant', header: t('claims.claimant'), sortValue: (c) => c.user_name || c.user_id, cell: (c) => (
      <div className="min-w-0">
        <p className="truncate font-medium">{c.user_name || c.user_id}</p>
        <p className="max-w-[360px] truncate text-xs text-ink-subtle">{description(c, locale)}</p>
      </div>
    ) },
    { key: 'type', header: t('claims.type'), sortValue: (c) => c.claim_type || '', cell: (c) => (
      <Badge tone={TYPE_TONES[(c.claim_type || '').toLowerCase()] ?? 'neutral'}>{c.claim_type || '—'}</Badge>
    ) },
    { key: 'status', header: t('case.status'), sortValue: (c) => c.status, cell: (c) => <StatusBadge status={c.status} /> },
    { key: 'submitted', header: t('case.submitted'), sortValue: (c) => c.submitted_at || '', cell: (c) => <span className="text-ink-muted">{formatDate(c.submitted_at, locale)}</span> },
    { key: 'duration', header: t('case.duration'), className: 'text-right', sortValue: (c) => c.total_processing_time_ms ?? -1, cell: (c) => (
      <span className="font-mono text-xs text-ink-muted">{c.total_processing_time_ms ? formatDuration(c.total_processing_time_ms) : '—'}</span>
    ) },
  ],
  searchText: (c) => [c.number, c.user_name, c.user_id, c.claim_type, c.metadata?.description, c.metadata?.description_en].join(' '),
  extraFilter: (_cases, t) => ({
    label: t('ui.allTypes'),
    options: ['Auto', 'Home', 'Medical', 'Life'].map((v) => ({ value: v, label: v })),
    apply: (c, v) => (c.claim_type || '').toLowerCase() === v.toLowerCase(),
  }),

  hero: (c, t, locale) => {
    const ocr = c.processing_steps.find((s) => s.step_name === 'ocr_document')?.output_data?.structured_data?.fields
    return {
      kind: c.claim_type && <Badge tone="info">{c.claim_type}</Badge>,
      title: ocr?.diagnosis?.value || ocr?.service?.value,
      description: description(c, locale),
      fields: [
        { label: t('claims.claimant'), value: c.user_name || c.user_id },
        { label: t('case.submittedAt'), value: formatDateTime(c.submitted_at, locale) },
        { label: t('case.processedAt'), value: formatDateTime(c.processed_at, locale) },
        { label: t('case.duration'), value: formatDuration(c.total_processing_time_ms) },
      ],
    }
  },
  Extras: PersonalData,
}
