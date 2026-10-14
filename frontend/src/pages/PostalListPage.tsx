import { useNavigate } from 'react-router-dom'
import { AlertOctagon, CheckCircle2, Clock, FileStack, Package } from 'lucide-react'
import { EntityTable, type Column } from '../components/business/EntityTable'
import { Badge } from '../components/ui/Badge'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDate, formatMoney, numericKey } from '../lib/format'
import { postalApi } from '../services/api'
import type { Reclamation } from '../types/reclamation'

const STATUSES = ['pending', 'processing', 'completed', 'manual_review', 'escalated', 'rejected']
const TYPES = ['colis_endommage', 'colis_perdu', 'non_livre', 'mauvaise_adresse', 'vol_point_relais', 'retard_livraison']

export default function PostalListPage() {
  const { t, locale } = useTranslation()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useResource(() => postalApi.list(), [])
  const rows = data ?? []
  const count = (s: string) => rows.filter((r) => r.status === s).length

  const columns: Column<Reclamation>[] = [
    { key: 'number', header: t('postal.reclamationNumber'), sortValue: (r) => numericKey(r.reclamation_number), cell: (r) => <span className="font-mono text-xs font-semibold">{r.reclamation_number}</span> },
    { key: 'client', header: t('postal.clientName'), sortValue: (r) => r.client_nom, cell: (r) => (
      <div className="min-w-0">
        <p className="truncate font-medium">{r.client_nom}</p>
        <p className="max-w-[340px] truncate text-xs text-ink-subtle">{(locale === 'en' && r.metadata?.description_en) || r.description}</p>
      </div>
    ) },
    { key: 'type', header: t('claims.type'), sortValue: (r) => r.reclamation_type, cell: (r) => <Badge tone="orange">{t(`postal.type_${r.reclamation_type}`)}</Badge> },
    { key: 'tracking', header: t('postal.trackingNumber'), sortValue: (r) => r.numero_suivi, cell: (r) => <span className="font-mono text-xs text-ink-muted">{r.numero_suivi}</span> },
    { key: 'value', header: t('postal.declaredValue'), className: 'text-right', sortValue: (r) => r.valeur_declaree ?? -1, cell: (r) => <span className="tabular-nums">{formatMoney(r.valeur_declaree, locale, 2)}</span> },
    { key: 'status', header: t('claims.status'), sortValue: (r) => r.status, cell: (r) => <StatusBadge status={r.status} /> },
    { key: 'submitted', header: t('postal.submitted'), sortValue: (r) => r.submitted_at, cell: (r) => <span className="text-ink-muted">{formatDate(r.submitted_at, locale)}</span> },
  ]

  return (
    <>
      <PageHeader icon={<Package className="h-5 w-5 text-rose-600" />} title={t('postal.title')} subtitle={t('postal.subtitle')} />
      <EntityTable
        rows={rows}
        loading={loading}
        error={error}
        onRetry={reload}
        columns={columns}
        rowKey={(r) => r.id}
        onRowClick={(r) => navigate(`/postal/${r.id}`)}
        statusOf={(r) => r.status}
        statusOptions={STATUSES.map((s) => ({ value: s, label: t(`status.${s}`) }))}
        searchText={(r) => [r.reclamation_number, r.client_nom, r.client_email, r.numero_suivi, r.description].join(' ')}
        searchPlaceholder={t('postal.searchPlaceholder')}
        defaultSort={{ key: 'number', dir: 'desc' }}
        extraFilter={{
          label: t('ui.allTypes'),
          options: TYPES.map((v) => ({ value: v, label: t(`postal.type_${v}`) })),
          apply: (r, v) => r.reclamation_type === v,
        }}
        kpis={[
          { key: 'total', label: t('ui.total'), value: rows.length, icon: <FileStack className="h-5 w-5" />, accent: 'bg-brand-500/10 text-brand-600 dark:text-brand-300', status: '' },
          { key: 'pending', label: t('status.pending'), value: count('pending'), icon: <Clock className="h-5 w-5" />, accent: 'bg-amber-500/10 text-amber-600', status: 'pending' },
          { key: 'escalated', label: t('status.escalated'), value: count('escalated') + count('manual_review'), icon: <AlertOctagon className="h-5 w-5" />, accent: 'bg-orange-500/10 text-orange-600', status: 'escalated' },
          { key: 'done', label: t('status.completed'), value: count('completed'), icon: <CheckCircle2 className="h-5 w-5" />, accent: 'bg-emerald-500/10 text-emerald-600', status: 'completed' },
        ]}
      />
    </>
  )
}
