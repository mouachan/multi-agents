import { useNavigate } from 'react-router-dom'
import { CheckCircle2, Clock, FileStack, UserCheck } from 'lucide-react'
import { EntityTable } from '../components/business/EntityTable'
import { PageHeader } from '../components/ui/PageHeader'
import { domainUI } from '../domains'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { formatDuration } from '../lib/format'
import { casesApi } from '../services/api'
import type { Domain } from '../types/case'

/** The cases of a domain: search, filters, key figures (columns and filters: src/domains/<domain>.tsx). */
export default function CaseListPage({ domain }: { domain: Domain }) {
  const ui = domainUI(domain)
  const { t, locale } = useTranslation()
  const navigate = useNavigate()
  const { data, loading, error, reload } = useResource(() => casesApi(domain).list(), [domain])
  const cases = data ?? []
  const count = (status: string) => cases.filter((c) => c.status === status).length
  const timed = cases.filter((c) => c.total_processing_time_ms)
  const average = timed.length ? timed.reduce((sum, c) => sum + (c.total_processing_time_ms ?? 0), 0) / timed.length : null
  const Icon = ui.icon

  return (
    <>
      <PageHeader icon={<Icon className="h-5 w-5" />} title={t(`${ui.i18n}.title`)} subtitle={t(`${ui.i18n}.subtitle`)} />
      <EntityTable
        rows={cases}
        loading={loading}
        error={error}
        onRetry={reload}
        columns={ui.columns(t, locale)}
        rowKey={(c) => c.id}
        onRowClick={(c) => navigate(`${ui.path}/${c.id}`)}
        statusOf={(c) => c.status}
        statusOptions={ui.statuses.map((s) => ({ value: s, label: t(`status.${s}`) }))}
        searchText={ui.searchText}
        searchPlaceholder={t(`${ui.i18n}.searchPlaceholder`)}
        defaultSort={{ key: 'number', dir: 'desc' }}
        extraFilter={ui.extraFilter?.(cases, t)}
        kpis={[
          { key: 'total', label: t('ui.total'), value: cases.length, icon: <FileStack className="h-5 w-5" />, accent: 'bg-brand-500/10 text-brand-600 dark:text-brand-300', status: '' },
          { key: 'pending', label: t('status.pending'), value: count('pending'), icon: <Clock className="h-5 w-5" />, accent: 'bg-amber-500/10 text-amber-600', status: 'pending' },
          { key: 'review', label: t(`status.${ui.reviewStatus}`), value: count(ui.reviewStatus), icon: <UserCheck className="h-5 w-5" />, accent: 'bg-violet-500/10 text-violet-600', status: ui.reviewStatus },
          { key: 'done', label: t('status.completed'), value: count('completed'), hint: average ? `${t('ui.avgTime')} ${formatDuration(average)}` : undefined, icon: <CheckCircle2 className="h-5 w-5" />, accent: 'bg-emerald-500/10 text-emerald-600', status: 'completed' },
        ]}
      />
    </>
  )
}
