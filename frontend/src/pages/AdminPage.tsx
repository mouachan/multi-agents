import { useState } from 'react'
import { BookOpen, Database, FileStack, RotateCcw, Settings, TriangleAlert, Users } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { UserProfiles } from '../components/admin/UserProfiles'
import { Button } from '../components/ui/Button'
import { Card, CardHeader } from '../components/ui/Card'
import { ErrorBanner } from '../components/ui/Feedback'
import { KpiCard } from '../components/ui/KpiCard'
import { ConfirmDialog } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { adminApi } from '../services/api'

export default function AdminPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const { data: stats, loading, error, reload } = useResource(() => adminApi.databaseStats(), [])
  const [confirming, setConfirming] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null)

  const reset = async () => {
    setConfirming(false)
    setResetting(true)
    setResult(null)
    try {
      const res = await adminApi.resetDatabase()
      const d = res.data || {}
      const loaded = d.loaded ?? {}
      const kept = d.restored ?? {}
      setResult({
        ok: true,
        text: `${t('adm.resetDone')} — claims ${loaded.claims ?? '?'}, tenders ${loaded.tenders ?? '?'}, complaints ${loaded.reclamations ?? '?'} · `
          + `${t('adm.resetRestored')}: ${kept.documents ?? 0} documents (OCR + embeddings), ${kept.reference_embeddings ?? 0} reference embeddings, `
          + `${kept.precedent_decisions ?? 0} precedents, ${kept.document_links ?? 0} PDF links`,
      })
      await reload()
    } catch (err: any) {
      setResult({ ok: false, text: err?.response?.data?.detail || err?.message || 'Reset failed' })
    } finally {
      setResetting(false)
    }
  }

  const v = (n: number | string | undefined) => (loading ? <span className="skeleton inline-block h-6 w-10 align-middle" /> : n ?? '—')

  return (
    <>
      <PageHeader icon={<Settings className="h-5 w-5 text-ink-muted" />} title={t('admin.title')} subtitle={t('admin.subtitle')} />
      {error && <div className="mb-4"><ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error}</ErrorBanner></div>}

      <div className="grid grid-cols-2 gap-3 lg:grid-cols-4">
        <KpiCard label={t('adm.users')} value={v(stats?.users)} icon={<Users className="h-5 w-5" />} accent="bg-brand-500/10 text-brand-600 dark:text-brand-300" />
        <KpiCard label={t('adm.contracts')} value={v(stats?.contracts)} icon={<FileStack className="h-5 w-5" />} accent="bg-sky-500/10 text-sky-600" />
        <KpiCard label={t('adm.claims')} value={v(stats?.claims_total)} icon={<Database className="h-5 w-5" />} accent="bg-emerald-500/10 text-emerald-600" />
        <KpiCard label={t('adm.knowledgeBase')} value={v(stats?.knowledge_base)} hint={stats ? `embeddings ${stats.knowledge_base_embeddings}` : undefined} icon={<BookOpen className="h-5 w-5" />} accent="bg-amber-500/10 text-amber-600" />
      </div>

      <div className="mt-5 grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader icon={<Database className="h-4 w-4" />} title={t('adm.claimsByStatus')} />
          <div className="flex flex-wrap gap-2 p-5">
            {stats && Object.entries(stats.claims_by_status).map(([s, n]) => (
              <span key={s} className="inline-flex items-center gap-2 rounded-xl bg-surface-muted px-3 py-2">
                <StatusBadge status={s} /> <span className="text-sm font-semibold tabular-nums text-ink">{n}</span>
              </span>
            ))}
            {stats && <p className="w-full pt-2 text-xs text-ink-subtle">claim documents embeddings: {stats.claim_documents_embeddings}</p>}
          </div>
        </Card>

        <Card>
          <CardHeader icon={<TriangleAlert className="h-4 w-4 text-orange-500" />} title={t('adm.resetTitle')} />
          <div className="space-y-4 p-5">
            <ul className="list-inside list-disc space-y-1 text-sm text-ink-muted">
              <li>{t('adm.resetLine1')}</li>
              <li>{t('adm.resetLine2')}</li>
              <li>{t('adm.resetLine3')}</li>
            </ul>
            <Button variant="danger" size="md" className="w-full" icon={<RotateCcw className="h-4 w-4" />} loading={resetting} onClick={() => setConfirming(true)}>
              {resetting ? t('adm.resetting') : t('adm.resetButton')}
            </Button>
            {result && (
              <p className={`rounded-xl px-3 py-2 text-sm ${result.ok ? 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300' : 'bg-red-500/10 text-red-700 dark:text-red-300'}`}>
                {result.text}
              </p>
            )}
          </div>
        </Card>
      </div>

      {user.authEnabled && <div className="mt-5"><UserProfiles /></div>}

      <ConfirmDialog
        open={confirming}
        danger
        title={t('adm.resetTitle')}
        message={t('adm.resetConfirm')}
        confirmLabel={t('adm.resetButton')}
        cancelLabel={t('ui.cancel')}
        onCancel={() => setConfirming(false)}
        onConfirm={reset}
      />
    </>
  )
}
