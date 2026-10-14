import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Clock, FileStack, ShieldCheck, UserCheck } from 'lucide-react'
import { EntityTable, type Column } from '../components/business/EntityTable'
import { Badge, type Tone } from '../components/ui/Badge'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDate, formatDuration, numericKey } from '../lib/format'
import { claimsApi } from '../services/api'
import type { Claim } from '../types'

const TYPE_TONES: Record<string, Tone> = { auto: 'info', home: 'orange', medical: 'success', life: 'violet' }
const STATUSES = ['pending', 'processing', 'completed', 'manual_review', 'denied', 'failed']

export default function ClaimsListPage() {
  const { t, locale } = useTranslation()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useResource(() => claimsApi.list(), [])
  const rows = data ?? []
  const count = (s: string) => rows.filter((r) => r.status === s).length
  const timed = rows.filter((r) => r.total_processing_time_ms)
  const avg = timed.length ? timed.reduce((a, r) => a + (r.total_processing_time_ms ?? 0), 0) / timed.length : null

  const columns: Column<Claim>[] = [
    { key: 'number', header: t('claims.claimNumber'), sortValue: (r) => numericKey(r.claim_number), cell: (r) => <span className="font-mono text-xs font-semibold">{r.claim_number}</span> },
    { key: 'claimant', header: t('claims.claimant'), sortValue: (r) => r.user_name || r.user_id, cell: (r) => (
      <div className="min-w-0">
        <p className="truncate font-medium">{r.user_name || r.user_id}</p>
        <p className="max-w-[360px] truncate text-xs text-ink-subtle">{(locale === 'en' && r.metadata?.description_en) || r.metadata?.description || ''}</p>
      </div>
    ) },
    { key: 'type', header: t('claims.type'), sortValue: (r) => r.claim_type || '', cell: (r) => (
      <Badge tone={TYPE_TONES[(r.claim_type || '').toLowerCase()] ?? 'neutral'}>{r.claim_type || '—'}</Badge>
    ) },
    { key: 'status', header: t('claims.status'), sortValue: (r) => r.status, cell: (r) => <StatusBadge status={r.status} /> },
    { key: 'submitted', header: t('claims.submitted'), sortValue: (r) => r.submitted_at, cell: (r) => <span className="text-ink-muted">{formatDate(r.submitted_at, locale)}</span> },
    { key: 'duration', header: t('claims.duration'), className: 'text-right', sortValue: (r) => r.total_processing_time_ms ?? -1, cell: (r) => (
      <span className="font-mono text-xs text-ink-muted">{r.total_processing_time_ms ? formatDuration(r.total_processing_time_ms) : '—'}</span>
    ) },
  ]

  return (
    <>
      <PageHeader
        icon={<ShieldCheck className="h-5 w-5 text-emerald-600" />}
        title={t('claims.title')}
        subtitle={t('claims.subtitle')}
      />
      <EntityTable
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        columns={columns}
        rowKey={(r) => r.id}
        onRowClick={(r) => navigate(`/claims/${r.id}`)}
        statusOf={(r) => r.status}
        statusOptions={STATUSES.map((s) => ({ value: s, label: t(`status.${s}`) }))}
        searchText={(r) => [r.claim_number, r.user_name, r.user_id, r.claim_type, r.metadata?.description, r.metadata?.description_en].join(' ')}
        searchPlaceholder={t('claims.searchPlaceholder')}
        defaultSort={{ key: 'number', dir: 'desc' }}
        extraFilter={{
          label: t('claims.allTypes'),
          options: ['Auto', 'Home', 'Medical', 'Life'].map((v) => ({ value: v, label: v })),
          apply: (r, v) => (r.claim_type || '').toLowerCase() === v.toLowerCase(),
        }}
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
