import { useState } from 'react'
import { Database, RotateCcw, Settings, TriangleAlert } from 'lucide-react'
import { useAuth } from '../auth/AuthContext'
import { UserProfiles } from '../components/admin/UserProfiles'
import { Button } from '../components/ui/Button'
import { Card, CardHeader } from '../components/ui/Card'
import { ErrorBanner } from '../components/ui/Feedback'
import { ConfirmDialog } from '../components/ui/Modal'
import { PageHeader } from '../components/ui/PageHeader'
import { StatusBadge } from '../components/ui/StatusBadge'
import { useResource } from '../hooks/useResource'
import { useTranslation } from '../i18n/LanguageContext'
import { adminApi } from '../services/api'

/** Administration: what the database holds, the demo reset, and the users' access profiles. */
export default function AdminPage() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const { data: overview, error, reload } = useResource(() => adminApi.overview(), [])
  const [confirming, setConfirming] = useState(false)
  const [resetting, setResetting] = useState(false)
  const [result, setResult] = useState<{ ok: boolean; text: string } | null>(null)

  const reset = async () => {
    setConfirming(false)
    setResetting(true)
    setResult(null)
    try {
      const { loaded, restored } = await adminApi.reset()
      setResult({
        ok: true,
        text: `${t('adm.resetDone')} — ${Object.entries(loaded).map(([table, n]) => `${table} ${n}`).join(', ')} · `
          + `${t('adm.resetRestored')}: ${restored.documents} documents, ${restored.reference_embeddings} embeddings, `
          + `${restored.precedent_decisions} precedents, ${restored.document_links} PDF`,
      })
      await reload()
    } catch (err: any) {
      setResult({ ok: false, text: err?.response?.data?.detail || err?.message || 'Reset failed' })
    } finally {
      setResetting(false)
    }
  }

  return (
    <>
      <PageHeader icon={<Settings className="h-5 w-5 text-ink-muted" />} title={t('admin.title')} subtitle={t('admin.subtitle')} />
      {error && <div className="mb-4"><ErrorBanner onRetry={reload} retryLabel={t('ui.retry')}>{error}</ErrorBanner></div>}

      <div className="grid gap-5 lg:grid-cols-2">
        <Card>
          <CardHeader icon={<Database className="h-4 w-4" />} title={t('adm.overview')} />
          <div className="space-y-4 p-5">
            {overview?.domains.map((d) => (
              <div key={d.domain}>
                <p className="label mb-1.5">{t(`nav.${d.domain}`)} · {t('adm.embeddings')} {d.documents_with_embedding}/{d.documents}</p>
                <div className="flex flex-wrap gap-2">
                  {Object.entries(d.by_status).map(([status, n]) => (
                    <span key={status} className="inline-flex items-center gap-2 rounded-xl bg-surface-muted px-2.5 py-1.5">
                      <StatusBadge status={status} /> <span className="text-sm font-semibold tabular-nums text-ink">{n}</span>
                    </span>
                  ))}
                </div>
              </div>
            ))}
            {overview && (
              <p className="text-xs text-ink-subtle">
                {t('adm.references')}: {Object.entries(overview.references).map(([table, r]) => `${table} ${r.with_embedding}/${r.rows}`).join(' · ')}
              </p>
            )}
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
