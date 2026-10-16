import { useEffect, useState } from 'react'
import { CheckCircle2, ExternalLink, Gauge, Play, XCircle } from 'lucide-react'
import { Badge } from '../ui/Badge'
import { Button } from '../ui/Button'
import { Card, CardHeader } from '../ui/Card'
import { useTranslation } from '../../i18n/LanguageContext'
import { adminApi, type Evaluation } from '../../services/api'

const ALIASES = ['production', 'candidate']
const percent = (value?: number) => (value === undefined ? '—' : `${Math.round(value * 100)} %`)

/** Quality of the agents' decisions: the precedents processed again (nothing saved) and compared with
 *  their known decision; the run is logged in MLflow (backend/app/services/evaluation.py). */
export function DecisionEvaluation() {
  const { t } = useTranslation()
  const [evaluation, setEvaluation] = useState<Evaluation | null>(null)
  const [alias, setAlias] = useState('production')
  const [error, setError] = useState<string | null>(null)
  const running = evaluation?.status === 'running'

  useEffect(() => { adminApi.evaluation().then(setEvaluation).catch(() => undefined) }, [])
  useEffect(() => {
    if (!running) return
    const timer = setInterval(() => adminApi.evaluation().then(setEvaluation).catch(() => undefined), 3000)
    return () => clearInterval(timer)
  }, [running])

  const start = async () => {
    setError(null)
    try {
      setEvaluation(await adminApi.evaluate(alias))
    } catch (err: any) {
      setError(err?.response?.data?.detail || err?.message)
    }
  }

  const domains = ['claims', 'tenders', 'postal'].filter((d) => evaluation?.metrics[`accuracy_${d}`] !== undefined)
  return (
    <Card>
      <CardHeader icon={<Gauge className="h-4 w-4" />} title={t('adm.evalTitle')} subtitle={t('adm.evalSubtitle')} />
      <div className="space-y-4 p-5">
        <div className="flex flex-wrap items-center gap-3">
          <label className="text-sm text-ink-muted">{t('adm.evalPrompts')}</label>
          <select className="input w-auto" value={alias} onChange={(e) => setAlias(e.target.value)} disabled={running}>
            {ALIASES.map((a) => <option key={a} value={a}>@{a}</option>)}
          </select>
          <Button variant="primary" size="md" icon={<Play className="h-4 w-4" />} loading={running} onClick={start}>
            {running ? `${t('adm.evalRunning')} ${evaluation?.done}/${evaluation?.total}` : t('adm.evalStart')}
          </Button>
        </div>
        {error && <p className="rounded-xl bg-red-500/10 px-3 py-2 text-sm text-red-700 dark:text-red-300">{error}</p>}

        {evaluation && evaluation.status !== 'running' && (
          <>
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <Badge tone="brand">@{evaluation.prompt_alias}</Badge>
              <span className="font-semibold text-ink">{t('adm.evalAccuracy')} {percent(evaluation.metrics.accuracy)}</span>
              {domains.map((d) => (
                <span key={d} className="chip">{t(`nav.${d}`)} {percent(evaluation.metrics[`accuracy_${d}`])}
                  {' · '}{t('adm.evalReview')} {percent(evaluation.metrics[`review_rate_${d}`])}</span>
              ))}
              {evaluation.mlflow_url && (
                <a className="inline-flex items-center gap-1 text-brand-600 hover:underline" href={evaluation.mlflow_url} target="_blank" rel="noreferrer">
                  MLflow <ExternalLink className="h-3.5 w-3.5" />
                </a>
              )}
            </div>
            {Object.keys(evaluation.prompts).length > 0 && (
              <p className="text-xs text-ink-subtle">
                {t('adm.evalVersions')}: {Object.entries(evaluation.prompts).map(([name, v]) => `${name} v${v}`).join(' · ')}
              </p>
            )}
            <div className="max-h-72 overflow-auto rounded-xl border border-line">
              <table className="w-full text-sm">
                <thead className="bg-surface-muted text-left text-xs text-ink-subtle">
                  <tr><th className="px-3 py-2">{t('adm.evalCase')}</th><th>{t('adm.evalExpected')}</th><th>{t('adm.evalAgent')}</th><th /></tr>
                </thead>
                <tbody>
                  {[...evaluation.results].sort((a, b) => a.number.localeCompare(b.number)).map((r) => (
                    <tr key={r.number} className="border-t border-line">
                      <td className="px-3 py-1.5 font-mono text-xs">{r.number}</td>
                      <td>{t(`decision.${r.expected}`)}</td>
                      <td>{r.error ? <span className="text-red-600">{r.error}</span> : r.decision && t(`decision.${r.decision}`)}</td>
                      <td className="pr-3">{r.correct ? <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                        : r.correct === false && <XCircle className="h-4 w-4 text-red-500" />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        )}
      </div>
    </Card>
  )
}
