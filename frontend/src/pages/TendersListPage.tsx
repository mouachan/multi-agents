import { useNavigate } from 'react-router-dom'
import { Building2, CheckCircle2, Clock, FileStack, UserCheck } from 'lucide-react'
import { EntityTable, type Column } from '../components/business/EntityTable'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDuration, formatMoney, numericKey } from '../lib/format'
import { tendersApi } from '../services/api'
import type { Tender } from '../types/tender'

const STATUSES = ['pending', 'processing', 'completed', 'manual_review', 'failed']
const meta = (r: Tender) => (r.metadata || {}) as Record<string, any>
const amount = (r: Tender): number | undefined => meta(r).montant_estime ?? r.montant_estime

export default function TendersListPage() {
  const { t, locale } = useTranslation()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useResource(() => tendersApi.list(), [])
  const rows = data ?? []
  const count = (s: string) => rows.filter((r) => r.status === s).length
  const timed = rows.filter((r) => r.total_processing_time_ms)
  const avg = timed.length ? timed.reduce((a, r) => a + (r.total_processing_time_ms ?? 0), 0) / timed.length : null
  const regions = Array.from(new Set(rows.map((r) => meta(r).region).filter(Boolean))).sort() as string[]

  const columns: Column<Tender>[] = [
    { key: 'number', header: t('tenders.tenderNumber'), sortValue: (r) => numericKey(r.tender_number), cell: (r) => <span className="font-mono text-xs font-semibold">{r.tender_number}</span> },
    { key: 'title', header: t('tenders.objectMarche'), sortValue: (r) => meta(r).titre || r.objet_marche || '', cell: (r) => (
      <div className="min-w-0">
        <p className="max-w-[420px] truncate font-medium">{meta(r).titre || r.objet_marche || '—'}</p>
        <p className="max-w-[420px] truncate text-xs text-ink-subtle">{meta(r).maitre_ouvrage || r.maitre_ouvrage || r.entity_id}</p>
      </div>
    ) },
    { key: 'region', header: t('tenders.region'), sortValue: (r) => meta(r).region || '', cell: (r) => (
      <span className="text-ink-muted">{meta(r).region || '—'}{meta(r).commune ? ` · ${meta(r).commune}` : ''}</span>
    ) },
    { key: 'amount', header: t('tenders.estimatedAmount'), className: 'text-right', sortValue: (r) => amount(r) ?? -1, cell: (r) => (
      <span className="font-medium tabular-nums">{formatMoney(amount(r), locale)}</span>
    ) },
    { key: 'status', header: t('claims.status'), sortValue: (r) => r.status, cell: (r) => <StatusBadge status={r.status} /> },
    { key: 'deadline', header: t('tenders.submissionDeadline'), sortValue: (r) => meta(r).date_limite_remise || r.date_limite_reponse || '', cell: (r) => (
      <span className="text-ink-muted">{meta(r).date_limite_remise || r.date_limite_reponse || '—'}</span>
    ) },
  ]

  return (
    <>
      <PageHeader icon={<Building2 className="h-5 w-5 text-amber-600" />} title={t('tenders.title')} subtitle={t('tenders.subtitle')} />
      <EntityTable
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        columns={columns}
        rowKey={(r) => r.id}
        onRowClick={(r) => navigate(`/tenders/${r.id}`)}
        statusOf={(r) => r.status}
        statusOptions={STATUSES.map((s) => ({ value: s, label: t(`status.${s}`) }))}
        searchText={(r) => [r.tender_number, r.entity_id, meta(r).titre, meta(r).maitre_ouvrage, meta(r).region, meta(r).commune, r.objet_marche].join(' ')}
        searchPlaceholder={t('tenders.searchPlaceholder')}
        defaultSort={{ key: 'number', dir: 'desc' }}
        extraFilter={regions.length ? {
          label: t('ui.allRegions'),
          options: regions.map((v) => ({ value: v, label: v })),
          apply: (r, v) => meta(r).region === v,
        } : undefined}
        kpis={[
          { key: 'total', label: t('ui.total'), value: rows.length, icon: <FileStack className="h-5 w-5" />, accent: 'bg-brand-500/10 text-brand-600 dark:text-brand-300', status: '' },
          { key: 'pending', label: t('status.pending'), value: count('pending'), icon: <Clock className="h-5 w-5" />, accent: 'bg-amber-500/10 text-amber-600', status: 'pending' },
          { key: 'review', label: t('status.manual_review'), value: count('manual_review'), icon: <UserCheck className="h-5 w-5" />, accent: 'bg-violet-500/10 text-violet-600', status: 'manual_review' },
          { key: 'done', label: t('status.completed'), value: count('completed'), hint: avg ? `${t('ui.avgTime')} ${formatDuration(avg)}` : undefined, icon: <CheckCircle2 className="h-5 w-5" />, accent: 'bg-emerald-500/10 text-emerald-600', status: 'completed' },
        ]}
      />
    </>
  )
}
